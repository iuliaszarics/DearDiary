# MODEL_NAME = "bert-base-uncased"
MODEL_NAME = "distilbert-base-uncased"
# MODEL_NAME = "roberta-base"
# MODEL_NAME = "xlnet-base-cased"
# MODEL_NAME = "google/bigbird-roberta-base"

import os

# Supported values: "single_label" (ISEAR) or "multi_label" (GoEmotions)
TASK_TYPE = os.getenv("TASK_TYPE", "single_label").strip().lower()
if TASK_TYPE not in ("single_label", "multi_label"):
    raise ValueError("TASK_TYPE must be either 'single_label' or 'multi_label'")


def _first_existing_path(candidates):
    return next((path for path in candidates if os.path.exists(path)), None)


def _resolve_isear_path():
    env_path = os.getenv("ISEAR_DATA_PATH")
    if env_path:
        return env_path

    if os.path.exists("/kaggle/input"):
        kaggle_candidates = [
            "/kaggle/input/isear-dataset/eng_dataset.csv",
            "/kaggle/input/isear/eng_dataset.csv",
            "/kaggle/input/isear/isear.csv",
            "/kaggle/input/isear/ISEAR.csv",
        ]
        existing = _first_existing_path(kaggle_candidates)
        if existing:
            return existing
        return kaggle_candidates[0]

    local_candidates = [
        "data/eng_dataset.csv",
        "data/isear.csv",
        "data/ISEAR.csv",
    ]
    existing = _first_existing_path(local_candidates)
    return existing or local_candidates[0]


def _resolve_goemotions_path():
    env_path = os.getenv("GOEMOTIONS_DATA_PATH")
    if env_path:
        return env_path

    if os.path.exists("/kaggle/input"):
        kaggle_candidates = [
            "/kaggle/input/goemotions",
            "/kaggle/input/goemotions-dataset",
            "/kaggle/input/debarshichanda-goemotions",
        ]
        existing = _first_existing_path(kaggle_candidates)
        if existing:
            return existing

    local_candidates = [
        "data/goemotions",
        "data/goemotions.csv",
        "data/goemotions.tsv",
    ]
    existing = _first_existing_path(local_candidates)
    if existing:
        return existing

    if os.getenv("AUTO_DOWNLOAD_GOEMOTIONS", "0") == "1":
        try:
            import kagglehub
        except ImportError as exc:
            raise ImportError(
                "AUTO_DOWNLOAD_GOEMOTIONS=1 requires kagglehub. Install it with: pip install kagglehub"
            ) from exc

        return kagglehub.dataset_download("debarshichanda/goemotions")

    # Fallback to a standard location so the error message points to an expected path.
    return "data/goemotions"


if TASK_TYPE == "multi_label":
    DATA_PATH = _resolve_goemotions_path()
    TEXT_COLUMN = os.getenv("TEXT_COLUMN", "text")
    LABEL_COLUMN = None
    CLASS_NAMES = None
else:
    DATA_PATH = _resolve_isear_path()
    TEXT_COLUMN = os.getenv("TEXT_COLUMN", "content")
    LABEL_COLUMN = os.getenv("LABEL_COLUMN", "sentiment")
    # Set to None to infer sorted classes from dataset
    CLASS_NAMES = ["anger", "fear", "joy", "sadness"]

# Kept for optional GoEmotions multi-label compatibility
EMOTION_COLUMNS = [
    "admiration", "amusement", "anger", "annoyance", "approval", "caring",
    "confusion", "curiosity", "desire", "disappointment", "disapproval",
    "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
    "joy", "love", "nervousness", "optimism", "pride", "realization",
    "relief", "remorse", "sadness", "surprise", "neutral"
]

BATCH_SIZE = 16
EPOCHS = 3
LEARNING_RATE = 2e-5
MAX_LENGTH = 128
TRAIN_TEST_SPLIT = 0.2
OUTPUT_DIR = "./results"
EXPORTED_MODEL_DIR = "./results/exported_model"
RANDOM_SEED = 42