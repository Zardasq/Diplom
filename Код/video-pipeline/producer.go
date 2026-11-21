// Command transcoder-worker implements steps 5-6: consume "video-tasks"
// from Kafka, run ffmpeg to produce HLS renditions + thumbnail, upload
// results to MinIO, and publish progress to "video-status".
package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"video-pipeline/internal/config"
	"video-pipeline/internal/kafka"
	"video-pipeline/internal/models"
	"video-pipeline/internal/storage"
	"video-pipeline/internal/worker"
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

	minioClient, err := storage.NewMinIO(ctx, cfg.MinIOEndpoint, cfg.MinIOAccessKey, cfg.MinIOSecretKey, cfg.MinIOBucket, cfg.MinIOUseSSL)
	if err != nil {
		slog.Error("failed to connect to minio", "err", err)
		os.Exit(1)
	}

	statusProducer := kafka.NewProducer(cfg.KafkaBrokers, cfg.TopicVideoStatus)
	defer statusProducer.Close()

	transcoder := worker.NewTranscoder(minioClient, statusProducer, pg, cfg.FFmpegBin)
	pool := worker.NewPool(cfg.TranscoderWorkers, cfg.TranscoderWorkers*2, transcoder.Process)

	consumer := kafka.NewConsumer(cfg.KafkaBrokers, cfg.TopicVideoTasks, "transcoder-worker-group")
	defer consumer.Close()

	// Run the worker pool and the Kafka consumer loop concurrently.
	go pool.Start(ctx)

	slog.Info("transcoder-worker started", "workers", cfg.TranscoderWorkers)
	err = consumer.Run(ctx, func(ctx context.Context, key, value []byte) error {
		task, err := kafka.Unmarshal[models.VideoTaskEvent](value)
		if err != nil {
			return err
		}
		pool.Submit(worker.Job{Task: task})
		return nil
	})
	if err != nil {
		slog.Error("consumer loop exited with error", "err", err)
	}

	pool.Close()
	slog.Info("transcoder-worker stopped")
}
