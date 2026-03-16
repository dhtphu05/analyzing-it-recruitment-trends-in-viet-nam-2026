"""Shared utility functions for processing modules."""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd


def strip_accents(text: str) -> str:
    """Remove Vietnamese diacritics and normalize Unicode characters."""
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    return stripped.replace("\u0111", "d").replace("\u0110", "D")


def normalize_text(value: object) -> object:
    """Normalize whitespace and return NaN for empty/null values."""
    if pd.isna(value):
        return np.nan
    text = unicodedata.normalize("NFC", str(value)).strip()
    text = re.sub(r"\s+", " ", text)
    return text or np.nan


def slugify_key(value: object) -> str:
    """Convert value to a lowercase ASCII key for dictionary lookups."""
    if pd.isna(value):
        return ""
    text = strip_accents(str(value).lower())
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
