.PHONY: tidy build run-api run-relay run-worker run-ws up down

tidy:
	go mod tidy

build:
	go build ./...

run-api:
	go run ./cmd/api-gateway

run-relay:
	go run ./cmd/outbox-relay

run-worker:
	go run ./cmd/transcoder-worker

run-ws:
	go run ./cmd/notification-ws

up:
	docker compose up --build

down:
	docker compose down -v
