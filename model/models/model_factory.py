from transformers import AutoTokenizer, AutoModelForSequenceClassification

def get_model(model_name, num_labels, task_type="single_label"):
    if task_type not in ("single_label", "multi_label"):
        raise ValueError("task_type must be either 'single_label' or 'multi_label'")

    problem_type = "single_label_classification" if task_type == "single_label" else "multi_label_classification"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=num_labels,
        problem_type=problem_type
    )
    return tokenizer, model