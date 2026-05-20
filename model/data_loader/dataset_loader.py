import pandas as pd
import numpy as np
import os
import re
from sklearn.model_selection import train_test_split

class DatasetLoader:
    """
    Loads emotion datasets for either:
    - single-label classification (e.g., ISEAR)
    - multi-label classification (e.g., GoEmotions)
    """

    def __init__(
        self,
        file_path,
        text_column,
        task_type,
        emotion_columns=None,
        label_column=None,
        class_names=None,
        test_size=0.2,
        random_seed=42,
    ):
        self.file_path = file_path
        self.text_column = text_column
        self.task_type = task_type
        self.emotion_columns = emotion_columns or []
        self.label_column = label_column
        self.class_names = class_names
        self.test_size = test_size
        self.random_seed = random_seed

    @staticmethod
    def _read_table(path):
        _, extension = os.path.splitext(path.lower())
        separator = "\t" if extension in {".tsv", ".txt"} else ","
        df = pd.read_csv(path, sep=separator)

        # GoEmotions split files are often TSV without a header row.
        if extension == ".tsv":
            normalized_columns = {str(column).strip().lower() for column in df.columns}
            if "labels" not in normalized_columns and "text" not in normalized_columns and df.shape[1] >= 2:
                names = ["text", "labels", "id"]
                use_columns = [0, 1, 2] if df.shape[1] >= 3 else [0, 1]
                df = pd.read_csv(path, sep=separator, header=None, names=names[: len(use_columns)], usecols=use_columns)

        return df

    @staticmethod
    def _pick_existing_path(base_path, candidates):
        for candidate in candidates:
            candidate_path = os.path.join(base_path, candidate)
            if os.path.exists(candidate_path):
                return candidate_path
        return None

    @staticmethod
    def _resolve_text_column(df, preferred_column):
        if preferred_column in df.columns:
            return preferred_column

        for candidate in ["text", "comment_text", "content", "sentence"]:
            if candidate in df.columns:
                return candidate

        raise ValueError(
            f"Text column '{preferred_column}' not found in dataset. Available columns: {list(df.columns)}"
        )

    @staticmethod
    def _labels_to_multi_hot(raw_labels, num_labels):
        vector = np.zeros(num_labels, dtype=np.float32)
        if pd.isna(raw_labels):
            return vector

        for match in re.findall(r"\d+", str(raw_labels)):
            label_index = int(match)
            if 0 <= label_index < num_labels:
                vector[label_index] = 1.0
        return vector


    def _load_single_label_data(self, df):
        text_column = self._resolve_text_column(df, self.text_column)

        if not self.label_column:
            raise ValueError("label_column must be provided for single_label task type")

        if self.label_column not in df.columns:
            raise ValueError(
                f"Label column '{self.label_column}' not found in dataset. Available columns: {list(df.columns)}"
            )

        data = df[[text_column, self.label_column]].dropna(subset=[text_column, self.label_column]).copy()
        data[text_column] = data[text_column].astype(str)
        data[self.label_column] = data[self.label_column].astype(str).str.strip().str.lower()

        if self.class_names:
            class_names = [str(name).strip().lower() for name in self.class_names]
        else:
            class_names = sorted(data[self.label_column].unique().tolist())

        label_to_id = {label: idx for idx, label in enumerate(class_names)}
        unknown_labels = sorted(set(data[self.label_column].unique()) - set(label_to_id.keys()))
        if unknown_labels:
            raise ValueError(
                f"Found labels not present in class_names: {unknown_labels}. "
                "Set CLASS_NAMES=None in config.py to auto-infer labels from data."
            )

        texts = data[text_column].tolist()
        labels = data[self.label_column].map(label_to_id).values.astype(np.int64)

        stratify_labels = labels if len(np.unique(labels)) > 1 else None
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts,
            labels,
            test_size=self.test_size,
            random_state=self.random_seed,
            stratify=stratify_labels,
        )

        return train_texts, val_texts, train_labels, val_labels, len(class_names), class_names


    def _extract_multi_label_arrays(self, df):
        text_column = self._resolve_text_column(df, self.text_column)

        # Preferred format: one column per emotion
        has_emotion_columns = all(column in df.columns for column in self.emotion_columns)
        if has_emotion_columns:
            required_columns = [text_column] + self.emotion_columns
            data = df[required_columns].dropna(subset=[text_column]).copy()
            data[text_column] = data[text_column].astype(str)
            data[self.emotion_columns] = data[self.emotion_columns].fillna(0)

            texts = data[text_column].tolist()
            labels = data[self.emotion_columns].values.astype(np.float32)
        # Fallback format: single "labels" column with comma-separated ids
        elif "labels" in df.columns:
            data = df[[text_column, "labels"]].dropna(subset=[text_column]).copy()
            data[text_column] = data[text_column].astype(str)
            texts = data[text_column].tolist()

            num_labels = len(self.emotion_columns)
            labels = np.vstack(
                [self._labels_to_multi_hot(raw_labels, num_labels) for raw_labels in data["labels"].tolist()]
            )
        else:
            raise ValueError(
                "Dataset must contain either all emotion columns or a 'labels' column. "
                f"Available columns: {list(df.columns)}"
            )

        return texts, labels

    def _load_multi_label_data(self, df):
        texts, labels = self._extract_multi_label_arrays(df)

        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts,
            labels,
            test_size=self.test_size,
            random_state=self.random_seed,
        )

        return train_texts, val_texts, train_labels, val_labels, len(self.emotion_columns), self.emotion_columns

    def _load_multi_label_from_split_directory(self):
        if not os.path.isdir(self.file_path):
            return None

        train_path = self._pick_existing_path(
            self.file_path,
            ["train.csv", "train.tsv", "training.csv", "training.tsv"],
        )
        val_path = self._pick_existing_path(
            self.file_path,
            ["val.csv", "val.tsv", "validation.csv", "validation.tsv", "dev.csv", "dev.tsv"],
        )
        test_path = self._pick_existing_path(
            self.file_path,
            ["test.csv", "test.tsv"],
        )

        if not train_path:
            return None

        if not val_path:
            if test_path:
                val_path = test_path
            else:
                raise ValueError(
                    "Found GoEmotions train split but no validation/dev/test split. "
                    f"Directory checked: {self.file_path}"
                )

        train_df = self._read_table(train_path)
        val_df = self._read_table(val_path)

        train_texts, train_labels = self._extract_multi_label_arrays(train_df)
        val_texts, val_labels = self._extract_multi_label_arrays(val_df)

        return (
            train_texts,
            val_texts,
            train_labels,
            val_labels,
            len(self.emotion_columns),
            self.emotion_columns,
        )

    
    def load_data(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(
                f"Dataset path does not exist: {self.file_path}. "
                "Set GOEMOTIONS_DATA_PATH or ISEAR_DATA_PATH in config/environment."
            )

        if self.task_type == "multi_label":
            split_data = self._load_multi_label_from_split_directory()
            if split_data is not None:
                return split_data

        df = self._read_table(self.file_path)

        if self.task_type == "single_label":
            return self._load_single_label_data(df)

        if self.task_type == "multi_label":
            return self._load_multi_label_data(df)

        raise ValueError("task_type must be either 'single_label' or 'multi_label'")
