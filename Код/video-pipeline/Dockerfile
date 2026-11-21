# Video Pipeline — Distributed Media Processing (Go)

Реализация архитектуры из диаграммы: загрузка видео, транскодинг в HLS,
доставка статусов клиенту в реальном времени через WebSocket.

## Сервисы

| Сервис               | Роль                                                                 |
|-----------------------|-----------------------------------------------------------------------|
| `api-gateway`          | Шаги 1-4: принимает `POST /videos`, кладёт оригинал в MinIO, пишет `videos` (status=PENDING) и outbox-событие в Postgres **в одной транзакции** |
| `outbox-relay`         | Читает неотправленные outbox-события и публикует их в Kafka topic `video-tasks` (Transactional Outbox pattern) |
| `transcoder-worker`    | Шаги 5-6: consumer группа на `video-tasks`, пул воркеров (goroutines), ffmpeg → HLS-рендиции (1080p/720p/480p) + thumbnail, аплоад в MinIO, публикация прогресса в `video-status` |
| `notification-ws`      | Шаг 7: consumer на `video-status`, WebSocket hub, push клиенту        |

## Почему Transactional Outbox

Если бы `api-gateway` писал в Postgres и сразу публиковал в Kafka, при падении
между этими двумя операциями сообщение потерялось бы навсегда (или наоборот —
дубль). Outbox-паттерн пишет событие в ту же транзакцию, что и бизнес-строку,
а отдельный relay-процесс с ретраями гарантированно доставляет его в Kafka
(at-least-once).

## Структура проекта

```
cmd/
  api-gateway/main.go        точка входа HTTP API
  outbox-relay/main.go       точка входа relay-процесса
  transcoder-worker/main.go  точка входа воркер-пула
  notification-ws/main.go    точка входа WS-сервиса
internal/
  config/     env-конфигурация
  models/     общие доменные типы (Video, OutboxEvent, Kafka-события)
  storage/    обёртки Postgres (pgx) и MinIO (minio-go)
  kafka/      обёртки Producer/Consumer (segmentio/kafka-go)
  outbox/     relay-цикл (poll -> publish -> mark sent)
  api/        HTTP-хендлеры и роутер (chi)
  worker/     пул воркеров + сама ffmpeg-транскодинг логика
  ws/         WebSocket hub
migrations/   SQL-схема (videos, outbox_events)
build/        общий Dockerfile для всех 4 сервисов
docker-compose.yml   Postgres + Kafka + Zookeeper + MinIO + все сервисы
```

## Запуск локально

Требуется установленный Docker (Postgres/Kafka/MinIO поднимаются в контейнерах),
Go 1.22+ и `ffmpeg` в PATH, если запускаете `transcoder-worker` не в Docker.

```bash
cp .env.example .env   # при необходимости поправьте переменные
go mod tidy             # подтянуть зависимости в go.sum

# поднять инфраструктуру + все 4 сервиса
make up

# либо запускать сервисы по отдельности локально (Postgres/Kafka/MinIO — в докере):
docker compose up postgres kafka zookeeper minio -d
make run-api
make run-relay
make run-worker
make run-ws
```

## Пример использования

```bash
# Загрузка видео
curl -X POST http://localhost:8080/videos -F "file=@sample.mp4"
# -> {"id": "<uuid>", "status": "PENDING"}

# Опрос статуса (или подписка через WS ниже)
curl http://localhost:8080/videos/<uuid>

# Подписка на прогресс в реальном времени
wscat -c "ws://localhost:8081/ws?video_id=<uuid>"
```

## Масштабирование

- `transcoder-worker` горизонтально масштабируется — несколько инстансов в
  одной Kafka consumer group автоматически разделят партиции `video-tasks`
  (в docker-compose уже `replicas: 2`).
- Внутри каждого инстанса дополнительный параллелизм даёт `worker.Pool`
  (`TRANSCODER_WORKERS` в `.env`).
- `notification-ws` можно масштабировать за балансировщиком с sticky-сессиями
  по WebSocket, либо добавить Redis pub/sub для fan-out между инстансами
  (в текущем скелете hub — in-memory, в пределах одного процесса).

## Что дальше (не реализовано в скелете)

- Аутентификация/авторизация на `api-gateway`
- Ретраи/DLQ для "зависших" сообщений Kafka
- Идемпотентность транскодинга при повторной обработке одного task
- Метрики (Prometheus) и трейсинг (OpenTelemetry)
- Presigned upload напрямую в MinIO вместо proxy через api-gateway для больших файлов
