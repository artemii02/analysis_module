# Модуль анализа ответов на интервью

Это отдельный сервис на FastAPI для анализа ответов пользователя на технические вопросы интервью.

Что делает модуль:
- принимает список вопросов и ответов по одной сессии;
- оценивает каждый ответ локальной LLM через Ollama;
- строит итоговый JSON-отчёт по сессии;
- сохраняет задания и отчёты в PostgreSQL;
- отдаёт question bank и OpenAPI-контракт для интеграции с backend.

Текущая демонстрационная сборка работает как отдельный модуль общего проекта и подходит для записи демонстрации контрольной точки.

## Технологии

- FastAPI
- PostgreSQL
- Docker / Docker Compose
- Ollama
- локальная модель `qwen2.5:3b`

## Быстрый запуск

1. Установить Docker Desktop.
2. Открыть корень проекта.
3. Запустить `start.bat`.
4. Дождаться поднятия контейнеров и первой загрузки модели `qwen2.5:3b`.
5. Открыть `http://127.0.0.1:8000/demo`.

Для остановки использовать `stop.bat`.

## Что доступно после запуска

- Demo UI: `http://127.0.0.1:8000/demo`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Health: `http://127.0.0.1:8000/assessment/v1/health`

## Как проверить модуль вручную

1. Открыть `/demo`.
2. Выбрать набор вопросов.
3. Вписать ответы вручную в текстовые поля.
4. Нажать `Сгенерировать отчёт`.
5. Проверить, что на странице появились:
   - общий балл;
   - оценки по критериям;
   - разбор по каждому вопросу;
   - рекомендации;
   - итоговый JSON-ответ.

Для демонстрации доступен набор `Backend Junior: 10 вопросов`.

## Интеграция с backend

Основной сценарий интеграции:
1. backend получает или формирует список вопросов текущей сессии;
2. backend отправляет JSON в `POST /assessment/v1/report`;
3. модуль возвращает готовый JSON-отчёт;
4. backend сохраняет отчёт у себя или показывает его в основном приложении.

Для защищённых endpoint нужно передавать заголовок:

```http
X-API-Key: demo-api-key
```

Если ключ будет изменён через переменную окружения `ANALYSIS_API_KEY`, backend должен использовать новое значение.

## Получение банка вопросов

`GET /assessment/v1/questions?specialization=backend&grade=junior&limit=10`

Пример ответа:

```json
{
  "status": "ok",
  "specialization": "backend",
  "grade": "junior",
  "count": 10,
  "items": [
    {
      "question_id": "backend_junior_rest_methods",
      "specialization": "backend",
      "grade": "junior",
      "topic_code": "http_api",
      "topic_label": "HTTP API и REST-подход",
      "question_text": "Чем отличаются методы GET, POST, PUT и DELETE в REST API?",
      "tags": ["http", "rest", "crud"],
      "version": "questions-2026.03-demo"
    }
  ]
}
```

## JSON, который backend отправляет в модуль анализа

`POST /assessment/v1/report`

```json
{
  "request_id": "req-1001",
  "session_id": "session-1001",
  "client_id": "main-backend",
  "mode": "sync",
  "scenario": {
    "scenario_id": "backend_junior_session",
    "specialization": "backend",
    "grade": "junior",
    "topics": ["http_api", "sql_performance", "distributed_systems"],
    "report_language": "ru"
  },
  "items": [
    {
      "item_id": "item-1",
      "question_id": "backend_junior_rest_methods",
      "question_text": "Чем отличаются методы GET, POST, PUT и DELETE в REST API?",
      "answer_text": "GET читает ресурс и не должен менять состояние. POST обычно создает ресурс. PUT заменяет ресурс целиком и является идемпотентным. DELETE удаляет ресурс.",
      "asked_at": "2026-03-17T10:00:00Z",
      "tags": ["http", "rest", "crud"]
    },
    {
      "item_id": "item-2",
      "question_id": "backend_junior_sql_index",
      "question_text": "Что такое индекс в SQL-базе данных и когда он помогает?",
      "answer_text": "Индекс ускоряет поиск по WHERE и JOIN, но занимает место и замедляет запись.",
      "asked_at": "2026-03-17T10:02:00Z",
      "tags": ["sql", "index", "performance"]
    }
  ],
  "metadata": {
    "source": "main-backend",
    "subscription_plan": "start"
  }
}
```

## JSON, который модуль возвращает backend

Пример ответа для `mode = sync`:

```json
{
  "status": "ready",
  "job": {
    "status": "ready",
    "job_id": "6e1a3ade-6691-44a6-9c0b-87ace1a083f5",
    "request_id": "req-1001",
    "session_id": "session-1001",
    "created_at": "2026-03-17T10:05:21+00:00",
    "updated_at": "2026-03-17T10:05:34+00:00",
    "error_code": null,
    "error_message": null
  },
  "report": {
    "request_id": "req-1001",
    "session_id": "session-1001",
    "client_id": "main-backend",
    "specialization": "backend",
    "grade": "junior",
    "overall_score": 74,
    "criterion_scores": {
      "correctness": 78,
      "completeness": 72,
      "clarity": 75,
      "practicality": 70,
      "terminology": 73
    },
    "summary": "Сессия показывает уверенное понимание базовых тем backend junior. Основной резерв улучшения связан с полнотой и практической детализацией ответов.",
    "questions": [
      {
        "item_id": "item-1",
        "question_id": "backend_junior_rest_methods",
        "question_text": "Чем отличаются методы GET, POST, PUT и DELETE в REST API?",
        "topic": "HTTP API и REST-подход",
        "score": 80,
        "criterion_scores": {
          "correctness": 84,
          "completeness": 78,
          "clarity": 82,
          "practicality": 75,
          "terminology": 78
        },
        "summary": "Ответ в целом корректно различает основные HTTP-методы и их назначение.",
        "strengths": [
          "Корректно описана семантика GET и POST.",
          "Упомянута идемпотентность PUT."
        ],
        "issues": [
          "Не раскрыто, почему GET считается safe-методом."
        ],
        "covered_keypoints": [
          "GET используется для чтения ресурса.",
          "PUT должен быть идемпотентным."
        ],
        "missing_keypoints": [
          "Не раскрыта safe-семантика GET."
        ],
        "detected_mistakes": [],
        "recommendations": [
          "Добавить объяснение safe- и idempotent-семантики HTTP-методов."
        ],
        "context_snippets": [
          {
            "chunk_id": "kb_backend_http_1",
            "source_title": "REST semantics notes",
            "source_url": "https://example.local/kb/rest-semantics",
            "excerpt": "GET запрашивает представление ресурса и по спецификации считается safe-методом...",
            "score": 0.62
          }
        ]
      }
    ],
    "topics": [
      {
        "topic": "HTTP API и REST-подход",
        "average_score": 80,
        "strengths": ["Базовая семантика HTTP-методов раскрыта верно."],
        "gaps": ["Не хватает объяснения safe/idempotent-свойств."]
      }
    ],
    "recommendations": [
      "Усилить ответы практическими примерами и деталями по протоколу HTTP."
    ],
    "versions": {
      "model_version": "qwen2.5:3b",
      "rubric_version": "rubrics-2026.03-demo",
      "kb_version": "kb-2026.03-demo",
      "questions_version": "questions-2026.03-demo",
      "prompt_version": "ollama-json-ru-v4"
    },
    "generated_at": "2026-03-17T10:05:34+00:00"
  }
}
```

## Асинхронный режим

Если отправить `"mode": "async"`, сервис сначала вернёт только статус задачи, а готовый отчёт можно забрать позже:
- `GET /assessment/v1/report/{job_id}/status`
- `GET /assessment/v1/report/{job_id}`

## OpenAPI для backend

1. склонировать репозиторий;
2. запустить `start.bat`;
3. открыть `http://127.0.0.1:8000/docs`;
4. подключиться к endpoint `GET /assessment/v1/questions` и `POST /assessment/v1/report`.

Контракт целиком доступен по адресу `http://127.0.0.1:8000/openapi.json`.
