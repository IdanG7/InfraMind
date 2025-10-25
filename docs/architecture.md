# Architecture Overview

InfraMind is a distributed system for CI/CD optimization with ML-driven resource tuning.

## System Components

### 1. FastAPI Service (`services/api`)

**Purpose**: Central brain of InfraMind. Receives telemetry, trains models, serves optimization suggestions.

**Tech Stack**:
- FastAPI + Pydantic for API
- SQLAlchemy + PostgreSQL for persistence
- Redis for caching
- scikit-learn + LightGBM for ML

**Key Endpoints**:
- `POST /builds/start` - Register new build
- `POST /builds/step` - Record step telemetry
- `POST /builds/complete` - Finalize build
- `POST /optimize` - Get optimization suggestions
- `GET /features/{run_id}` - Inspect features

### 2. C++ Telemetry Agent (`agents/cpp_agent`)

**Purpose**: Low-overhead profiling of build agents. Collects CPU, memory, I/O, and cache metrics.

```mermaid
flowchart TB
    subgraph Agent Process
        Main[Main Loop<br/>1s interval]

        subgraph Collectors
            CPU[CPU Collector<br/>/proc/stat]
            Mem[Memory Collector<br/>/proc/meminfo]
            IO[I/O Collector<br/>/proc/self/io]
            Cache[Cache Collector<br/>ccache/bazel stats]
        end

        subgraph Exporters
            Prom[Prometheus Exporter<br/>:9102/metrics]
            Log[JSON Logger<br/>stdout]
        end

        Main --> CPU
        Main --> Mem
        Main --> IO
        Main --> Cache

        CPU --> Metrics[Aggregate Metrics]
        Mem --> Metrics
        IO --> Metrics
        Cache --> Metrics

        Metrics --> Prom
        Metrics --> Log
    end

    K8s[Kubernetes] -.->|scrape :9102| Prom
    FluentBit[Fluent Bit] -.->|read stdout| Log
    FluentBit --> S3[S3/MinIO]

    style CPU fill:#3498db,stroke:#2980b9,color:#fff
    style Prom fill:#e74c3c,stroke:#c0392b,color:#fff
    style Log fill:#f39c12,stroke:#e67e22,color:#fff
```

**Architecture**:
- **Collectors**: Modular metric collectors (CPU, mem, I/O, cache)
- **Exporters**: Prometheus HTTP endpoint (`:9102/metrics`) + JSON logging
- **Runtime**: Runs as DaemonSet or sidecar in Kubernetes

**Metrics Exposed**:
```
im_cpu_usage_percent
im_mem_used_bytes
im_io_read_bytes_total
im_io_write_bytes_total
im_cache_hit_ratio
```

### 3. Jenkins Shared Library (`services/jenkins-shared-lib`)

**Purpose**: Drop-in integration for existing Jenkins pipelines.

**Functions**:
- `inframindOptimize()` - Fetch suggestions and set env vars
- `inframindStage()` - Wrap stages with telemetry
- `inframindNotify()` - Report completion

**Usage**:
```groovy
@Library('inframind') _
pipeline {
  stages {
    stage('Optimize') {
      steps { inframindOptimize(params: [tool: 'cmake']) }
    }
    stage('Build') {
      steps { inframindStage(name: 'compile') { sh 'make' } }
    }
  }
  post { always { inframindNotify() } }
}
```

### 4. ML Optimizer (`services/api/app/ml`)

**Components**:
- **Feature Engineering**: Compute features from run + step data
- **Model Training**: RandomForest regressor predicting `duration_s`
- **Optimizer**: Grid search + safety guards to select config
- **Model Store**: Versioned model persistence with joblib

**Safety Guards**:
- Memory ≥ 1.2× historical RSS p95
- CPU ≥ concurrency / 4
- Bounded exploration (±25% from last success)

**Optimization Loop**:
1. Receive context (repo, tool, recent metrics)
2. Generate candidate configs (grid around last success)
3. Score each with trained model
4. Apply safety constraints
5. Return argmin with rationale

## Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant Jenkins
    participant API as FastAPI /optimize
    participant DB as PostgreSQL
    participant Model as ML Model
    participant K8s as K8s Agent Pod
    participant Agent as C++ Agent
    participant Prom as Prometheus
    participant Graf as Grafana

    Jenkins->>API: POST /builds/start
    Jenkins->>API: Request optimization
    API->>DB: Query build history
    DB-->>API: Recent runs + metrics
    API->>Model: Predict duration for candidates
    Model-->>API: Best config + confidence
    API-->>Jenkins: Return suggestions

    Jenkins->>K8s: Apply optimized config
    K8s->>Agent: Start telemetry collection

    loop Build running
        Agent->>Prom: Export metrics (CPU, mem, I/O)
        Agent->>Jenkins: Stream logs
    end

    Jenkins->>API: POST /builds/step (telemetry)
    API->>DB: Store step data

    Jenkins->>API: POST /builds/complete
    API->>DB: Store final results
    API->>Model: Update training data

    Prom->>Graf: Render dashboards
```

## Deployment Modes

### Local (Docker Compose)

```bash
make up
```

```mermaid
graph LR
    subgraph Docker Compose
        API[FastAPI :8080]
        PG[(PostgreSQL :5432)]
        Redis[(Redis :6379)]
        Prom[Prometheus :9090]
        Graf[Grafana :3000]
        MinIO[MinIO :9000]

        API <--> PG
        API <--> Redis
        API --> MinIO
        Prom --> Graf
    end

    Browser[Browser] --> API
    Browser --> Graf
```

All services on localhost with persistent volumes.

### Kubernetes

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/
```

```mermaid
graph TB
    subgraph Namespace: infra
        subgraph API Layer
            API1[API Pod 1]
            API2[API Pod 2]
            APISvc[Service: inframind-api]
            API1 --> APISvc
            API2 --> APISvc
        end

        subgraph Data Layer
            PG[PostgreSQL StatefulSet]
            Redis[Redis StatefulSet]
            PGVol[(PVC 20Gi)]
            RedisVol[(PVC 5Gi)]
            PG --> PGVol
            Redis --> RedisVol
        end

        subgraph Telemetry Layer
            Agent1[Agent DaemonSet Pod 1]
            Agent2[Agent DaemonSet Pod 2]
            AgentN[Agent DaemonSet Pod N]
        end

        subgraph Observability
            Prom[Prometheus]
            Graf[Grafana]
            Prom --> Graf
        end

        APISvc <--> PG
        APISvc <--> Redis
        Agent1 -.->|scrape :9102| Prom
        Agent2 -.->|scrape :9102| Prom
        AgentN -.->|scrape :9102| Prom
    end

    Jenkins[Jenkins] -->|webhook| APISvc
    User[User] --> Graf
```

Components:
- API: Deployment (2 replicas)
- Agent: DaemonSet (all nodes)
- Postgres: StatefulSet
- Redis: StatefulSet
- Prometheus: Operator
- Grafana: Deployment

### Helm

```bash
helm install inframind deploy/helm/inframind \
  --namespace infra --create-namespace \
  --set api.image.tag=v0.1.0 \
  --set agent.image.tag=v0.1.0
```

## Security

- **API Authentication**: API key via `X-IM-Token` header
- **RBAC**: ServiceAccount with minimal permissions (read/patch pods)
- **Secrets**: Kubernetes Secrets for DB credentials
- **Network Policies**: Restrict egress to DB/Redis only
- **TLS**: Optional mTLS for API (via Istio/Linkerd)

## Scaling

### Horizontal
- API: Scale to N replicas (stateless)
- Agent: DaemonSet (automatic per node)

### Vertical
- Postgres: Increase storage for long retention
- Redis: Increase memory for more cache

### Performance
- API: p99 < 200ms for `/optimize`
- Agent: < 1% CPU overhead
- Model inference: < 10ms
