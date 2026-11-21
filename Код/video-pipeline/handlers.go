// Command notification-ws implements step 7: consume "video-status" from
// Kafka and push updates to clients over WebSocket.
package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"video-pipeline/internal/config"
	"video-pipeline/internal/kafka"
	"video-pipeline/internal/ws"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	cfg := config.Load()

	hub := ws.NewHub()

	consumer := kafka.NewConsumer(cfg.KafkaBrokers, cfg.TopicVideoStatus, "notification-ws-group")
	defer consumer.Close()

	go func() {
		if err := consumer.Run(ctx, hub.HandleStatusEvent); err != nil {
			slog.Error("status consumer loop exited with error", "err", err)
		}
	}()

	mux := http.NewServeMux()
	mux.HandleFunc("/ws", hub.ServeWS)
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	srv := &http.Server{
		Addr:    ":" + cfg.WSHTTPPort,
		Handler: mux,
	}

	go func() {
		slog.Info("notification-ws listening", "port", cfg.WSHTTPPort)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Error("http server error", "err", err)
			os.Exit(1)
		}
	}()

	<-ctx.Done()
	slog.Info("shutting down notification-ws")
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(shutdownCtx)
}
