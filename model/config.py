MODEL_NAME = "roberta-base"
import os
TASK_TYPE = "multi_label"

def _first_existing_path(candidates):
    return next((path for path in candidates if os.path.exists(path)), None)

def _resolve_goemotions_path():
    env_path = os.getenv("GOEMOTIONS_DATA_PATH")
    if env_path:
        return env_path
    if os.path.exists("/kaggle/input"):
        for root, dirs, files in os.walk("/kaggle/input"):
            if "train.tsv" in files:
                return root
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
        path = kagglehub.dataset_download("debarshichanda/goemotions")
        if os.path.exists(os.path.join(path, "data")):
            return os.path.join(path, "data")
        return path
    return "data/goemotions"
DATA_PATH = _resolve_goemotions_path()
TEXT_COLUMN = os.getenv("TEXT_COLUMN", "text")
LABEL_COLUMN = None
CLASS_NAMES = None
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
