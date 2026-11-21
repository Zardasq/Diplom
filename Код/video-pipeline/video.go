version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: videos
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 10

  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 5s
      retries: 10

  api-gateway:
    build:
      context: .
      dockerfile: build/Dockerfile
      args:
        SERVICE: api-gateway
    env_file: .env.example
    environment:
      POSTGRES_DSN: postgres://postgres:postgres@postgres:5432/videos?sslmode=disable
      KAFKA_BROKERS: kafka:29092
      MINIO_ENDPOINT: minio:9000
    ports:
      - "8080:8080"
    depends_on:
      - postgres
      - kafka
      - minio

  outbox-relay:
    build:
      context: .
      dockerfile: build/Dockerfile
      args:
        SERVICE: outbox-relay
    env_file: .env.example
    environment:
      POSTGRES_DSN: postgres://postgres:postgres@postgres:5432/videos?sslmode=disable
      KAFKA_BROKERS: kafka:29092
    depends_on:
      - postgres
      - kafka

  transcoder-worker:
    build:
      context: .
      dockerfile: build/Dockerfile
      args:
        SERVICE: transcoder-worker
    env_file: .env.example
    environment:
      POSTGRES_DSN: postgres://postgres:postgres@postgres:5432/videos?sslmode=disable
      KAFKA_BROKERS: kafka:29092
      MINIO_ENDPOINT: minio:9000
    depends_on:
      - postgres
      - kafka
      - minio
    deploy:
      replicas: 2 # scale the worker pool horizontally

  notification-ws:
    build:
      context: .
      dockerfile: build/Dockerfile
      args:
        SERVICE: notification-ws
    env_file: .env.example
    environment:
      KAFKA_BROKERS: kafka:29092
    ports:
      - "8081:8081"
    depends_on:
      - kafka

volumes:
  pgdata:
  miniodata:
