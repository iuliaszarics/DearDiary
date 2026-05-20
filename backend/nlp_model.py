import os
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
        self.task_type = "single_label"
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

        # Load labels
        labels_path = os.path.join(model_path, "labels.json")
        if os.path.exists(labels_path):
            with open(labels_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
                self.class_names = [str(x) for x in payload.get("class_names", [])]
                self.task_type = payload.get("task_type", "single_label")

        if not self.class_names:
            model_num_labels = int(getattr(self.model.config, "num_labels", 0) or 0)
            self.class_names = [f"label_{idx}" for idx in range(model_num_labels)]

    def predict(self, text: str) -> Dict[str, Any]:
        if self.tokenizer is None or self.model is None:
            # Try reloading in case it failed previously
            self._load_artifacts()
            if self.tokenizer is None or self.model is None:
                raise RuntimeError("Model artifacts are not loaded. Ensure model/results/exported_model exists.")

        encoded = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}

        with torch.no_grad():
            logits = self.model(**encoded).logits

        if self.task_type == "single_label":
            probabilities = torch.softmax(logits, dim=-1)[0].detach().cpu().numpy().tolist()
            prediction_idx = int(torch.argmax(logits, dim=-1).item())
        else:
            probabilities = torch.sigmoid(logits)[0].detach().cpu().numpy().tolist()
            prediction_idx = int(max(range(len(probabilities)), key=lambda idx: probabilities[idx]))

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

# Global singleton instance
predictor = EmotionPredictor()

def predict_emotion(text: str) -> Dict[str, Any]:
    return predictor.predict(text)
