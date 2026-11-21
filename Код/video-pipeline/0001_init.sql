// Package config centralizes environment-based configuration for all services
// (api-gateway, outbox-relay, transcoder-worker, notification-ws).
package config

import (
	"os"
	"strconv"
	"strings"
)

type Config struct {
	PostgresDSN string

	KafkaBrokers     []string
	TopicVideoTasks  string
	TopicVideoStatus string

	MinIOEndpoint  string
	MinIOAccessKey string
	MinIOSecretKey string
	MinIOBucket    string
	MinIOUseSSL    bool

	APIHTTPPort string
	WSHTTPPort  string

	OutboxPollIntervalMs int
	OutboxBatchSize      int

	TranscoderWorkers int
	FFmpegBin         string
}

// Load reads configuration from environment variables, falling back to
// sane local-development defaults (matching docker-compose.yml).
func Load() *Config {
	return &Config{
		PostgresDSN: getEnv("POSTGRES_DSN", "postgres://postgres:postgres@localhost:5432/videos?sslmode=disable"),

		KafkaBrokers:     strings.Split(getEnv("KAFKA_BROKERS", "localhost:9092"), ","),
		TopicVideoTasks:  getEnv("TOPIC_VIDEO_TASKS", "video-tasks"),
		TopicVideoStatus: getEnv("TOPIC_VIDEO_STATUS", "video-status"),

		MinIOEndpoint:  getEnv("MINIO_ENDPOINT", "localhost:9000"),
		MinIOAccessKey: getEnv("MINIO_ACCESS_KEY", "minioadmin"),
		MinIOSecretKey: getEnv("MINIO_SECRET_KEY", "minioadmin"),
		MinIOBucket:    getEnv("MINIO_BUCKET", "videos"),
		MinIOUseSSL:    getEnvBool("MINIO_USE_SSL", false),

		APIHTTPPort: getEnv("API_HTTP_PORT", "8080"),
		WSHTTPPort:  getEnv("WS_HTTP_PORT", "8081"),

		OutboxPollIntervalMs: getEnvInt("OUTBOX_POLL_INTERVAL_MS", 500),
		OutboxBatchSize:      getEnvInt("OUTBOX_BATCH_SIZE", 50),

		TranscoderWorkers: getEnvInt("TRANSCODER_WORKERS", 4),
		FFmpegBin:         getEnv("FFMPEG_BIN", "ffmpeg"),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return fallback
}

func getEnvBool(key string, fallback bool) bool {
	if v := os.Getenv(key); v != "" {
		if b, err := strconv.ParseBool(v); err == nil {
			return b
		}
	}
	return fallback
}
