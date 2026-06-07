import json
import os
from typing import Any, Dict, List, Optional

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import config


class PredictRequest(BaseModel):
	text: str = Field(..., min_length=1, description="Input text to classify")


class PredictBatchRequest(BaseModel):
	texts: List[str] = Field(..., min_length=1, description="List of input texts")


class EmotionPrediction(BaseModel):
	label: str
	score: float


class ChunkPrediction(BaseModel):
	chunk_id: int
	prediction: EmotionPrediction
	scores: Dict[str, float]


class PredictResponse(BaseModel):
	task_type: str
	prediction: EmotionPrediction
	scores: Dict[str, float]
	timeline: List[ChunkPrediction]


app = FastAPI(title="Emotion Inference API", version="1.0.0")

tokenizer = None
model = None
class_names: List[str] = []
task_type: str = config.TASK_TYPE
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_labels(model_dir: str) -> Dict[str, Any]:
	labels_path = os.path.join(model_dir, "labels.json")
	if os.path.exists(labels_path):
		with open(labels_path, "r", encoding="utf-8") as labels_file:
			payload = json.load(labels_file)
			loaded = payload.get("class_names", [])
			resolved_class_names = [str(item) for item in loaded] if isinstance(loaded, list) else []
			resolved_task_type = str(payload.get("task_type") or config.TASK_TYPE)
			return {
				"class_names": resolved_class_names,
				"task_type": resolved_task_type,
			}

	if config.CLASS_NAMES:
		return {
			"class_names": [str(item) for item in config.CLASS_NAMES],
			"task_type": config.TASK_TYPE,
		}

	return {
		"class_names": [],
		"task_type": config.TASK_TYPE,
	}


def _resolve_model_dir() -> str:
	candidates = [
		os.environ.get("MODEL_DIR"),
		config.EXPORTED_MODEL_DIR,
		config.OUTPUT_DIR,
	]
	for candidate in candidates:
		if not candidate:
			continue
		if os.path.exists(os.path.join(candidate, "config.json")):
			return candidate

	output_dir = config.OUTPUT_DIR
	if os.path.isdir(output_dir):
		checkpoints = [
			os.path.join(output_dir, entry)
			for entry in os.listdir(output_dir)
			if entry.startswith("checkpoint-") and os.path.isdir(os.path.join(output_dir, entry))
		]
		checkpoints.sort(key=os.path.getmtime, reverse=True)
		if checkpoints and os.path.exists(os.path.join(checkpoints[0], "config.json")):
			return checkpoints[0]

	raise FileNotFoundError(
		"No exported model found. Run training first so artifacts are saved in results/exported_model."
	)


def load_artifacts() -> None:
	global tokenizer, model, class_names, task_type

	model_dir = _resolve_model_dir()
	tokenizer = AutoTokenizer.from_pretrained(model_dir)
	model = AutoModelForSequenceClassification.from_pretrained(model_dir)
	model.to(device)
	model.eval()

	labels_payload = _load_labels(model_dir)
	class_names = labels_payload.get("class_names", [])
	loaded_task_type = str(labels_payload.get("task_type") or config.TASK_TYPE).strip().lower()
	task_type = loaded_task_type if loaded_task_type in {"single_label", "multi_label"} else config.TASK_TYPE

	if not class_names:
		model_num_labels = int(getattr(model.config, "num_labels", 0) or 0)
		class_names = [f"label_{idx}" for idx in range(model_num_labels)]


@app.on_event("startup")
def startup_event() -> None:
	load_artifacts()


def _predict_single(text: str) -> Dict[str, Any]:
	if tokenizer is None or model is None:
		raise RuntimeError("Model artifacts are not loaded")

	encoded = tokenizer(
		text,
		truncation=True,
		padding="max_length",
		max_length=config.MAX_LENGTH,
		return_overflowing_tokens=True,
		stride=20,
		return_tensors="pt",
	)
	
	# The model doesn't expect this mapping token
	if "overflow_to_sample_mapping" in encoded:
		del encoded["overflow_to_sample_mapping"]

	encoded = {key: value.to(device) for key, value in encoded.items()}

	with torch.no_grad():
		logits = model(**encoded).logits

	if task_type == "single_label":
		probabilities = torch.softmax(logits, dim=-1).detach().cpu().numpy()
	else:
		probabilities = torch.sigmoid(logits).detach().cpu().numpy()

	timeline = []
	for chunk_idx, chunk_probs in enumerate(probabilities):
		prediction_idx = int(chunk_probs.argmax())
		label_scores = {
			class_names[idx] if idx < len(class_names) else f"label_{idx}": float(score)
			for idx, score in enumerate(chunk_probs)
		}
		predicted_label = class_names[prediction_idx] if prediction_idx < len(class_names) else f"label_{prediction_idx}"
		
		timeline.append({
			"chunk_id": chunk_idx,
			"prediction": {
				"label": predicted_label,
				"score": float(chunk_probs[prediction_idx]),
			},
			"scores": label_scores,
		})

	avg_probabilities = probabilities.mean(axis=0)
	avg_prediction_idx = int(avg_probabilities.argmax())
	
	avg_label_scores = {
		class_names[idx] if idx < len(class_names) else f"label_{idx}": float(score)
		for idx, score in enumerate(avg_probabilities)
	}
	avg_predicted_label = class_names[avg_prediction_idx] if avg_prediction_idx < len(class_names) else f"label_{avg_prediction_idx}"

	return {
		"task_type": task_type,
		"prediction": {
			"label": avg_predicted_label,
			"score": float(avg_probabilities[avg_prediction_idx]),
		},
		"scores": avg_label_scores,
		"timeline": timeline,
	}


@app.get("/health")
def health() -> Dict[str, Any]:
	is_loaded = tokenizer is not None and model is not None
	return {
		"status": "ok" if is_loaded else "error",
		"loaded": is_loaded,
		"task_type": task_type,
		"device": str(device),
		"num_labels": len(class_names),
	}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> Dict[str, Any]:
	if not request.text.strip():
		raise HTTPException(status_code=400, detail="Text must not be empty")
	return _predict_single(request.text)


@app.post("/predict-batch")
def predict_batch(request: PredictBatchRequest) -> Dict[str, List[Dict[str, Any]]]:
	if not request.texts:
		raise HTTPException(status_code=400, detail="texts must not be empty")

	predictions: List[Dict[str, Any]] = []
	for text in request.texts:
		if not str(text).strip():
			predictions.append({"error": "Text must not be empty"})
			continue
		predictions.append(_predict_single(text))

	return {"predictions": predictions}
