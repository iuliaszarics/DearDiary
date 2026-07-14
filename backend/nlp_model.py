import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TF"] = "0"
import json
from pathlib import Path
from typing import Dict, Any
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "model" / "results" / "exported_model"
MAX_LENGTH = 128

class EmotionPredictor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.class_names = []
        self.task_type = "multi_label"
        self._load_artifacts()

    def _load_artifacts(self):
        model_path = str(MODEL_DIR)
        if not os.path.exists(model_path):
            print(f"Warning: Model directory {model_path} does not exist.")
            return
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        labels_path = os.path.join(model_path, "labels.json")
        if os.path.exists(labels_path):
            with open(labels_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
                self.class_names = [str(x) for x in payload.get("class_names", [])]
                self.task_type = payload.get("task_type", "multi_label")
        if not self.class_names:
            model_num_labels = int(getattr(self.model.config, "num_labels", 0) or 0)
            self.class_names = [f"label_{idx}" for idx in range(model_num_labels)]

    def predict(self, text: str) -> Dict[str, Any]:
        if self.tokenizer is None or self.model is None:
            self._load_artifacts()
            if self.tokenizer is None or self.model is None:
                raise RuntimeError("Model artifacts are not loaded. Ensure model/results/exported_model exists.")
        
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks = []
        current_chunk = []
        current_len = 0
        for sent in sentences:
            if not sent.strip():
                continue
            sent_tokens = self.tokenizer.encode(sent, add_special_tokens=True)
            sent_len = len(sent_tokens)
            if current_len + sent_len - 2 > 120 and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sent]
                current_len = sent_len
            else:
                current_chunk.append(sent)
                current_len += (sent_len - 2) if len(current_chunk) > 1 else sent_len
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        if not chunks:
            chunks = [text]
            
        chunk_probs = []
        for chunk in chunks:
            encoded = self.tokenizer(
                chunk,
                truncation=True,
                padding="max_length",
                max_length=MAX_LENGTH,
                return_tensors="pt",
            )
            encoded = {key: value.to(self.device) for key, value in encoded.items()}
            with torch.no_grad():
                logits = self.model(**encoded).logits
            probs = torch.sigmoid(logits)[0].detach().cpu().numpy().tolist()
            chunk_probs.append(probs)
            
        num_chunks = len(chunk_probs)
        num_classes = len(chunk_probs[0])
        averaged_probabilities = [0.0] * num_classes
        for probs in chunk_probs:
            for idx in range(num_classes):
                averaged_probabilities[idx] += probs[idx]
        for idx in range(num_classes):
            averaged_probabilities[idx] /= num_chunks
            
        prediction_idx = int(max(range(num_classes), key=lambda idx: averaged_probabilities[idx]))
        probabilities = averaged_probabilities
        label_scores = {
            self.class_names[idx] if idx < len(self.class_names) else f"label_{idx}": float(score)
            for idx, score in enumerate(probabilities)
        }
        predicted_label = self.class_names[prediction_idx] if prediction_idx < len(self.class_names) else f"label_{prediction_idx}"
        predicted_score = float(probabilities[prediction_idx])
        
        return {
            'predicted_emotion': predicted_label,
            'confidence': predicted_score,
            'task_type': self.task_type,
            'scores': label_scores,
            'model_name': 'local-nlp-model'
        }

predictor = EmotionPredictor()

def predict_emotion(text: str) -> Dict[str, Any]:
    return predictor.predict(text)
