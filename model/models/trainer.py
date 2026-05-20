import torch
from transformers import Trainer, TrainingArguments
from torch.utils.data import Dataset
from utils.utils import compute_metrics
import config
import random
import numpy as np
from functools import partial

class EmotionDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, task_type="single_label", max_len=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.task_type = task_type
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding='max_length',
            max_length=self.max_len,
            return_tensors='pt'
        )

        label_dtype = torch.long if self.task_type == "single_label" else torch.float32
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.labels[idx], dtype=label_dtype)
        }

def check_device():
    """Check if GPU is available and print device information"""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"✓ GPU is available! Using device: {torch.cuda.get_device_name(0)}")
        print(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        device = torch.device("cpu")
        print("⚠ GPU not available. Using CPU for training (this may be slow).")
    return device

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def train_model(model, tokenizer, train_texts, val_texts, train_labels, val_labels, task_type="single_label"):
    device = check_device()
    train_dataset = EmotionDataset(train_texts, train_labels, tokenizer, task_type=task_type)
    val_dataset = EmotionDataset(val_texts, val_labels, tokenizer, task_type=task_type)
    training_args = TrainingArguments(
        output_dir=config.OUTPUT_DIR,
        per_device_train_batch_size=config.BATCH_SIZE,
        per_device_eval_batch_size=config.BATCH_SIZE,
        num_train_epochs=config.EPOCHS,
        learning_rate=config.LEARNING_RATE,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True
    )
    set_seed(config.RANDOM_SEED)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=partial(compute_metrics, task_type=task_type)
    )

    trainer.train()
    results = trainer.evaluate()
    return results
    

