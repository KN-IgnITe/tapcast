# Setup

### General Prerequisites
Regardless of your team, you will need the following installed:
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Make](https://www.gnu.org/software/make/)
- [Buf] (https://docs.buf.build/installation) (for Protobuf code generation)
- [Lefthook](https://github.com/evilmartians/lefthook) (e.g., `brew install lefthook` or `npm install -g @evilmartians/lefthook`)

To initialize your local environment variables, run:
```bash
make init-env
```
This will create a `.env` file from a template. Make sure to populate it with the required values.

---

### 🌐 Frontend Team
**Prerequisites:** [Node.js](https://nodejs.org/) and npm.

**Setup:**
```bash
cd frontend && npm ci
cd ..
lefthook install
```

**Running Locally:**
To start the necessary backend services in Docker and run the frontend in development mode:
```bash
make dev-frontend
```

---

### ⚙️ Backend Team
**Prerequisites:** [Go](https://golang.org/doc/install) (1.21+).

**Setup:**
Install the required Go tools and Lefthook hooks:
```bash
go install golang.org/x/tools/cmd/goimports@latest
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
lefthook install
```

**Running Locally:**
To start the necessary dependencies (Postgres, RabbitMQ, S3, Inference) in Docker and run the backend locally:
```bash
make dev-backend
```

---

### 🧠 ML Team (Inference & Training)
**Prerequisites:** Python 3.x and [Poetry](https://python-poetry.org/docs/#installation).

**Setup:**
Install dependencies for both ML services:
```bash
cd inference && poetry install
cd ../training && poetry install
cd ..
lefthook install
```

**Running Locally:**
- **Inference:** Starts Postgres & S3 in Docker, runs Inference locally.
  ```bash
  make dev-inference
  ```
- **Training:** Starts Postgres, RabbitMQ & S3 in Docker, runs Training locally.
  ```bash
  make dev-training
  ```

---

### 🚀 Running & Testing Everything
If you want to spin up the entire stack (Frontend, Backend, Inference, Training, and databases) inside Docker:

```bash
# Generate Protobuf code for backend and inference services
make proto

# Build and start all services
make build

# Or if images are already built
make up
```

To view logs for all running Docker containers:
```bash
make logs
```

To tear down the environment and remove volumes:
```bash
make down
```
