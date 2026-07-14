import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TF"] = "0"
import re
from typing import List, Dict, Any
from transformers import pipeline
from nlp_model import predict_emotion
import truecase

def clean_entity_name(name: str) -> str:
    if not name:
        return ""
    cleaned = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', name)
    if cleaned.lower().endswith("'s"):
        cleaned = cleaned[:-2]
    elif cleaned.lower().endswith("s'"):
        cleaned = cleaned[:-1]
    return cleaned.strip()

def expand_entity_bounds(sentence: str, start: int, end: int) -> str:
    if start is None or end is None:
        return ""
    word_start = start
    while word_start > 0 and not sentence[word_start - 1].isspace():
        word_start -= 1
    word_end = end
    while word_end < len(sentence) and not sentence[word_end].isspace():
        word_end += 1
    extracted = sentence[word_start:word_end]
    cleaned = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', extracted)
    return cleaned

def capitalize_entity(entity: str) -> str:
    parts = []
    for word in entity.strip().split():
        subparts = [sub.capitalize() for sub in word.split('-')]
        parts.append("-".join(subparts))
    return " ".join(parts)

def _categorize(emotion):
    from db_utils import emotion_categorization

    return emotion_categorization(emotion)
try:
    ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
except Exception as e:
    print(f"Warning: NER pipeline could not be loaded. {e}")
    ner_pipeline = None
ENTITY_BLACKLIST = {
    'email', 'emails', 'tea', 'coffee', 'breakfast', 'lunch', 'dinner', 
    'work', 'home', 'school', 'university', 'college', 'class', 'classes',
    'exam', 'exams', 'test', 'tests', 'task', 'tasks', 'project', 'projects',
    'meeting', 'meetings', 'phone', 'computer', 'laptop', 'movie', 'movies',
    'music', 'song', 'songs', 'book', 'books', 'dog', 'cat', 'walk', 'run',
    'car', 'train', 'bus', 'flight', 'trip', 'gym', 'bed', 'morning', 'afternoon',
    'evening', 'night', 'weekend', 'week', 'day', 'month', 'year', 'today',
    'yesterday', 'tomorrow', 'street', 'road', 'park', 'river', 'lake', 'sea',
    'ocean', 'beach', 'mountain', 'hill', 'forest', 'wood', 'woods', 'city',
    'town', 'village', 'country', 'world', 'earth', 'sun', 'moon', 'star',
    'stars', 'sky', 'cloud', 'clouds', 'rain', 'snow', 'wind', 'weather',
    'summer', 'winter', 'spring', 'autumn', 'fall', 'holiday', 'holidays',
    'vacation', 'vacations', 'weekend', 'weekends', 'monday', 'tuesday',
    'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
}

CONTRASTIVE_CONJS = re.compile(r'\b(but|however|although|though|while)\b', re.IGNORECASE)

def split_contrastive(sentence: str) -> List[str]:
    parts = CONTRASTIVE_CONJS.split(sentence)
    if len(parts) <= 1:
        return [sentence]
    clauses = []
    left = parts[0].strip(" ,.!?")
    if left:
        clauses.append(left)
    for i in range(1, len(parts), 2):
        right = parts[i+1].strip(" ,.!?")
        if right:
            clauses.append(right)
    return clauses

def predict_emotion_with_fallback(text: str, sentence_idx: int, sentences: List[str], threshold: float = 0.5) -> Dict[str, Any]:
    prediction = predict_emotion(text)
    if not prediction:
        return {}
    confidence = prediction.get('confidence', 0.0)
    pred_emotion = prediction.get('predicted_emotion')
    if confidence < threshold or pred_emotion == 'neutral':
        context_parts = []
        if sentence_idx > 0:
            context_parts.append(sentences[sentence_idx - 1])
        context_parts.append(text)
        if sentence_idx < len(sentences) - 1:
            context_parts.append(sentences[sentence_idx + 1])
        windowed_text = " ".join(context_parts)
        windowed_prediction = predict_emotion(windowed_text)
        if windowed_prediction:
            win_emotion = windowed_prediction.get('predicted_emotion')
            win_conf = windowed_prediction.get('confidence', 0.0)
            if pred_emotion == 'neutral' or (win_emotion != 'neutral' and win_conf > confidence):
                return windowed_prediction
    return prediction

def extract_entities_with_emotion(text: str) -> List[Dict[str, Any]]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    results = []
    processed_entities = set()
    last_per_entity = None
    last_per_sentence_idx = -1
    pronouns_pattern = re.compile(r'\b(he|she|they|him|her|them|his|hers|their|theirs)\b', re.IGNORECASE)
    for idx, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
        entities = []
        if ner_pipeline is not None:
            try:
                tc_sentence = truecase.get_true_case(sentence)
                ner_entities = ner_pipeline(tc_sentence)
                merged = []
                for ent in ner_entities:
                    word = ent.get('word', '').strip()
                    label = ent.get('entity_group', '')
                    start = ent.get('start')
                    end = ent.get('end')
                    if word.startswith('##'):
                        if merged:
                            merged[-1]['word'] += word[2:]
                            if end is not None:
                                merged[-1]['end'] = end
                        else:
                            merged.append({
                                'word': word.replace('##', ''),
                                'label': label,
                                'start': start,
                                'end': end
                            })
                    else:
                        merged.append({
                            'word': word,
                            'label': label,
                            'start': start,
                            'end': end
                        })
                seen_ents = set()
                unique_merged = []
                for ent in merged:
                    key = (ent['word'].lower(), ent['label'])
                    if key not in seen_ents:
                        seen_ents.add(key)
                        unique_merged.append(ent)
                entities = unique_merged
            except Exception as e:
                print(f"Warning: NER execution failed: {e}")
        valid_ner_entities = []
        seen_valid = set()
        for ent in entities:
            label = ent['label']
            word = ent['word']
            start = ent.get('start')
            end = ent.get('end')
            if start is not None and end is not None:
                expanded = expand_entity_bounds(sentence, start, end)
                if expanded:
                    word = expanded
            cleaned_word = clean_entity_name(word)
            if label in ['PER', 'LOC', 'ORG'] and len(cleaned_word) > 1:
                if cleaned_word.lower() in ENTITY_BLACKLIST:
                    continue
                key = (cleaned_word.lower(), label)
                if key not in seen_valid:
                    seen_valid.add(key)
                    valid_ner_entities.append((cleaned_word, label))
        for word, label in valid_ner_entities:
            if label == 'PER':
                last_per_entity = word
                last_per_sentence_idx = idx
        is_coref_sentence = False
        if not valid_ner_entities and pronouns_pattern.search(sentence):
            if last_per_entity is not None and (idx - last_per_sentence_idx) <= 2:
                is_coref_sentence = True
        targets = []
        if is_coref_sentence:
            targets.append((last_per_entity, "PER"))
        else:
            for word, label in valid_ner_entities:
                targets.append((word, label))
        clauses = split_contrastive(sentence)
        for entity, ent_type in targets:
            standardized_entity = capitalize_entity(entity)
            if not standardized_entity:
                continue
            unique_key = f"{standardized_entity.lower()}_{sentence}"
            if unique_key in processed_entities:
                continue
            processed_entities.add(unique_key)
            target_text = sentence
            if len(clauses) > 1:
                found_clause = None
                if is_coref_sentence:
                    for clause in clauses:
                        if pronouns_pattern.search(clause):
                            found_clause = clause
                            break
                else:
                    search_term = standardized_entity.lower()
                    for clause in clauses:
                        if search_term in clause.lower():
                            found_clause = clause
                            break
                if found_clause:
                    target_text = found_clause
            prediction = predict_emotion_with_fallback(target_text, idx, sentences)
            if not prediction:
                continue
            predicted_emotion = prediction.get('predicted_emotion')
            confidence = prediction.get('confidence')
            bucket = _categorize(predicted_emotion)
            results.append({
                "entity": standardized_entity,
                "type": ent_type,
                "context_sentence": sentence,
                "predicted_emotion": predicted_emotion,
                "emotion_bucket": bucket,
                "confidence": confidence
            })
    return results

def generate_entity_advice(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped_entities = {}
    for item in entities:
        raw_name = item['entity']
        entity_name = capitalize_entity(clean_entity_name(raw_name))
        if not entity_name:
            continue
        ent_type = item['type']
        bucket = item['emotion_bucket']
        confidence = item.get('confidence', 0.5)
        key = entity_name.lower()
        if key not in grouped_entities:
            grouped_entities[key] = {
                'entity_name': entity_name,
                'type': ent_type,
                'mentions': []
            }
        grouped_entities[key]['mentions'].append({
            'bucket': bucket,
            'confidence': confidence
        })
    aggregated_entities = []
    for key, group in grouped_entities.items():
        entity_name = group['entity_name']
        ent_type = group['type']
        mentions = group['mentions']
        bucket_scores = {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
        for m in mentions:
            b = m['bucket']
            c = m['confidence']
            if b in bucket_scores:
                bucket_scores[b] += c
        priority = {'negative': 3, 'positive': 2, 'neutral': 1}
        best_bucket = max(bucket_scores.keys(), key=lambda b: (bucket_scores[b], priority.get(b, 0)))
        if bucket_scores[best_bucket] > 0:
            aggregated_entities.append({
                'entity': entity_name,
                'type': ent_type,
                'emotion_bucket': best_bucket
            })
    advice_list = []
    for item in aggregated_entities:
        entity_name = item['entity']
        ent_type = item['type']
        bucket = item['emotion_bucket']
        advice_text = ""
        rationale_text = f"You mentioned '{entity_name}' in a {bucket} context."
        if ent_type == "PER":
            if bucket == "positive":
                advice_text = f"It sounds like {entity_name} brings positive energy. Consider seeing them more often, talking to them, reaching out to them, or planning more activities with them to strengthen that connection!"
            elif bucket == "negative":
                advice_text = f"It seems your thoughts or interactions with {entity_name} were negative. Consider talking to them about what made you feel like that, or if you do not want closure, it might be best to just drift apart from them."
            else:
                advice_text = f"Reflect on your relationship with {entity_name}."
        elif ent_type == "LOC":
            if bucket == "positive":
                advice_text = f"It sounds like {entity_name} has a positive impact on you. Consider going there more often whenever possible."
            elif bucket == "negative":
                advice_text = f"Since {entity_name} is associated with negative emotions, it might be best to avoid going to that place as much as possible to protect your peace of mind."
            else:
                advice_text = f"Consider how your environment at {entity_name} affects your mindset."
        elif ent_type == "ORG":
            if bucket == "positive":
                advice_text = f"You had a good experience related to {entity_name}. Planning more visits or activities there could be a great way to boost your mood!"
            elif bucket == "negative":
                advice_text = f"It seems that {entity_name} is associated with some negative feelings right now. Consider avoiding it unless absolutely necessary, or try going to a more relaxing place like a park instead."
            else:
                advice_text = f"Consider how your environment at {entity_name} affects your mindset."
        elif ent_type == "KEYWORD":
            if bucket == "positive":
                advice_text = f"You had a good experience related to {entity_name}. Keep embracing things like this that bring positivity!"
            elif bucket == "negative":
                advice_text = f"It seems that {entity_name} is associated with some stress or negativity. Give yourself some grace and space if you need it."
            else:
                advice_text = f"Reflect on how {entity_name} plays a role in your current feelings."
        if advice_text:
            advice_list.append({
                "advice_key": f"entity_{entity_name.lower().replace(' ', '_')}_{bucket}",
                "emotion_key": bucket,
                "title": f"Regarding {entity_name}",
                "advice_text": advice_text,
                "rationale_text": rationale_text
            })
    return advice_list
