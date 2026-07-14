import pandas as pd
import numpy as np
import os

class DatasetLoader:
    def __init__(
        self,
        file_path,
        text_column,
        emotion_columns=None,
        test_size=0.2,
        random_seed=42,
    ):
        self.file_path = file_path
        self.text_column = text_column
        self.emotion_columns = emotion_columns or []
        self.test_size = test_size
        self.random_seed = random_seed

    @staticmethod
    def _read_table(path):
        _, extension = os.path.splitext(path.lower())
        separator = "\t" if extension in {".tsv", ".txt"} else ","
        return pd.read_csv(path, sep=separator)

    @staticmethod
    def _pick_existing_path(base_path, candidates):
        for candidate in candidates:
            candidate_path = os.path.join(base_path, candidate)
            if os.path.exists(candidate_path):
                return candidate_path
        return None

    def load_data(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Dataset path does not exist: {self.file_path}")

        if os.path.isdir(self.file_path):
            train_path = self._pick_existing_path(
                self.file_path,
                ["train.csv", "train.tsv", "training.csv", "training.tsv"]
            )
            val_path = self._pick_existing_path(
                self.file_path,
                ["val.csv", "val.tsv", "validation.csv", "validation.tsv", "dev.csv", "dev.tsv"]
            )
            if not train_path or not val_path:
                raise ValueError(f"Could not find train/validation splits in {self.file_path}")

            train_df = self._read_table(train_path)
            val_df = self._read_table(val_path)

            train_texts = train_df[self.text_column].astype(str).tolist()
            train_labels = train_df[self.emotion_columns].values.astype(np.float32)

            val_texts = val_df[self.text_column].astype(str).tolist()
            val_labels = val_df[self.emotion_columns].values.astype(np.float32)

            return train_texts, val_texts, train_labels, val_labels, len(self.emotion_columns), self.emotion_columns

        df = self._read_table(self.file_path)
        texts = df[self.text_column].astype(str).tolist()
        labels = df[self.emotion_columns].values.astype(np.float32)

        from sklearn.model_selection import train_test_split
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts,
            labels,
            test_size=self.test_size,
            random_state=self.random_seed
        )
        return train_texts, val_texts, train_labels, val_labels, len(self.emotion_columns), self.emotion_columns
