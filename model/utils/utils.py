import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, hamming_loss

def compute_metrics(eval_pred, task_type="multi_label"):
    logits, labels = eval_pred
    predictions = (1 / (1 + np.exp(-logits))) > 0.5
    subset_accuracy = accuracy_score(labels, predictions)
    hamming = hamming_loss(labels, predictions)
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="macro",
        zero_division=0
    )
    
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
