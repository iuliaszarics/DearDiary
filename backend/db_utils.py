import sqlite3
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from calendar import monthrange
from urllib import error, request
from nlp_model import predict_emotion
from entity_extractor import extract_entities_with_emotion, generate_entity_advice
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
db_path= str(PROJECT_ROOT / 'database' / 'journal.db')

load_dotenv(PROJECT_ROOT / 'backend' / '.env')
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    FERNET_KEY = Fernet.generate_key()
    with open(PROJECT_ROOT / 'backend' / '.env', 'a') as f:
        f.write(f"\nFERNET_KEY={FERNET_KEY.decode('utf-8')}\n")
else:
    FERNET_KEY = FERNET_KEY.encode('utf-8')

cipher_suite = Fernet(FERNET_KEY)

def encrypt_text(text: str) -> str:
    if not text:
        return text
    return cipher_suite.encrypt(text.encode('utf-8')).decode('utf-8')

def decrypt_text(encrypted_text: str) -> str:
    if not encrypted_text:
        return encrypted_text
    try:
        return cipher_suite.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return encrypted_text

POSITIVE_EMOTIONS={'admiration','amusement','approval','caring','desire','excitement','gratitude','joy','love','optimism','pride','relief'}
NEGATIVE_EMOTIONS={'anger','annoyance','disappointment','disapproval','disgust','embarrassment','fear','grief','nervousness','remorse','sadness'}
NEUTRAL_EMOTIONS={'neutral','confusion','curiosity','realization','surprise'}

EMOTION_COLOR_MAP = {
    'positive': '#ffb3ba',
    'negative': '#bae1ff',
    'neutral': '#e2e2e2'
}

def ensure_analysis_columns(connection):
    columns={ row['name'] for row in connection.execute("pragma table_info(Analysis)").fetchall()}
    if "scores_json" not in columns:
        connection.execute("alter table Analysis add column scores_json text")
    if "task_type" not in columns:
        connection.execute("alter table Analysis add column task_type text")


def get_db_connection():
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found at {db_path}")
    connection=sqlite3.connect(db_path)
    connection.row_factory=sqlite3.Row
    connection.execute("pragma foreign_keys=ON;")
    return connection


def register_user(username, password):
    connection=get_db_connection()
    hashed_password=hash_password(password)
    try:
        connection.execute("insert into Users (username, password_hash) values (?, ?)", (username, hashed_password))
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        connection.close()

def login_user(username, password):
    connection = get_db_connection()
    hashed_password = hash_password(password)
    user = connection.execute("select user_id from Users where username = ? and password_hash =?", (username, hashed_password)).fetchone()
    connection.close()
    return user['user_id'] if user else None



def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def emotion_categorization(predicted_emotion):
    label = (predicted_emotion or 'neutral').strip().lower()
    if label in POSITIVE_EMOTIONS:
        return 'positive'
    elif label in NEGATIVE_EMOTIONS:
        return 'negative'   
    elif label in NEUTRAL_EMOTIONS:
        return 'neutral'

def analyze_entry(user_id, text, incognito=False):
    connection=get_db_connection()
    try:
        entry_time=datetime.now().isoformat(timespec='seconds')
        cursor=connection.execute("insert into Entries(user_id,text,entry_time) values(?,?,?)", (user_id, encrypt_text(text), entry_time))
        entry_id=cursor.lastrowid
        model_result = predict_emotion(text)
        if model_result is None:
            model_result=keyword_baseline_prediction(text)
        predicted_emotion=model_result['predicted_emotion']
        confidence=model_result['confidence']
        model_name = model_result['model_name']
        task_type=model_result.get('task_type')
        scores=model_result.get('scores')
        scores_json=json.dumps(scores) if scores else None
        insight_bundle = get_entry_insight(connection, user_id, text, predicted_emotion, confidence, scores, entry_time, incognito)
        persist_entry_history(connection, entry_id, insight_bundle['insight'], insight_bundle['advice'])
        connection.execute("insert into Analysis (entry_id,model_name,predicted_emotion,confidence,scores_json, task_type) values (?,?,?,?,?,?)", (entry_id, model_name, predicted_emotion, confidence, scores_json, task_type))
        recalculate_daily_summary(connection, user_id, entry_time[:10])
        connection.commit()
        return{
            'entry_id': entry_id,
            'text': text,
            'predicted_emotion': predicted_emotion,
            'confidence': confidence,
            'model_name': model_name,
            'task_type': task_type,
            'scores': scores,
            'emotion_bucket':insight_bundle['insight']['bucket'],
            'insight': insight_bundle['insight'],
            'advice': insight_bundle['advice']
            #'day_summary': insight_bundle['day_summary'],
        }
    except sqlite3.Error as e:
        print(f"Database error during analysis: {e}")
        raise 
    finally:
        connection.close()

def delete_entry(user_id, entry_id):
    connection = get_db_connection()
    try:
        row = connection.execute("select date(entry_time) as summary_date from Entries where entry_id = ? and user_id = ?", (entry_id, user_id)).fetchone()
        if not row:
            return False
        summary_date = row['summary_date']
        cursor=connection.execute("delete from Entries where entry_id = ? and user_id = ?", (entry_id, user_id))
        if cursor.rowcount == 0:
            return False
        else:
            recalculate_daily_summary(connection, user_id, summary_date)
            connection.commit()
            return True
    finally:
        connection.close()

def persist_entry_history(connection, entry_id, insight, advice):
    details_json = json.dumps(insight.get('details') or [])
    connection.execute("insert or replace into  EntryInsightHistory(entry_id, emotion_bucket, title, explanation, details_json) values (?, ?, ?, ?, ?)", (entry_id, insight.get('bucket','neutral'), insight.get('title', 'Insight'), insight.get('explanation',''), details_json))
    connection.execute("delete from  EntryAdviceHistory WHERE entry_id = ?", (entry_id,))
    for item in advice:
        connection.execute(
            "insert into EntryAdviceHistory (entry_id, advice_key, emotion_key, title, advice_text, rationale_text) values (?, ?, ?, ?, ?, ?)",
            (
                entry_id,
                item.get('advice_key', 'generic_advice'),
                item.get('emotion_key', 'neutral'),
                item.get('title', 'Advice'),
                item.get('advice_text', ''),
                item.get('rationale_text', ''),
            ),
        )

def assign_color_to_emotion(bucket):
    return EMOTION_COLOR_MAP.get(bucket, EMOTION_COLOR_MAP['neutral'])

def recalculate_daily_summary(connection, user_id, summary_date):
    rows = connection.execute("select a.predicted_emotion, e.text from Entries e left join Analysis a on e.entry_id = a.entry_id where e.user_id = ? and date(e.entry_time)=? order by e.entry_time desc", (user_id, summary_date)).fetchall()
    if not rows:
        connection.execute("delete from DailyEmotionSummary where user_id = ? and summary_date = ?", (user_id, summary_date))
        return
    breakdown={}
    for row in rows: 
        bucket = emotion_categorization(row['predicted_emotion'])
        breakdown[bucket] = breakdown.get(bucket, 0) + 1
    total = len(rows)
    dominant_emotion = max(breakdown.items(), key=lambda item: item[1])[0]
    positivity_score = round((breakdown.get('positive',0)+(0.5*breakdown.get('neutral',0)))/total,2)
    preview = decrypt_text(rows[0]['text'] or '').strip().replace('\n',' ')
    latest_entry_preview  = preview[:160]
    summary_text=f"Your day had a {dominant_emotion} tone with a positivity score of {positivity_score}. You had {breakdown.get('positive',0)} positive, {breakdown.get('negative',0)} negative and {breakdown.get('neutral',0)} neutral entries. Your most recent entry was: \"{latest_entry_preview}\""
    
    latest_entry_preview_enc = encrypt_text(latest_entry_preview)
    summary_text_enc = encrypt_text(summary_text)

    exists = connection.execute("select 1 from DailyEmotionSummary where user_id = ? and summary_date = ?", (user_id, summary_date)).fetchone()
    if exists:
        connection.execute(
            """
            UPDATE DailyEmotionSummary
            SET dominant_emotion = ?, emotion_breakdown_json = ?, positivity_score = ?, entry_count = ?,
                latest_entry_preview = ?, summary_text = ?
            WHERE user_id = ? AND summary_date = ?
            """,
            (dominant_emotion, json.dumps(breakdown), positivity_score, total, latest_entry_preview_enc, summary_text_enc, user_id, summary_date),
        )
    else:
        connection.execute(
            """
            INSERT INTO DailyEmotionSummary
            (user_id, summary_date, dominant_emotion, emotion_breakdown_json, positivity_score, entry_count, latest_entry_preview, summary_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, summary_date, dominant_emotion, json.dumps(breakdown), positivity_score, total, latest_entry_preview_enc, summary_text_enc),
        )

def get_entry_insight(connection, user_id, text, predicted_emotion, confidence, scores, occured_at, incognito=False):
    insight = build_insight(predicted_emotion, confidence, scores)
    
    # Generate entity-based personalized advice
    if incognito:
        advice = []
    else:
        entities = extract_entities_with_emotion(text)
        advice = generate_entity_advice(entities)
    
    # Add general advice
    bucket = insight.get('bucket', 'neutral')
    if bucket == 'positive':
        advice.insert(0, {
            "advice_key": "general_positive",
            "emotion_key": "positive",
            "title": "General Advice",
            "advice_text": "Keep doing what you like with the people you love! Cherish these positive moments.",
            "rationale_text": "Your overall entry is positive."
        })
    elif bucket == 'negative':
        advice.insert(0, {
            "advice_key": "general_negative",
            "emotion_key": "negative",
            "title": "General Advice",
            "advice_text": "Consider trying some mindfulness or relaxation techniques. Taking a few deep breaths or a short walk can really help.",
            "rationale_text": "Your overall entry reflects some heavy emotions."
        })
    
    day_summary = None
    return{
        'insight': insight,
        'advice': advice,
        'day_summary': day_summary,
    }

def build_insight(predicted_emotion, confidence, scores):
    bucket = emotion_categorization(predicted_emotion)
    if bucket == 'positive':
        title = 'Positive emotion detected'
        explanation = (
            'Your entry reads as emotionally positive. The language suggests a good moment, a sense of progress, '
            'or some form of connection that left you feeling better.'
        )
    elif bucket == 'negative':
        title = 'Negative emotion detected'
        explanation = (
            'Your entry suggests emotional strain or discomfort. The wording points to stress, frustration, or a '
            'low mood that may need a small reset or some support.'
        )
    else:
        title = 'Neutral emotion detected'
        explanation = (
            'Your entry appears more neutral or reflective than emotionally intense. That can mean you are describing '
            'events, organizing thoughts, or processing the day in a steady way.'
        )

    return {
        'title': title,
        'explanation': explanation,
        'bucket': bucket,
    }

def summarize_scores(scores):
    if not isinstance(scores, dict) or not scores:
        return[]
    ranked = sorted(((label, value) for label, value in scores.items() if isinstance(value, (int, float))), key = lambda item: item[1], reverse=True)
    return [{'label': label, 'score': float(value)} for label, value in ranked[:3]]

def get_calendar(user_id, year, month):
    connection = get_db_connection()
    try:
        start_date = f"{year:04d}-{month:02d}-01"
        _, last_day = monthrange(year, month)
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"
        
        rows = connection.execute(
            """
            SELECT summary_date, dominant_emotion, entry_count, summary_text 
            FROM DailyEmotionSummary 
            WHERE user_id = ? AND summary_date BETWEEN ? AND ?
            """,
            (user_id, start_date, end_date)
        ).fetchall()
        
        stats = {'positive_days': 0, 'neutral_days': 0, 'negative_days': 0}
        days_dict = {}
        
        for row in rows:
            bucket = row['dominant_emotion']
            days_dict[row['summary_date']] = {
                'color': assign_color_to_emotion(bucket),
                'dominant_emotion': bucket,
                'entry_count': row['entry_count'],
                'summary_text': decrypt_text(row['summary_text']) if row['summary_text'] else 'No entries for this day.'
            }
            stats_key = f"{bucket}_days"
            if stats_key in stats:
                stats[stats_key] += 1
                
        days = []
        for day in range(1, last_day + 1):
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            if date_str in days_dict:
                days.append({
                    'date': date_str,
                    'day': day,
                    **days_dict[date_str]
                })
            else:
                days.append({
                    'date': date_str,
                    'day': day,
                    'entry_count': 0,
                    'color': '#ffffff',
                    'dominant_emotion': 'none',
                    'summary_text': 'No entries for this day.'
                })
                
        return {'stats': stats, 'days': days}
    finally:
        connection.close()

def get_user_stats(user_id):
    connection = get_db_connection()
    try:
        # Emotion distribution
        emotion_rows = connection.execute(
            """
            SELECT a.predicted_emotion, COUNT(*) as count 
            FROM Analysis a 
            JOIN Entries e ON a.entry_id = e.entry_id 
            WHERE e.user_id = ? 
            GROUP BY a.predicted_emotion
            """, 
            (user_id,)
        ).fetchall()
        
        emotion_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for row in emotion_rows:
            bucket = emotion_categorization(row['predicted_emotion'])
            if bucket in emotion_counts:
                emotion_counts[bucket] += row['count']
                
        # Writing occurrences per month
        # In SQLite, strftime('%Y-%m', entry_time) gives the year-month
        month_rows = connection.execute(
            """
            SELECT strftime('%Y-%m', entry_time) as month, COUNT(*) as count
            FROM Entries
            WHERE user_id = ?
            GROUP BY strftime('%Y-%m', entry_time)
            ORDER BY month ASC
            """,
            (user_id,)
        ).fetchall()
        
        writing_occurrences = []
        for row in month_rows:
            writing_occurrences.append({
                'month': row['month'],
                'count': row['count']
            })
            
        return {
            'emotion_distribution': emotion_counts,
            'writing_occurrences': writing_occurrences
        }
    finally:
        connection.close()

def get_emotion_fluctuation(user_id):
    connection = get_db_connection()
    try:
        rows = connection.execute(
            """
            SELECT e.entry_time, a.predicted_emotion 
            FROM Entries e
            LEFT JOIN Analysis a ON e.entry_id = a.entry_id
            WHERE e.user_id = ?
            ORDER BY e.entry_time ASC
            """,
            (user_id,)
        ).fetchall()
        
        fluctuation = []
        for row in rows:
            if not row['predicted_emotion']:
                continue
            bucket = emotion_categorization(row['predicted_emotion'])
            score = 0
            if bucket == 'positive':
                score = 1
            elif bucket == 'negative':
                score = -1
                
            fluctuation.append({
                'timestamp': row['entry_time'],
                'score': score
            })
            
        return fluctuation
    finally:
        connection.close()

def get_user_analysis_history(user_id, limit=20, offset=0, date=None):
    connection = get_db_connection()
    try:
        query = """
            SELECT 
                e.entry_id, e.text, e.entry_time as occured_at,
                a.predicted_emotion, a.confidence,
                i.emotion_bucket, i.title as insight_title, i.explanation as insight_explanation, i.details_json as insight_details
            FROM Entries e
            LEFT JOIN Analysis a ON e.entry_id = a.entry_id
            LEFT JOIN EntryInsightHistory i ON e.entry_id = i.entry_id
            WHERE e.user_id = ?
        """
        params = [user_id]
        if date:
            query += " AND date(e.entry_time) = ?"
            params.append(date)
            
        query += " ORDER BY e.entry_time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        entries = connection.execute(query, params).fetchall()
        result = []
        
        for entry in entries:
            entry_id = entry['entry_id']
            advice_rows = connection.execute(
                "SELECT advice_key, emotion_key, title, advice_text, rationale_text FROM EntryAdviceHistory WHERE entry_id = ?",
                (entry_id,)
            ).fetchall()
            
            advice = [dict(row) for row in advice_rows]
            
            insight_details = []
            if entry['insight_details']:
                try:
                    insight_details = json.loads(entry['insight_details'])
                except:
                    pass
                    
            item = {
                'entry_id': entry_id,
                'text': decrypt_text(entry['text']),
                'occured_at': entry['occured_at'],
                'predicted_emotion': entry['predicted_emotion'],
                'confidence': entry['confidence'],
                'insight': {
                    'title': entry['insight_title'],
                    'explanation': entry['insight_explanation'],
                    'bucket': entry['emotion_bucket'],
                    'details': insight_details
                },
                'advice': advice
            }
            result.append(item)
            
        return result
    finally:
        connection.close()

import random

def get_user_prompts(user_id):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT eah.advice_key, eah.emotion_key, eah.title
            FROM EntryAdviceHistory eah
            JOIN Entries e ON eah.entry_id = e.entry_id
            WHERE e.user_id = ? AND eah.advice_key LIKE 'entity_%'
            ORDER BY eah.created_at DESC
            LIMIT 15
        """, (user_id,))
        
        rows = cursor.fetchall()
        
        prompts = []
        seen_entities = set()
        
        for row in rows:
            title = row['title'] # e.g. "Regarding Alex"
            emotion = row['emotion_key']
            
            entity = title.replace("Regarding ", "").strip()
            if entity.lower() in seen_entities:
                continue
            seen_entities.add(entity.lower())
            
            if emotion == "positive":
                prompts.append(f"You mentioned {entity} in a positive light recently. Have you seen them since or made any plans?")
            elif emotion == "negative":
                prompts.append(f"You had a stressful time regarding {entity} recently. How are you feeling about that now?")
            else:
                prompts.append(f"What's new with {entity}?")
                
        generic_prompts = [
            "What's on your mind right now?",
            "What's one thing you're grateful for today?",
            "Describe a challenge you faced recently.",
            "What is something you are looking forward to?",
            "How are you feeling physically today?",
            "What did you learn recently that surprised you?"
        ]
        
        # We want exactly 3 prompts. Mix entity prompts with generic ones.
        final_prompts = prompts[:2] # take up to 2 entity prompts
        
        random.shuffle(generic_prompts)
        for g in generic_prompts:
            if len(final_prompts) >= 3:
                break
            final_prompts.append(g)
            
        return final_prompts
    finally:
        connection.close()