from __future__ import annotations

import re


TOKEN_RE = re.compile(r"\w+", re.UNICODE)
STOPWORDS = {
    "and",
    "are",
    "for",
    "that",
    "the",
    "with",
    "это",
    "как",
    "при",
    "для",
    "или",
    "что",
    "если",
    "также",
    "надо",
    "быть",
    "когда",
    "чтобы",
}


def normalize_answer(text: str) -> str:
    return " ".join(text.strip().casefold().split())


def tokenize(text: str) -> list[str]:
    return [match.group(0).casefold() for match in TOKEN_RE.finditer(text)]


def significant_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if len(token) > 2 and token not in STOPWORDS]
