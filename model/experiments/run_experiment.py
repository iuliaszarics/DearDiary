from data_loader.dataset_loader import DatasetLoader
from models.model_factory import get_model
from models.trainer import train_model
import json
import os
from config import (
	DATA_PATH,
	TEXT_COLUMN,
	EMOTION_COLUMNS,
	LABEL_COLUMN,
	CLASS_NAMES,
	MODEL_NAME,
	TASK_TYPE,
	TRAIN_TEST_SPLIT,
	RANDOM_SEED,
	EXPORTED_MODEL_DIR,
)


loader = DatasetLoader(
	file_path=DATA_PATH,
	text_column=TEXT_COLUMN,
	task_type=TASK_TYPE,
	emotion_columns=EMOTION_COLUMNS,
	label_column=LABEL_COLUMN,
	class_names=CLASS_NAMES,
	test_size=TRAIN_TEST_SPLIT,
	random_seed=RANDOM_SEED,
)

train_texts, val_texts, train_labels, val_labels, num_labels, class_names = loader.load_data()
tokenizer, model = get_model(MODEL_NAME, num_labels, task_type=TASK_TYPE)
results = train_model(
	model,
	tokenizer,
	train_texts,
	val_texts,
	train_labels,
	val_labels,
	task_type=TASK_TYPE,
)

print("Classes:", class_names)
print("Evaluation results:", results)

# Export artifacts for inference app consumption.
os.makedirs(EXPORTED_MODEL_DIR, exist_ok=True)
model.save_pretrained(EXPORTED_MODEL_DIR)
tokenizer.save_pretrained(EXPORTED_MODEL_DIR)

labels_payload = {
	"task_type": TASK_TYPE,
	"class_names": [str(label) for label in class_names],
}
with open(os.path.join(EXPORTED_MODEL_DIR, "labels.json"), "w", encoding="utf-8") as labels_file:
	json.dump(labels_payload, labels_file, ensure_ascii=True, indent=2)

print("Exported artifacts to:", EXPORTED_MODEL_DIR)
 