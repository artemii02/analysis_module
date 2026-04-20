from __future__ import annotations

from interview_analysis.core.topic_catalog import topic_label


def test_topic_label_returns_human_readable_russian_titles() -> None:
    assert topic_label('http_api') == "HTTP API и REST-подход"
    assert topic_label('sql_performance') == "SQL: индексы и производительность"
    assert topic_label('unknown_topic') == 'Unknown topic'
