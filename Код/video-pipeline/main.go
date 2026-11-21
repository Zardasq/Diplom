# Multi-stage Dockerfile shared by all four services.
# Build with: docker build --build-arg SERVICE=api-gateway -t api-gateway .
FROM golang:1.22-alpine AS build
ARG SERVICE
WORKDIR /src
COPY go.mod ./
RUN go mod download || true
COPY . .
RUN CGO_ENABLED=0 go build -o /out/service ./cmd/${SERVICE}

FROM alpine:3.19
RUN apk add --no-cache ffmpeg ca-certificates
COPY --from=build /out/service /usr/local/bin/service
ENTRYPOINT ["/usr/local/bin/service"]
