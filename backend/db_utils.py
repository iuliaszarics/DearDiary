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
import random
from database import init_db

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
        init_db()
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found at {db_path}")
    connection=sqlite3.connect(db_path)
    connection.row_factory=sqlite3.Row
    connection.execute("pragma foreign_keys=ON;")
    ensure_analysis_columns(connection)
    connection.commit()
    return connection

def register_user(username, password):
    connection=get_db_connection()
    username = username.strip()
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
    username = username.strip()
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

def keyword_baseline_prediction(text: str) -> dict:
    import re
    try:
        from nlp_model import predictor
        if hasattr(predictor, 'class_names') and predictor.class_names:
            class_names = predictor.class_names
            task_type = getattr(predictor, 'task_type', 'single_label')
        else:
            class_names = list(POSITIVE_EMOTIONS | NEGATIVE_EMOTIONS | NEUTRAL_EMOTIONS)
            task_type = 'single_label'
    except Exception as e:
        print(f"Warning: Could not import or read predictor attributes. Error: {e}")
        class_names = list(POSITIVE_EMOTIONS | NEGATIVE_EMOTIONS | NEUTRAL_EMOTIONS)
        task_type = 'single_label'
    text_lower = (text or '').lower()
    words = re.findall(r'\b\w+\b', text_lower)
    def get_stems(emotion_name):
        name = emotion_name.lower()
        if name.endswith('ness'): 
            return [name[:-4], name]
        if name.endswith('ment'): 
            return [name[:-4], name]
        if name == 'anger':
            return ['angr', 'anger']
        if name == 'grief':
            return ['griev', 'grief']
        if name == 'love':
            return ['lov', 'love']
        return [name]
    best_emotion = 'neutral'
    max_matches = 0
    for emotion in class_names:
        stems = get_stems(emotion)
        matches = 0
        for word in words:
            for stem in stems:
                if word == stem or word.startswith(stem) or stem.startswith(word):
                    matches += len(stem)
                    break
        if matches > max_matches:
            max_matches = matches
            best_emotion = emotion
    scores = {}
    for emotion in class_names:
        scores[emotion] = 1.0 if emotion == best_emotion else 0.0
    return {
        'predicted_emotion': best_emotion,
        'confidence': 0.5 if max_matches > 0 else 0.1,
        'model_name': 'keyword-baseline',
        'task_type': task_type,
        'scores': scores
    }

def analyze_entry(user_id, text, incognito=False):
    connection=get_db_connection()
    try:
        entry_time=datetime.now().isoformat(timespec='seconds')
        cursor=connection.execute("insert into Entries(user_id,text,entry_time) values(?,?,?)", (user_id, encrypt_text(text), entry_time))
        entry_id=cursor.lastrowid
        
        try:
            model_result = predict_emotion(text)
        except Exception as e:
            print(f"Warning: Primary emotion model failed ({e}). Falling back to keyword prediction.")
            model_result = None
            
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
    connection.execute("delete from EntryInsightHistory WHERE entry_id = ?", (entry_id,))
    connection.execute("insert into EntryInsightHistory(entry_id, emotion_bucket, title, explanation, details_json) values (?, ?, ?, ?, ?)", (entry_id, insight.get('bucket','neutral'), insight.get('title', 'Insight'), insight.get('explanation',''), details_json))
    connection.execute("delete from EntryAdviceHistory WHERE entry_id = ?", (entry_id,))
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
    if incognito:
        advice = []
        entities = []
    else:
        entities = extract_entities_with_emotion(text)
        advice = generate_entity_advice(entities)
    bucket = insight.get('bucket', 'neutral')
    if bucket == 'positive':
        positive_options = [
            "In psychology, thoughts, emotions, and behaviors are deeply connected. Positive emotions typically foster constructive thinking and lead to socially connected, purposeful behaviors. To maintain this positive cycle, try actively scheduling enjoyable and rewarding activities such as hobbies, physical exercises, or connecting with loved ones in your daily routine. ",
            "When you feel good, it's the perfect time to build positive momentum. Emotions, thoughts, and behaviors reinforce each other. You can keep this constructive cycle going by consciously scheduling activities you love, like pursuing a hobby, moving your body, or reaching out to a friend.",
            "A positive mood is an excellent opportunity to strengthen healthy habits. Your thoughts, feelings, and actions are all connected in a feedback loop. To support this positive state, try planning rewarding activities that bring you joy. Actively participating in things you like helps sustain this positive energy in the long run."
        ]
        advice_text = random.choice(positive_options)
        advice.insert(0, {
            "advice_key": "general_positive",
            "emotion_key": "positive",
            "title": "General Advice",
            "advice_text": advice_text,
            "rationale_text": "Your overall entry is positive, reinforcing constructive thoughts and behaviors."
        })
    elif bucket == 'negative':
        negative_options = [
            "When you feel down, thoughts, emotions, and behaviors can form a negative loop. You can break this loop by increasing your commitment to pleasant and rewarding activities. Try reintroducing enjoyable hobbies from your past or scheduling new positive activities in your daily plan. Taking action, even in your lowest moments, is key to improving your physical and mental health",
            "During tough times, a low mood can lead to withdrawal, which further lowers your mood. You can break this negative cycle by actively scheduling and participating in small, enjoyable, or meaningful activities, even when you don't feel like it. Reconnecting with hobbies or planning simple pleasant tasks is a proven way to gradually lift your spirits.",
            "Feeling low can start a cycle of inactivity and negative thoughts. A powerful way to disrupt this loop is by scheduling activities that bring you pleasure or a sense of accomplishment. Try taking small steps to do things you normally enjoy, like a short walk, a creative hobby, or calling a loved one, to help restore your state of mind"
        ]
        advice_text = random.choice(negative_options)
        advice.insert(0, {
            "advice_key": "general_negative",
            "emotion_key": "negative",
            "title": "General Advice",
            "advice_text": advice_text,
            "rationale_text": "Your overall entry reflects heavy emotions, where Behavioral Activation can help break negative loops."
        })
    else:
        neutral_options = [
            "Even on quiet or ordinary days, taking small steps can boost your happiness. Keeping a steady routine is helpful, but you can further improve your mood and energy by proactively scheduling activities you genuinely enjoy. Consider dedicating some time today to a favorite hobby, physical movement or a pleasant conversation to boost your mood .",
            "Neutral days are a great opportunity to check in with yourself and build a solid foundation. You can gently improve your state by integrating activities you love into your schedule. Trying a hobby, planning a relaxing walk, or engaging in a creative outlet can help transition a quiet day into a deeply rewarding one.",
            "A balanced, neutral day is the perfect time to practice self-care and keep your spirits up. To nurture your physical and mental health, try setting aside time for pleasant, fulfilling activities that you like. Actively prioritizing your favorite interests, no matter how small, is a wonderful way to improve your overall quality of life."
        ]
        advice_text = random.choice(neutral_options)
        advice.insert(0, {
            "advice_key": "general_neutral",
            "emotion_key": "neutral",
            "title": "General Advice",
            "advice_text": advice_text,
            "rationale_text": "Your overall entry is neutral, which is a great time to build well-being routines."
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

def get_positivity_color(positivity_score: float) -> str:
    if positivity_score is None:
        return "#ffffff"
    score = max(0.0, min(1.0, positivity_score))
    if score >= 0.5:
        t = (score - 0.5) / 0.5
        r = int(226 + t * (255 - 226))
        g = int(226 + t * (179 - 226))
        b = int(226 + t * (186 - 226))
    else:
        t = score / 0.5
        r = int(186 + t * (226 - 186))
        g = int(225 + t * (226 - 225))
        b = int(255 + t * (226 - 255))
    return f"#{r:02x}{g:02x}{b:02x}"

def get_calendar(user_id, year, month):
    connection = get_db_connection()
    try:
        start_date = f"{year:04d}-{month:02d}-01"
        _, last_day = monthrange(year, month)
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"
        rows = connection.execute(
            """
            SELECT summary_date, dominant_emotion, entry_count, summary_text, positivity_score, emotion_breakdown_json
            FROM DailyEmotionSummary
            WHERE user_id = ? AND summary_date BETWEEN ? AND ?
            """,
            (user_id, start_date, end_date)
        ).fetchall()
        stats = {'positive_days': 0, 'neutral_days': 0, 'negative_days': 0}
        days_dict = {}
        for row in rows:
            bucket = row['dominant_emotion']
            score = row['positivity_score']
            breakdown = {}
            if row['emotion_breakdown_json']:
                try:
                    breakdown = json.loads(row['emotion_breakdown_json'])
                except:
                    pass
            pos = breakdown.get('positive', 0)
            neg = breakdown.get('negative', 0)
            neu = breakdown.get('neutral', 0)
            dominant_cap = bucket.capitalize()
            short_summary = f"{dominant_cap} day. {pos} positive, {neg} negative, {neu} neutral"
            days_dict[row['summary_date']] = {
                'color': get_positivity_color(score),
                'dominant_emotion': bucket,
                'positivity_score': score,
                'entry_count': row['entry_count'],
                'summary_text': short_summary
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
                    'positivity_score': None,
                    'summary_text': 'No entries for this day.'
                })
        return {'stats': stats, 'days': days}
    finally:
        connection.close()

def get_user_stats(user_id):
    connection = get_db_connection()
    try:
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
        entity_rows = connection.execute(
            """
            SELECT eah.title, eah.emotion_key, COUNT(*) as count
            FROM EntryAdviceHistory eah
            JOIN Entries e ON eah.entry_id = e.entry_id
            WHERE e.user_id = ? AND eah.advice_key LIKE 'entity_%'
            GROUP BY eah.title, eah.emotion_key
            """,
            (user_id,)
        ).fetchall()
        entity_map = {}
        for row in entity_rows:
            title = row['title']
            if not title.startswith("Regarding "):
                continue
            entity_name = title[10:].strip()
            emotion = row['emotion_key']
            count = row['count']
            if entity_name not in entity_map:
                entity_map[entity_name] = {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0}
            if emotion in entity_map[entity_name]:
                entity_map[entity_name][emotion] += count
            entity_map[entity_name]['total'] += count
        entity_impact = []
        for name, counts in entity_map.items():
            entity_impact.append({
                'entity': name,
                'positive': counts['positive'],
                'negative': counts['negative'],
                'neutral': counts['neutral'],
                'total': counts['total']
            })
        entity_impact = sorted(entity_impact, key=lambda x: x['total'], reverse=True)[:10]
        time_rows = connection.execute(
            """
            SELECT e.entry_time, a.predicted_emotion
            FROM Entries e
            LEFT JOIN Analysis a ON e.entry_id = a.entry_id
            WHERE e.user_id = ?
            """,
            (user_id,)
        ).fetchall()
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        times_of_day = ["Morning", "Afternoon", "Evening"]
        heatmap_data = {}
        for day in days_of_week:
            for time_slot in times_of_day:
                heatmap_data[(day, time_slot)] = {'score_sum': 0.0, 'count': 0}
        for row in time_rows:
            time_str = row['entry_time']
            emotion = row['predicted_emotion']
            if not time_str or not emotion:
                continue
            try:
                if 'T' in time_str:
                    dt = datetime.fromisoformat(time_str)
                else:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            day_idx = dt.weekday()
            day_name = days_of_week[day_idx]
            hour = dt.hour
            if 6 <= hour < 12:
                time_slot = "Morning"
            elif 12 <= hour < 18:
                time_slot = "Afternoon"
            else:
                time_slot = "Evening"
            bucket = emotion_categorization(emotion)
            score = 0.5
            if bucket == 'positive':
                score = 1.0
            elif bucket == 'negative':
                score = 0.0
            heatmap_data[(day_name, time_slot)]['score_sum'] += score
            heatmap_data[(day_name, time_slot)]['count'] += 1
        time_heatmap = []
        for (day_name, time_slot), info in heatmap_data.items():
            count = info['count']
            avg_score = round(info['score_sum'] / count, 2) if count > 0 else None
            time_heatmap.append({
                'day': day_name,
                'time': time_slot,
                'score': avg_score,
                'count': count
            })
        positivity_rows = connection.execute(
            """
            SELECT summary_date, positivity_score
            FROM DailyEmotionSummary
            WHERE user_id = ?
            ORDER BY summary_date ASC
            """,
            (user_id,)
        ).fetchall()
        daily_positivity = []
        for row in positivity_rows:
            daily_positivity.append({
                'date': row['summary_date'],
                'score': row['positivity_score']
            })
        return {
            'emotion_distribution': emotion_counts,
            'writing_occurrences': writing_occurrences,
            'entity_impact': entity_impact,
            'time_heatmap': time_heatmap,
            'daily_positivity': daily_positivity
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
            title = row['title']
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
        
        final_prompts = prompts[:2]
        
        random.shuffle(generic_prompts)
        for g in generic_prompts:
            if len(final_prompts) >= 3:
                break
            final_prompts.append(g)
            
        return final_prompts
    finally:
        connection.close()