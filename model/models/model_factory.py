from transformers import AutoTokenizer, AutoModelForSequenceClassification

def get_model(num_labels):
    model_name = "roberta-base"
    problem_type = "multi_label_classification"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels,
        problem_type=problem_type
    )
    return tokenizer, model
