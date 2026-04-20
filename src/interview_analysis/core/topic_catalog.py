from __future__ import annotations

TOPIC_LABELS: dict[str, str] = {
    "http_api": "HTTP API \u0438 REST-\u043f\u043e\u0434\u0445\u043e\u0434",
    "sql_performance": "SQL: \u0438\u043d\u0434\u0435\u043a\u0441\u044b \u0438 \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u044c\u043d\u043e\u0441\u0442\u044c",
    "distributed_systems": "\u0420\u0430\u0441\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u043d\u044b\u0435 \u0441\u0438\u0441\u0442\u0435\u043c\u044b \u0438 \u043d\u0430\u0434\u0435\u0436\u043d\u043e\u0441\u0442\u044c",
    "react_basics": "React: Virtual DOM \u0438 \u043e\u0441\u043d\u043e\u0432\u044b \u043a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442\u043e\u0432",
    "frontend_architecture": "Frontend-\u0430\u0440\u0445\u0438\u0442\u0435\u043a\u0442\u0443\u0440\u0430 \u0438 \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0435 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f",
    "containers": "Docker \u0438 \u043a\u043e\u043d\u0442\u0435\u0439\u043d\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f",
    "delivery_pipeline": "CI/CD \u0438 delivery pipeline",
}


def topic_label(topic_code: str) -> str:
    if topic_code in TOPIC_LABELS:
        return TOPIC_LABELS[topic_code]
    return topic_code.replace("_", " ").strip().capitalize()
