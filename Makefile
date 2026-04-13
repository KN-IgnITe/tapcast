-include .env
export

.PHONY: init-hooks init-env up down build logs proto deps-frontend deps-backend deps-inference deps-training dev-frontend dev-backend dev-inference dev-training backend-local inference-local training-local frontend-local clean docs

init-hooks:
	@echo "Bootstrapping Go tools..."
	go install golang.org/x/tools/cmd/goimports@latest
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	@echo "Bootstrapping Python (Inference)..."
	cd inference && poetry install
	@echo "Bootstrapping Python (Training)..."
	cd training && poetry install
	@echo "Bootstrapping Node (Frontend)..."
	cd frontend && npm ci
	@echo "Bootstrapping Prettier (Documentation)..."
	npm install --save-dev prettier
	@echo "Initializing Git Hooks..."
	lefthook install

#init-env:
#	@if [ ! -f .env ]; then cp .env.example .env; echo "Error: .env file missing. Created template. Populate variables and rerun."; exit 1; fi

init-env:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Pomyślnie utworzono plik .env z szablonu. Uzupełnij zmienne!"; fi

up: init-env
	docker compose up -d

down:
	docker compose down -v

build: init-env
	docker compose up --build -d

logs:
	docker compose logs -f

proto:
	cd proto && buf generate

deps-frontend: init-env
	docker compose up -d postgres rabbitmq s3 inference backend

deps-backend: init-env
	docker compose up -d postgres rabbitmq s3 inference

deps-inference: init-env
	docker compose up -d postgres s3

deps-training: init-env
	docker compose up -d postgres rabbitmq s3

dev-frontend: deps-frontend
	$(MAKE) frontend-local

dev-backend: deps-backend
	$(MAKE) backend-local

dev-inference: deps-inference
	$(MAKE) inference-local

dev-training: deps-training
	$(MAKE) training-local

backend-local: init-env
	cd backend && go run ./cmd/api/main.go

inference-local: init-env
	cd inference && poetry install && poetry run python -m inference.main

training-local: init-env
	cd training && poetry install && poetry run python -m training.main

frontend-local: init-env
	cd frontend && npm run dev

clean: down
	rm -rf backend/pkg/pb
	find inference/src/inference/pb -type f ! -name '__init__.py' -delete

docs:
	docker compose --profile docs up mkdocs