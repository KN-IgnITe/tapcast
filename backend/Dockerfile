FROM golang:alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /api ./cmd/api

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /api .
EXPOSE 8080
CMD ["./api"]
