import re
from typing import List, Dict, Any
from transformers import pipeline
from nlp_model import predict_emotion
import nltk

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')
try:
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    nltk.download('averaged_perceptron_tagger')
    nltk.download('averaged_perceptron_tagger_eng')


# Local import to prevent circular dependency
def _categorize(emotion):
    from db_utils import emotion_categorization
    return emotion_categorization(emotion)

try:
    # Use a lightweight fast NER model
    ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
except Exception as e:
    print(f"Warning: NER pipeline could not be loaded. {e}")
    ner_pipeline = None

def extract_entities_with_emotion(text: str) -> List[Dict[str, Any]]:
    if ner_pipeline is None:
        return []

    # Simple sentence tokenizer
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    results = []
    processed_entities = set()

    for sentence in sentences:
        if not sentence.strip():
            continue
            
        # Heuristic: if the sentence is mostly lowercase (e.g., lazy typing),
        # standard NER will fail to find entities. We temporarily title-case 
        # it for the pipeline to give it the necessary casing signals.
        uppercase_count = sum(1 for c in sentence if c.isupper())
        text_to_process = sentence.title() if uppercase_count < 2 else sentence
        
        entities = ner_pipeline(text_to_process)
        
        # Pass 1: Merge subwords (WordPiece tokenization artifacts like '##luj')
        merged_entities = []
        for ent in entities:
            word = ent.get('word', '').strip()
            label = ent.get('entity_group', '')
            
            if word.startswith('##'):
                if merged_entities:
                    merged_entities[-1]['word'] += word[2:]
                else:
                    # Rare case: first token is a subword
                    merged_entities.append({'word': word.replace('##', ''), 'label': label})
            else:
                merged_entities.append({'word': word, 'label': label})
                
        # Pass 2: Process the full words
        for ent in merged_entities:
            label = ent['label']
            word = ent['word']
            
            if label in ['PER', 'LOC', 'ORG'] and len(word) > 1:
                unique_key = f"{word.lower()}_{sentence}"
                if unique_key in processed_entities:
                    continue
                processed_entities.add(unique_key)
                
                prediction = predict_emotion(sentence)
                if not prediction:
                    continue
                    
                predicted_emotion = prediction.get('predicted_emotion')
                confidence = prediction.get('confidence')
                bucket = _categorize(predicted_emotion)
                
                results.append({
                    "entity": word,
                    "type": label,
                    "context_sentence": sentence,
                    "predicted_emotion": predicted_emotion,
                    "emotion_bucket": bucket,
                    "confidence": confidence
                })

        # Pass 3: Extract keywords (Nouns) using NLTK
        tokens = nltk.word_tokenize(sentence)
        tags = nltk.pos_tag(tokens)
        for word, pos in tags:
            # We look for singular or plural nouns (NN, NNS)
            if pos in ('NN', 'NNS') and len(word) > 2:
                # Make sure it's not already extracted as an entity
                is_duplicate = False
                for existing in results:
                    if existing['entity'].lower() == word.lower() and existing['context_sentence'] == sentence:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_key = f"kw_{word.lower()}_{sentence}"
                    if unique_key not in processed_entities:
                        processed_entities.add(unique_key)
                        
                        prediction = predict_emotion(sentence)
                        if prediction:
                            predicted_emotion = prediction.get('predicted_emotion')
                            confidence = prediction.get('confidence')
                            bucket = _categorize(predicted_emotion)
                            
                            results.append({
                                "entity": word.lower(),
                                "type": "KEYWORD",
                                "context_sentence": sentence,
                                "predicted_emotion": predicted_emotion,
                                "emotion_bucket": bucket,
                                "confidence": confidence
                            })
                
    return results

def generate_entity_advice(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    advice_list = []
    
    for item in entities:
        entity_name = item['entity']
        ent_type = item['type']
        bucket = item['emotion_bucket']
        
        advice_text = ""
        rationale_text = f"You mentioned '{entity_name}' in a {bucket} context."
        
        if ent_type == "PER":
            if bucket == "positive":
                advice_text = f"It sounds like {entity_name} brings positive energy. Consider reaching out to them, calling them, or planning to see them again soon to maintain that connection!"
            elif bucket == "negative":
                advice_text = f"Your interaction or thoughts regarding {entity_name} seemed stressful. It might be helpful to take a step back and set boundaries, or have a calm conversation if needed."
            else:
                advice_text = f"Reflect on your relationship with {entity_name} and how it impacts your daily routine."
                
        elif ent_type in ["LOC", "ORG"]:
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
