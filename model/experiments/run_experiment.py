from data_loader.dataset_loader import DatasetLoader
from models.model_factory import get_model
from models.trainer import train_model
import json
import os
from config import (
    DATA_PATH,
    TEXT_COLUMN,
    EMOTION_COLUMNS,
    TRAIN_TEST_SPLIT,
    RANDOM_SEED,
    EXPORTED_MODEL_DIR,
)

loader = DatasetLoader(
    file_path=DATA_PATH,
    text_column=TEXT_COLUMN,
    emotion_columns=EMOTION_COLUMNS,
    test_size=TRAIN_TEST_SPLIT,
    random_seed=RANDOM_SEED,
)

train_texts, val_texts, train_labels, val_labels, num_labels, class_names = loader.load_data()
tokenizer, model = get_model(num_labels)

results = train_model(
    model,
    tokenizer,
    train_texts,
    val_texts,
    train_labels,
    val_labels,
)

print("Classes:", class_names)
print("Evaluation results:", results)

os.makedirs(EXPORTED_MODEL_DIR, exist_ok=True)
model.save_pretrained(EXPORTED_MODEL_DIR)
tokenizer.save_pretrained(EXPORTED_MODEL_DIR)

labels_payload = {
    "task_type": "multi_label",
    "class_names": [str(label) for label in class_names],
}

with open(os.path.join(EXPORTED_MODEL_DIR, "labels.json"), "w", encoding="utf-8") as labels_file:
    json.dump(labels_payload, labels_file, ensure_ascii=True, indent=2)

print("Exported artifacts to:", EXPORTED_MODEL_DIR)
