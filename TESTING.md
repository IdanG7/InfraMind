# InfraMind Testing Guide

This guide shows you how to test all components of InfraMind locally.

## 🚀 Quick Test (5 minutes)

### 1. Start All Services

```bash
# Clone the repo (if not already)
cd infraread

# Start with Docker Compose
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
docker-compose ps
```

You should see all services running:
```
NAME                    STATUS              PORTS
inframind-api           Up                  0.0.0.0:8081->8080/tcp
inframind-postgres      Up (healthy)        0.0.0.0:5433->5432/tcp
inframind-redis         Up (healthy)        0.0.0.0:6380->6379/tcp
inframind-minio         Up                  0.0.0.0:9000-9001->9000-9001/tcp
inframind-prometheus    Up                  0.0.0.0:9092->9090/tcp
inframind-grafana       Up                  0.0.0.0:3001->3000/tcp
```

### 2. Check Service Health

```bash
# Check API health
curl http://localhost:8081/health

# Expected response:
# {"status":"healthy","version":"0.1.0","timestamp":"..."}
```

### 3. View API Documentation

Open in your browser:
```
http://localhost:8081/docs
```

You should see the interactive Swagger UI with all API endpoints.

### 4. Test Basic Optimization Request

```bash
# Request optimization suggestions
curl -X POST http://localhost:8081/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "myorg/myrepo",
    "branch": "main",
    "build_type": "release"
  }'
```

**Expected Response:**
```json
{
  "cpu": 4,
  "memory": 8192,
  "concurrency": 4,
  "cache_enabled": true,
  "estimated_duration": 300,
  "confidence": 0.75,
  "rationale": "Default configuration for new repository"
}
```

### 5. View Grafana Dashboards

Open in your browser:
```
http://localhost:3001
```

**Login:**
- Username: `admin`
- Password: `admin`

Navigate to Dashboards and you should see InfraMind dashboards.

---

## 🧪 Comprehensive Testing

### Test 1: API Endpoints

```bash
# 1. Health check
curl http://localhost:8081/health

# 2. Get optimization suggestions
curl -X POST http://localhost:8081/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "test/repo",
    "branch": "main",
    "build_type": "release",
    "previous_duration": 300
  }'

# 3. Report build results
curl -X POST http://localhost:8081/builds/complete \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "test/repo",
    "branch": "main",
    "duration": 245,
    "status": "success",
    "cpu": 4,
    "memory": 8192,
    "concurrency": 4
  }'

# 4. Get metrics
curl http://localhost:8081/metrics

# 5. Check OpenAPI spec
curl http://localhost:8081/openapi.json
```

### Test 2: Generate Demo Data

```bash
# Generate sample build data for testing
docker-compose exec api python app/scripts/generate_demo_data.py

# This will create:
# - 500 sample builds
# - Various repositories and branches
# - Different build types
# - Training data for ML model
```

**Expected Output:**
```
Generating demo data...
Created 500 builds
Trained ML model
Demo data generation complete!
```

### Test 3: Test CLI Tool

```bash
# Install the CLI tool
cd cli
pip install -e .

# Test health check
inframind health

# Test optimization
inframind optimize \
  --repo myorg/myrepo \
  --branch main \
  --format human

# Test with JSON output
inframind optimize \
  --repo myorg/myrepo \
  --branch main \
  --format json

# Test environment variable output
inframind optimize \
  --repo myorg/myrepo \
  --branch main \
  --format env

# Test reporting
inframind report \
  --repo myorg/myrepo \
  --branch main \
  --duration 180 \
  --status success \
  --cpu 8 \
  --memory 16384
```

### Test 4: Database Connection

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U inframind

# Run some queries
\dt                          # List tables
SELECT COUNT(*) FROM builds; # Count builds
SELECT * FROM builds LIMIT 5; # View sample builds
\q                           # Quit
```

### Test 5: Redis Cache

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Test commands
PING                         # Should return PONG
KEYS *                       # List all keys
GET some_key                 # Get a value
quit                         # Exit
```

### Test 6: MinIO Object Storage

Open in your browser:
```
http://localhost:9001
```

**Login:**
- Access Key: `minioadmin`
- Secret Key: `minioadmin`

You should see the MinIO console. Check if the `inframind-logs` bucket exists.

### Test 7: Prometheus Metrics

Open in your browser:
```
http://localhost:9092
```

**Test queries:**
```promql
# API request rate
rate(http_requests_total[5m])

# API response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])
```

### Test 8: Grafana Dashboards

1. Open http://localhost:3001
2. Login (admin/admin)
3. Go to Dashboards
4. Check the following dashboards exist:
   - Pipeline Performance
   - ML Model Performance
   - System Metrics

### Test 9: ML Model Training

```bash
# Train the ML model with demo data
docker-compose exec api python -c "
from app.ml.trainer import train_model
from app.storage.postgres import get_db
db = next(get_db())
model = train_model(db)
print(f'Model trained successfully!')
"
```

### Test 10: Integration Test Script

Create a test script:

```bash
# Save this as test_integration.sh
#!/bin/bash

set -e

echo "🧪 Running InfraMind Integration Tests..."
echo ""

# 1. Health check
echo "✓ Testing API health..."
curl -sf http://localhost:8081/health > /dev/null
echo "  API is healthy"

# 2. Optimization request
echo "✓ Testing optimization endpoint..."
RESULT=$(curl -sf -X POST http://localhost:8081/optimize \
  -H "Content-Type: application/json" \
  -d '{"repo":"test/repo","branch":"main"}')
echo "  Optimization response received"

# 3. Report build
echo "✓ Testing build reporting..."
curl -sf -X POST http://localhost:8081/builds/complete \
  -H "Content-Type: application/json" \
  -d '{"repo":"test/repo","branch":"main","duration":180,"status":"success"}' > /dev/null
echo "  Build reported successfully"

# 4. Check Prometheus
echo "✓ Testing Prometheus..."
curl -sf http://localhost:9092/-/healthy > /dev/null
echo "  Prometheus is healthy"

# 5. Check Grafana
echo "✓ Testing Grafana..."
curl -sf http://localhost:3001/api/health > /dev/null
echo "  Grafana is healthy"

# 6. Check database
echo "✓ Testing database..."
docker-compose exec -T postgres pg_isready -U inframind > /dev/null
echo "  Database is ready"

# 7. Check Redis
echo "✓ Testing Redis..."
docker-compose exec -T redis redis-cli ping > /dev/null
echo "  Redis is responding"

echo ""
echo "✅ All integration tests passed!"
```

Make it executable and run:
```bash
chmod +x test_integration.sh
./test_integration.sh
```

---

## 🔧 Testing CI/CD Integration

### Test with Jenkins (Local)

If you have Jenkins running locally:

```groovy
// Create a test pipeline in Jenkins
pipeline {
  agent any

  environment {
    INFRAMIND_URL = 'http://host.docker.internal:8081'
  }

  stages {
    stage('Test Optimization') {
      steps {
        script {
          def opts = sh(
            script: """
              curl -sf -X POST \${INFRAMIND_URL}/optimize \\
                -H 'Content-Type: application/json' \\
                -d '{"repo":"test/repo","branch":"main"}'
            """,
            returnStdout: true
          ).trim()

          echo "Optimization suggestions: ${opts}"
        }
      }
    }
  }
}
```

### Test with Shell Script (Simulates CI/CD)

```bash
#!/bin/bash
# test_cicd.sh - Simulates CI/CD pipeline

echo "🚀 Simulating CI/CD pipeline with InfraMind..."

# 1. Get optimization suggestions
echo "📊 Getting optimization suggestions..."
OPTS=$(curl -sf -X POST http://localhost:8081/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "myorg/myrepo",
    "branch": "main",
    "build_type": "release"
  }')

echo "Suggestions received: $OPTS"

# Extract values
CPU=$(echo $OPTS | jq -r '.cpu')
MEMORY=$(echo $OPTS | jq -r '.memory')
CONCURRENCY=$(echo $OPTS | jq -r '.concurrency')

echo "  CPU: $CPU"
echo "  Memory: $MEMORY MB"
echo "  Concurrency: $CONCURRENCY"

# 2. Simulate build
echo "🔨 Building with optimized settings..."
START_TIME=$(date +%s)

# Simulate build work (replace with actual build)
sleep 3

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 3. Report results
echo "📝 Reporting build results..."
curl -sf -X POST http://localhost:8081/builds/complete \
  -H "Content-Type: application/json" \
  -d "{
    \"repo\": \"myorg/myrepo\",
    \"branch\": \"main\",
    \"duration\": $DURATION,
    \"status\": \"success\",
    \"cpu\": $CPU,
    \"memory\": $MEMORY
  }" | jq '.'

echo "✅ CI/CD simulation complete!"
```

Run it:
```bash
chmod +x test_cicd.sh
./test_cicd.sh
```

---

## 🐳 Testing Kubernetes Deployment (Optional)

If you have a local Kubernetes cluster (minikube, kind, k3s):

### 1. Start Local Cluster

```bash
# Using minikube
minikube start

# Or using kind
kind create cluster --name inframind-test
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (use test values)
kubectl create secret generic inframind-secrets \
  --namespace=infra \
  --from-literal=api-key=test-api-key-12345 \
  --from-literal=postgres-password=testpass123 \
  --from-literal=database-url="postgresql://inframind:testpass123@postgres.infra.svc.cluster.local:5432/inframind" \
  --from-literal=postgres-exporter-dsn="postgresql://inframind:testpass123@localhost:5432/inframind?sslmode=disable" \
  --from-literal=redis-password=testredis123 \
  --from-literal=redis-url="redis://:testredis123@redis.infra.svc.cluster.local:6379/0" \
  --from-literal=minio-access-key=minioadmin \
  --from-literal=minio-secret-key=minioadmin123 \
  --from-literal=grafana-admin-password=admin123

# Deploy services
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/monitoring.yaml

# Wait for pods
kubectl wait --for=condition=ready pod -l app=inframind-api -n infra --timeout=300s

# Check status
kubectl get pods -n infra
```

### 3. Test in Kubernetes

```bash
# Port-forward API
kubectl port-forward -n infra svc/inframind-api 8081:8080 &

# Test API
curl http://localhost:8081/health

# Port-forward Grafana
kubectl port-forward -n infra svc/grafana-service 3001:3000 &

# Open Grafana
open http://localhost:3001
```

### 4. Cleanup

```bash
kubectl delete namespace infra
minikube stop  # or kind delete cluster --name inframind-test
```

---

## 📊 Verification Checklist

After running tests, verify:

- [ ] All Docker containers are running (`docker-compose ps`)
- [ ] API health endpoint returns success
- [ ] Swagger UI is accessible at http://localhost:8081/docs
- [ ] Optimization endpoint returns valid suggestions
- [ ] Build reporting endpoint accepts data
- [ ] PostgreSQL is accessible and has tables
- [ ] Redis is responding to commands
- [ ] MinIO console is accessible
- [ ] Prometheus is collecting metrics
- [ ] Grafana dashboards are visible
- [ ] CLI tool installs and works
- [ ] Integration test script passes

---

## 🐛 Troubleshooting

### API not responding

```bash
# Check API logs
docker-compose logs api

# Check if database is ready
docker-compose exec postgres pg_isready -U inframind

# Restart API
docker-compose restart api
```

### Database connection errors

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U inframind -c "SELECT 1"
```

### Redis connection errors

```bash
# Check Redis logs
docker-compose logs redis

# Test connection
docker-compose exec redis redis-cli ping
```

### Port conflicts

```bash
# Check what's using ports
netstat -an | grep -E ":(8081|5433|6380|9000|9092|3001)"

# Change ports in .env file
echo "API_PORT=8082" >> .env
docker-compose down && docker-compose up -d
```

### Services not starting

```bash
# Check all logs
docker-compose logs

# Check specific service
docker-compose logs api

# Restart everything
docker-compose down
docker-compose up -d
```

---

## 🎯 Performance Testing (Optional)

### Load Test with Apache Bench

```bash
# Install Apache Bench (if not installed)
# Ubuntu/Debian: sudo apt-get install apache2-utils
# macOS: brew install httpd

# Test optimization endpoint
ab -n 1000 -c 10 -p request.json -T application/json \
  http://localhost:8081/optimize

# Where request.json contains:
# {"repo":"test/repo","branch":"main"}
```

### Load Test with wrk

```bash
# Install wrk
# Ubuntu: sudo apt-get install wrk
# macOS: brew install wrk

# Test API
wrk -t4 -c100 -d30s http://localhost:8081/health
```

---

## 📝 Test Report Template

After testing, create a test report:

```markdown
# InfraMind Test Report

**Date:** YYYY-MM-DD
**Tested By:** Your Name
**Environment:** Docker Compose / Kubernetes

## Test Results

### Functional Tests
- [ ] API health check: PASS/FAIL
- [ ] Optimization endpoint: PASS/FAIL
- [ ] Build reporting: PASS/FAIL
- [ ] Database connectivity: PASS/FAIL
- [ ] Redis connectivity: PASS/FAIL
- [ ] MinIO access: PASS/FAIL

### Integration Tests
- [ ] Prometheus metrics: PASS/FAIL
- [ ] Grafana dashboards: PASS/FAIL
- [ ] CLI tool: PASS/FAIL
- [ ] Demo data generation: PASS/FAIL

### Performance Tests (Optional)
- API response time: X ms
- Concurrent requests: X req/s
- Memory usage: X MB
- CPU usage: X%

## Issues Found
1. [List any issues]

## Recommendations
1. [List recommendations]
```

---

## ✅ Quick Validation Commands

Copy and paste this to run all basic tests:

```bash
#!/bin/bash
echo "🧪 InfraMind Quick Validation"
echo ""
echo "1. API Health..."
curl -sf http://localhost:8081/health && echo " ✅" || echo " ❌"

echo "2. Optimization..."
curl -sf -X POST http://localhost:8081/optimize \
  -H "Content-Type: application/json" \
  -d '{"repo":"test/repo","branch":"main"}' > /dev/null && echo " ✅" || echo " ❌"

echo "3. Database..."
docker-compose exec -T postgres pg_isready -U inframind > /dev/null && echo " ✅" || echo " ❌"

echo "4. Redis..."
docker-compose exec -T redis redis-cli ping > /dev/null && echo " ✅" || echo " ❌"

echo "5. Prometheus..."
curl -sf http://localhost:9092/-/healthy > /dev/null && echo " ✅" || echo " ❌"

echo "6. Grafana..."
curl -sf http://localhost:3001/api/health > /dev/null && echo " ✅" || echo " ❌"

echo ""
echo "✅ All checks complete!"
```

---

**You're ready to test InfraMind! Start with the Quick Test section and work your way through the comprehensive tests as needed.**

Need help? Check the logs: `docker-compose logs -f`
