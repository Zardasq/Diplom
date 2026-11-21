package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/google/uuid"

	"video-pipeline/internal/models"
	"video-pipeline/internal/storage"
)

type Handler struct {
	PG           *storage.Postgres
	MinIO        *storage.MinIO
	TopicTasks   string
}

func NewHandler(pg *storage.Postgres, minio *storage.MinIO, topicTasks string) *Handler {
	return &Handler{PG: pg, MinIO: minio, TopicTasks: topicTasks}
}

// UploadVideo handles POST /videos.
// Flow (matches the architecture diagram):
//  1. Accept multipart upload
//  2. Store the original file in MinIO/S3
//  3. Write a `videos` row with status=PENDING
//  4. In the SAME DB transaction, write an outbox event -> the relay
//     process later publishes it to Kafka topic "video-tasks"
func (h *Handler) UploadVideo(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	if err := r.ParseMultipartForm(1 << 30); err != nil { // up to 1GiB in memory threshold
		httpError(w, http.StatusBadRequest, fmt.Errorf("parse multipart form: %w", err))
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		httpError(w, http.StatusBadRequest, fmt.Errorf("missing file field: %w", err))
		return
	}
	defer file.Close()

	videoID := uuid.NewString()
	originalKey := fmt.Sprintf("originals/%s/%s", videoID, header.Filename)

	// 2. Store original in object storage.
	if err := h.MinIO.Upload(ctx, originalKey, file, header.Size, header.Header.Get("Content-Type")); err != nil {
		httpError(w, http.StatusInternalServerError, fmt.Errorf("upload to minio: %w", err))
		return
	}

	video := &models.Video{
		ID:          videoID,
		OriginalKey: originalKey,
		Status:      models.StatusPending,
	}

	task := models.VideoTaskEvent{
		VideoID:     videoID,
		OriginalKey: originalKey,
	}

	// 3 + 4. Atomic write of business row + outbox event.
	if err := h.PG.CreateVideoWithOutbox(ctx, video, h.TopicTasks, models.EventTypeVideoTaskCreated, task); err != nil {
		httpError(w, http.StatusInternalServerError, fmt.Errorf("persist video + outbox: %w", err))
		return
	}

	respondJSON(w, http.StatusAccepted, map[string]any{
		"id":     videoID,
		"status": models.StatusPending,
	})
}

// GetVideo handles GET /videos/{id} for polling status (in addition to the
// WebSocket push channel).
func (h *Handler) GetVideo(w http.ResponseWriter, r *http.Request, id string) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	video, err := h.PG.GetVideo(ctx, id)
	if err != nil {
		httpError(w, http.StatusNotFound, fmt.Errorf("video not found: %w", err))
		return
	}
	respondJSON(w, http.StatusOK, video)
}

func respondJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func httpError(w http.ResponseWriter, status int, err error) {
	respondJSON(w, status, map[string]string{"error": err.Error()})
}
