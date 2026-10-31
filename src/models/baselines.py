"""
Classical Machine Learning Baselines for Multi-Label AMR Prediction
Implements k-mer frequency feature extraction with Logistic Regression,
Random Forest, and XGBoost Multi-Output Classifiers.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from xgboost import XGBClassifier


class GenomicKmerFeatureExtractor:
    """Extracts k-mer frequency and TF-IDF representations from concatenated genome chunks."""

    def __init__(self, k: int = 5, max_features: int = 1000):
        self.k = k
        self.max_features = max_features
        # Character n-gram vectorizer over DNA strings
        self.vectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(k, k),
            max_features=max_features,
            sublinear_tf=True
        )

    def fit_transform(self, genome_sequences: List[str]) -> np.ndarray:
        return self.vectorizer.fit_transform(genome_sequences).toarray()

    def transform(self, genome_sequences: List[str]) -> np.ndarray:
        return self.vectorizer.transform(genome_sequences).toarray()


class MLBaselinesPipeline:
    """Manages training and evaluation of classical ML baselines."""

    def __init__(self, k: int = 5, max_features: int = 1000, random_state: int = 42):
        self.feature_extractor = GenomicKmerFeatureExtractor(k=k, max_features=max_features)
        self.random_state = random_state

        self.models: Dict[str, Any] = {
            "Logistic Regression": MultiOutputClassifier(
                LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_state)
            ),
            "Random Forest": MultiOutputClassifier(
                RandomForestClassifier(n_estimators=100, max_depth=12, random_state=random_state)
            ),
            "XGBoost": MultiOutputClassifier(
                XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.08, eval_metric="logloss", random_state=random_state)
            )
        }
        self.trained_models: Dict[str, Any] = {}

    def fit(self, train_texts: List[str], y_train: np.ndarray):
        """Fit feature extractor and all baseline models on training genomes."""
        print(f"Extracting k-mer TF-IDF features (max_features={self.feature_extractor.max_features})...")
        X_train = self.feature_extractor.fit_transform(train_texts)

        for name, model in self.models.items():
            print(f"Training baseline: {name}...")
            model.fit(X_train, y_train)
            self.trained_models[name] = model

    def predict_proba(self, test_texts: List[str]) -> Dict[str, np.ndarray]:
        """Generate predicted probabilities across all 5 classes for each baseline model."""
        X_test = self.feature_extractor.transform(test_texts)
        predictions = {}

        for name, model in self.trained_models.items():
            # MultiOutputClassifier.predict_proba returns list of length C with (N, 2) arrays
            probas_list = model.predict_proba(X_test)
            # Stack positive class probabilities -> (N, C)
            pos_probas = np.column_stack([p[:, 1] if p.shape[1] > 1 else p[:, 0] for p in probas_list])
            predictions[name] = pos_probas

        return predictions

