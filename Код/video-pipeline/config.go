// Command outbox-relay polls Postgres for unsent outbox events and
// publishes them to Kafka, completing the Transactional Outbox pattern
// started by api-gateway.
package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"video-pipeline/internal/config"
	"video-pipeline/internal/kafka"
	"video-pipeline/internal/outbox"
	"video-pipeline/internal/storage"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	cfg := config.Load()

	pg, err := storage.NewPostgres(ctx, cfg.PostgresDSN)
	if err != nil {
		slog.Error("failed to connect to postgres", "err", err)
		os.Exit(1)
	}
	defer pg.Close()

	tasksProducer := kafka.NewProducer(cfg.KafkaBrokers, cfg.TopicVideoTasks)
	defer tasksProducer.Close()

	// Map topic name -> producer. As more event types/topics are added,
	// register additional producers here.
	producers := map[string]*kafka.Producer{
		cfg.TopicVideoTasks: tasksProducer,
	}

	relay := outbox.NewRelay(pg, producers, cfg.OutboxPollIntervalMs, cfg.OutboxBatchSize)

	slog.Info("outbox-relay started", "poll_interval_ms", cfg.OutboxPollIntervalMs)
	relay.Run(ctx) // blocks until ctx cancelled
	slog.Info("outbox-relay stopped")
}
