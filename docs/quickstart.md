# Quick Start Guide

Get InfraMind running locally in under 5 minutes!

## Prerequisites

- Docker & Docker Compose
- 8GB RAM minimum
- macOS, Linux, or WSL2

## Local Demo

### 1. Clone and Start

```bash
git clone https://github.com/yourorg/inframind.git
cd inframind

# Start all services
make up

# Wait ~30 seconds for services to initialize
docker-compose ps
```

### 2. Seed Demo Data

```bash
# Generate 50 synthetic build runs and train initial model
make seed-demo
```

This will:
- Create a demo pipeline `demo/example-app`
- Generate 50 build runs with varying configurations
- Train an ML model on the synthetic data
- Take ~2 minutes to complete

### 3. Explore

Open the following in your browser:

- **API Documentation**: http://localhost:8080/docs
- **Grafana Dashboards**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### 4. Test Optimization

```bash
# Request optimization suggestions
curl -X POST http://localhost:8080/optimize \
  -H "Content-Type: application/json" \
  -H "X-IM-Token: dev-key-change-in-production" \
  -d '{
    "pipeline": "demo/example-app",
    "context": {
      "tool": "cmake",
      "repo": "demo/example-app",
      "max_rss_gb": 4,
      "num_steps": 5,
      "avg_step_duration_s": 60
    }
  }'
```

Expected response:
```json
{
  "suggestions": {
    "concurrency": 6,
    "cpu_req": 6,
    "mem_req_gb": 8,
    "cache": {
      "ccache": true,
      "size_gb": 10
    }
  },
  "rationale": "Selected config with predicted duration=420.5s...",
  "confidence": 0.7
}
```

## Next Steps

1. **Grafana**: Explore the "Pipelines Overview" dashboard
2. **API**: Try other endpoints at http://localhost:8080/docs
3. **Jenkins**: See [Jenkins Integration](./architecture.md#jenkins-integration)
4. **Production**: See [Deployment Guide](./architecture.md#kubernetes-deployment)

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs -f api

# Reset everything
make down
docker volume prune
make up
```

### Demo seed fails

```bash
# Check database
docker-compose exec postgres psql -U inframind -d inframind -c '\dt'

# Restart API
docker-compose restart api
```

### Port conflicts

Edit `docker-compose.yml` to change port mappings if 8080, 3000, 5432, etc. are already in use.

## Cleanup

```bash
# Stop services
make down

# Remove volumes (deletes data)
docker-compose down -v
```
