"""Model lifecycle manager.

Detects available ML backends (scikit-learn always bundled with the app,
XGBoost optional), trains on built-in + user-labeled data, persists models
to disk and exposes a stable inference API.
"""
from __future__ import annotations

import logging
import os
import pickle
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings

logger = logging.getLogger("aegis.ai")

try:  # pragma: no cover - optional dependency
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.compose import ColumnTransformer
    HAS_SKLEARN = True
except Exception:  # pragma: no cover
    HAS_SKLEARN = False

try:  # pragma: no cover - optional dependency
    from xgboost import XGBClassifier

    HAS_XGBOOST = True
except Exception:  # pragma: no cover
    HAS_XGBOOST = False

try:  # pragma: no cover - optional dependency
    import spacy

    HAS_SPACY = True
    _NLP: object | None = None
    for _mdl in ("en_core_web_sm", "xx_ent_wiki_sm", "en_core_web_md"):
        try:
            _NLP = spacy.load(_mdl)
            break
        except Exception:
            continue
except Exception:  # pragma: no cover
    HAS_SPACY = False
    _NLP = None

try:  # pragma: no cover - optional dependency
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE = True
    _ST_MODEL = None
except Exception:  # pragma: no cover
    HAS_SENTENCE = False
    _ST_MODEL = None


@dataclass
class ModelInfo:
    name: str
    backend: str
    trained: bool
    samples: int = 0
    accuracy: float = 0.0
    features: list[str] = field(default_factory=list)
    available_backends: dict = field(default_factory=dict)


class _TfidfTextModel:
    """TF-IDF + logistic regression scam classifier."""

    def __init__(self) -> None:
        self.pipeline: object | None = None
        self.is_xgb = False

    def train(self, texts: list[str], labels: list[int]) -> dict:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score

        vectorizer = TfidfVectorizer(
            max_features=settings.ai_tfidf_max_features,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
        )
        clf = LogisticRegression(C=4.0, max_iter=1000, class_weight="balanced")
        pipeline = Pipeline([("tfidf", vectorizer), ("clf", clf)])
        pipeline.fit(texts, labels)
        self.pipeline = pipeline
        metrics: dict = {"samples": len(texts)}
        if len(set(labels)) > 1 and len(texts) >= 10:
            try:
                scores = cross_val_score(pipeline, texts, labels, cv=min(5, len(set(labels)) * 2))
                metrics["accuracy"] = round(float(scores.mean()), 4)
            except Exception as exc:  # pragma: no cover
                logger.warning("cross-validation failed: %s", exc)
        return metrics

    def predict(self, text: str) -> tuple[int, float, float]:
        if self.pipeline is None:
            return 0, 0.0, 0.0
        proba = self.pipeline.predict_proba([text])[0]
        label = int(np.argmax(proba))
        return label, float(proba[label]), float(proba[1])

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self.pipeline, fh)

    def load(self, path: Path) -> bool:
        if not path.exists():
            return False
        with open(path, "rb") as fh:
            self.pipeline = pickle.load(fh)
        return True


class _UrlFeatureModel:
    """Feature-vector + scaler model for URL classification."""

    def __init__(self) -> None:
        self.model = None
        self.scaler = None

    def train(self, rows: list[list[float]], labels: list[int]) -> dict:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score
        from sklearn.preprocessing import StandardScaler

        X = np.array(rows, dtype=float)
        y = np.array(labels, dtype=int)
        self.scaler = StandardScaler().fit(X)
        Xs = self.scaler.transform(X)
        self.model = LogisticRegression(C=2.0, max_iter=1000, class_weight="balanced")
        self.model.fit(Xs, y)
        metrics = {"samples": len(rows)}
        if len(set(labels)) > 1 and len(rows) >= 8:
            try:
                scores = cross_val_score(self.model, Xs, y, cv=min(5, len(set(labels))))
                metrics["accuracy"] = round(float(scores.mean()), 4)
            except Exception as exc:  # pragma: no cover
                logger.warning("cross-validation failed: %s", exc)
        return metrics

    def predict(self, row: list[float]) -> tuple[int, float, float]:
        if self.model is None or self.scaler is None:
            return 0, 0.0, 0.0
        X = self.scaler.transform(np.array([row], dtype=float))
        proba = self.model.predict_proba(X)[0]
        label = int(np.argmax(proba))
        return label, float(proba[label]), float(proba[1])

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump({"model": self.model, "scaler": self.scaler}, fh)

    def load(self, path: Path) -> bool:
        if not path.exists():
            return False
        with open(path, "rb") as fh:
            data = pickle.load(fh)
        self.model = data["model"]
        self.scaler = data["scaler"]
        return True


class ModelManager:
    """Singleton that owns all trained models and offers lazy training."""

    def __init__(self) -> None:
        self.model_dir = Path(settings.ai_model_dir)
        self.text_model = _TfidfTextModel()
        self.url_model = _UrlFeatureModel()
        self._loaded = False

    # --- capability reporting -------------------------------------------
    def capabilities(self) -> dict:
        return {
            "sklearn": HAS_SKLEARN,
            "xgboost": HAS_XGBOOST,
            "spacy": HAS_SPACY,
            "sentence_transformers": HAS_SENTENCE,
            "text_model_trained": self.text_model.pipeline is not None,
            "url_model_trained": self.url_model.model is not None,
        }

    def info(self) -> ModelInfo:
        return ModelInfo(
            name="AEGIS on-device classifier",
            backend="sklearn" + ("+xgboost" if HAS_XGBOOST else ""),
            trained=self.text_model.pipeline is not None or self.url_model.model is not None,
            samples=0,
            available_backends=self.capabilities(),
        )

    # --- loading ---------------------------------------------------------
    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        try:
            self.text_model.load(self.model_dir / "text_model.pkl")
            self.url_model.load(self.model_dir / "url_model.pkl")
        except Exception as exc:  # pragma: no cover
            logger.warning("model load failed: %s", exc)
        self._loaded = True

    def load(self) -> None:
        self.ensure_loaded()

    # --- training --------------------------------------------------------
    def train_all(
        self,
        extra_text_pairs: list[tuple[str, int]] | None = None,
        extra_url_rows: list[tuple[list[float], int]] | None = None,
    ) -> dict:
        from app.ai.dataset import labeled_text_pairs, labeled_url_pairs
        from app.ai.features import build_text_feature_row, build_url_feature_row

        if not HAS_SKLEARN:  # pragma: no cover
            raise RuntimeError("scikit-learn is required to train models")

        texts: list[str] = []
        labels: list[int] = []
        for text, label in labeled_text_pairs():
            texts.append(text)
            labels.append(label)
        if extra_text_pairs:
            for text, label in extra_text_pairs:
                texts.append(text)
                labels.append(label)

        metrics_text = self.text_model.train(texts, labels)
        self.text_model.save(self.model_dir / "text_model.pkl")

        rows: list[list[float]] = []
        url_labels: list[int] = []
        for url, label in labeled_url_pairs():
            rows.append(build_url_feature_row(url))
            url_labels.append(label)
        if extra_url_rows:
            for row, label in extra_url_rows:
                rows.append(row)
                url_labels.append(label)
        metrics_url = self.url_model.train(rows, url_labels)
        self.url_model.save(self.model_dir / "url_model.pkl")
        self._loaded = True
        return {
            "text": metrics_text,
            "url": metrics_url,
            "backends": self.capabilities(),
        }

    # --- inference --------------------------------------------------------
    def predict_text(self, text: str) -> tuple[int, float, float]:
        self.ensure_loaded()
        if self.text_model.pipeline is None:
            return 0, 0.0, 0.0
        return self.text_model.predict(text)

    def predict_url(self, row: list[float]) -> tuple[int, float, float]:
        self.ensure_loaded()
        if self.url_model.model is None:
            return 0, 0.0, 0.0
        return self.url_model.predict(row)

    def explain_text(self, text: str) -> list[str]:
        """Return human-readable reasons from the spaCy model if present."""
        if not HAS_SPACY or _NLP is None:  # pragma: no cover
            return []
        doc = _NLP(text[:4000])
        out: list[str] = []
        for ent in doc.ents:
            if ent.label_ in ("PERSON", "ORG", "GPE"):
                out.append(f"The text mentions {ent.label_.lower()} '{ent.text}'")
        return out[:5]


model_manager = ModelManager()
