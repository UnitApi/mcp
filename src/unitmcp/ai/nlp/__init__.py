"""
UnitMCP Natural Language Processing Module

This module provides natural language processing capabilities for UnitMCP,
including tokenization, entity extraction, and sentiment analysis.
"""

from .huggingface import (
    HuggingFaceConfig,
    HuggingFaceNLPModel,
)

from .spacy_integration import (
    SpacyConfig,
    SpacyNLPModel,
)

__all__ = [
    'HuggingFaceConfig',
    'HuggingFaceNLPModel',
    'SpacyConfig',
    'SpacyNLPModel',
]
