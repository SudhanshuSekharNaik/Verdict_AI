from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ml.classification.case_classifier import DocumentClassifier
    from ml.classification.sentence_classifier import LegalSentenceClassifier
    from ml.ner.legal_ner import LegalNER
    from ml.nli.contradiction_engine import ContradictionEngine
    from ml.similarity.sentence_embedder import SentenceEmbedder


class MLRegistry:
    _instances = {}

    @classmethod
    def get_ner(cls) -> LegalNER:
        if "ner" not in cls._instances:
            from ml.ner.legal_ner import LegalNER

            cls._instances["ner"] = LegalNER()
        return cls._instances["ner"]

    @classmethod
    def get_classifier(cls) -> DocumentClassifier:
        if "classifier" not in cls._instances:
            from ml.classification.case_classifier import DocumentClassifier

            cls._instances["classifier"] = DocumentClassifier()
        return cls._instances["classifier"]

    @classmethod
    def get_sentence_classifier(cls) -> LegalSentenceClassifier:
        if "sentence_classifier" not in cls._instances:
            from ml.classification.sentence_classifier import LegalSentenceClassifier

            cls._instances["sentence_classifier"] = LegalSentenceClassifier()
        return cls._instances["sentence_classifier"]

    @classmethod
    def get_nli(cls) -> ContradictionEngine:
        if "nli" not in cls._instances:
            from ml.nli.contradiction_engine import ContradictionEngine

            cls._instances["nli"] = ContradictionEngine()
        return cls._instances["nli"]

    @classmethod
    def get_embedder(cls) -> SentenceEmbedder:
        if "embedder" not in cls._instances:
            from ml.similarity.sentence_embedder import SentenceEmbedder

            cls._instances["embedder"] = SentenceEmbedder()
        return cls._instances["embedder"]


def get_ml_registry() -> MLRegistry:
    return MLRegistry()


__all__ = [
    "ContradictionEngine",
    "DocumentClassifier",
    "LegalNER",
    "LegalSentenceClassifier",
    "MLRegistry",
    "SentenceEmbedder",
    "get_ml_registry",
]
