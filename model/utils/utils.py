import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, hamming_loss

def compute_metrics(eval_pred, task_type="single_label"):
    logits, labels = eval_pred

    if task_type == "single_label":
        predictions = np.argmax(logits, axis=-1)

        accuracy = accuracy_score(labels, predictions)
        precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
            labels,
            predictions,
            average="macro",
            zero_division=0
        )
        precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
            labels,
            predictions,
            average="weighted",
            zero_division=0
        )

        return {
            "accuracy": accuracy,
            "precision_macro": precision_macro,
            "recall_macro": recall_macro,
            "f1_macro": f1_macro,
            "precision_weighted": precision_weighted,
            "recall_weighted": recall_weighted,
            "f1_weighted": f1_weighted,
        }
    
    # For multi-label classification, apply sigmoid and threshold at 0.5
    predictions = (1 / (1 + np.exp(-logits))) > 0.5
    
    # Subset accuracy: exact match across all labels
    subset_accuracy = accuracy_score(labels, predictions)
    
    # Hamming loss: fraction of incorrectly predicted labels
    hamming = hamming_loss(labels, predictions)
    
    # Macro-averaged precision, recall, and F1
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="macro",
        zero_division=0
    )
    
    # Micro-averaged metrics
    precision_micro, recall_micro, f1_micro, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="micro",
        zero_division=0
    )
    
    return {
        "subset_accuracy": subset_accuracy,
        "hamming_loss": hamming,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
        "precision_micro": precision_micro,
        "recall_micro": recall_micro,
        "f1_micro": f1_micro
    }