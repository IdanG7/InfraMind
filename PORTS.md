# InfraMind - Port Reference Guide

Quick reference for all service ports in InfraMind.

## Default Ports (Local Development)

### External Ports (Host Machine)

These are the ports you use to access services from your browser or localhost:

| Service | Port | URL | Credentials |
|---------|------|-----|-------------|
| **API** | 8081 | http://localhost:8081 | API Key required |
| **API Docs** | 8081 | http://localhost:8081/docs | - |
| **Grafana** | 3001 | http://localhost:3001 | admin / admin |
| **Prometheus** | 9091 | http://localhost:9091 | - |
| **PostgreSQL** | 5433 | localhost:5433 | inframind / inframind_dev |
| **Redis** | 6380 | localhost:6380 | - |
| **MinIO API** | 9000 | http://localhost:9000 | minioadmin / minioadmin |
| **MinIO Console** | 9001 | http://localhost:9001 | minioadmin / minioadmin |

### Internal Ports (Container Network)

These are the ports used for container-to-container communication:

| Service | Internal Port | Used By |
|---------|--------------|---------|
| API | 8080 | Containers, K8s |
| PostgreSQL | 5432 | API container |
| Redis | 6379 | API container |
| Prometheus | 9090 | Grafana container |
| Grafana | 3000 | - |
| MinIO | 9000 | API container |

## Customizing Ports

### Using .env File

All ports can be customized via environment variables:

```bash
# Copy the example
cp .env.example .env

# Edit .env and set your preferred ports
API_PORT=8081
GRAFANA_PORT=3001
PROMETHEUS_PORT=9091
POSTGRES_PORT=5433
REDIS_PORT=6380
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
```

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | 8081 | FastAPI external port |
| `API_HOST` | 0.0.0.0 | API bind address |
| `POSTGRES_PORT` | 5433 | PostgreSQL external port |
| `REDIS_PORT` | 6380 | Redis external port |
| `PROMETHEUS_PORT` | 9091 | Prometheus external port |
| `GRAFANA_PORT` | 3001 | Grafana external port |
| `MINIO_PORT` | 9000 | MinIO API external port |
| `MINIO_CONSOLE_PORT` | 9001 | MinIO Console port |

## Common Port Conflicts

### If Ports Are Already in Use

If you see errors like:
```
Bind for 0.0.0.0:8081 failed: port is already allocated
```

**Solution 1: Use .env file**
```bash
cp .env.example .env
# Edit .env and change the conflicting port
API_PORT=8082  # Change to any available port
```

**Solution 2: Stop conflicting services**
```bash
# Find what's using the port (macOS/Linux)
lsof -i :8081
kill <PID>

# Or use docker
docker ps
docker stop <container-name>
```

### Default Port Changes from Standard

InfraMind uses non-standard ports by default to avoid common conflicts:

| Service | Standard Port | InfraMind Default | Reason |
|---------|--------------|-------------------|---------|
| API | 8080 | 8081 | Avoid common dev servers |
| PostgreSQL | 5432 | 5433 | Avoid local Postgres |
| Redis | 6379 | 6380 | Avoid local Redis |
| Prometheus | 9090 | 9091 | Avoid local Prometheus |
| Grafana | 3000 | 3001 | Avoid Node.js/Rails apps |

## Kubernetes Ports

In Kubernetes, services use standard internal ports:

```yaml
# API Service
port: 8080
targetPort: 8080

# PostgreSQL
port: 5432

# Redis
port: 6379
```

Access via internal DNS:
```
http://inframind-api.infra.svc.cluster.local:8080
```

## Docker Compose Port Mapping

Port mapping format: `"<external>:<internal>"`

```yaml
services:
  api:
    ports:
      - "${API_PORT:-8081}:8080"
    # External: 8081 (customizable)
    # Internal: 8080 (fixed)

  postgres:
    ports:
      - "${POSTGRES_PORT:-5433}:5432"
    # External: 5433 (customizable)
    # Internal: 5432 (fixed)
```

## Connection Strings

### From Host Machine

```bash
# API
curl http://localhost:8081/healthz

# PostgreSQL
psql -h localhost -p 5433 -U inframind -d inframind

# Redis
redis-cli -h localhost -p 6380

# MinIO
mc alias set local http://localhost:9000 minioadmin minioadmin
```

### From Within Docker Compose

```bash
# API (from another container)
DATABASE_URL=postgresql://inframind:inframind_dev@postgres:5432/inframind
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
```

### From Kubernetes

```bash
DATABASE_URL=postgresql://user:pass@postgres-service.infra.svc.cluster.local:5432/db
REDIS_URL=redis://redis-service.infra.svc.cluster.local:6379/0
API_URL=http://inframind-api.infra.svc.cluster.local:8080
```

## Firewall Rules (Production)

### Recommended Firewall Configuration

```bash
# Allow only necessary ports
# API (from load balancer only)
ufw allow from <LB-IP> to any port 8080

# PostgreSQL (internal only)
ufw deny 5432

# Redis (internal only)
ufw deny 6379

# Prometheus (internal + VPN)
ufw allow from <VPN-CIDR> to any port 9090

# Grafana (load balancer)
ufw allow from <LB-IP> to any port 3000
```

## Health Check Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| API | http://localhost:8081/healthz | `{"status":"ok"}` |
| API | http://localhost:8081/readyz | `{"status":"ready"}` |
| Prometheus | http://localhost:9091/-/healthy | `Prometheus is Healthy` |
| Grafana | http://localhost:3001/api/health | `{"database":"ok"}` |
| PostgreSQL | `pg_isready -h localhost -p 5433` | `accepting connections` |
| Redis | `redis-cli -h localhost -p 6380 ping` | `PONG` |
| MinIO | http://localhost:9000/minio/health/live | 200 OK |

## Troubleshooting

### Check If Port Is Available

```bash
# macOS/Linux
lsof -i :<port>
netstat -an | grep <port>

# Check if listening
nc -zv localhost <port>
```

### View Docker Port Mappings

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### Test Connectivity

```bash
# API
curl -v http://localhost:8081/healthz

# PostgreSQL
nc -zv localhost 5433

# Redis
redis-cli -h localhost -p 6380 ping

# MinIO
curl -v http://localhost:9000/minio/health/live
```

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│ InfraMind Port Quick Reference              │
├─────────────────────────────────────────────┤
│ 🌐 API:        http://localhost:8081       │
│ 📊 Grafana:    http://localhost:3001       │
│ 📈 Prometheus: http://localhost:9091       │
│ 🗄️  PostgreSQL: localhost:5433             │
│ 🔴 Redis:      localhost:6380              │
│ 📦 MinIO:      http://localhost:9000       │
│ 🎛️  Console:    http://localhost:9001       │
├─────────────────────────────────────────────┤
│ Customize: cp .env.example .env            │
│ Docs: http://localhost:8081/docs          │
└─────────────────────────────────────────────┘
```

---

**Last Updated**: October 25, 2025
**Version**: 0.1.0
