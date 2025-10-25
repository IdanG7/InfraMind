# InfraMind - Visual Architecture Reference

All Mermaid diagrams in one place for easy reference.

## 1. System Overview

```mermaid
graph TB
    Dev[Developer pushes code] --> Jenkins[Jenkins Pipeline]
    Jenkins -->|executes on| Agent[K8s Build Agent Pod]
    Agent --> CppAgent[C++ Telemetry Agent]

    CppAgent -->|metrics| Prom[Prometheus]
    CppAgent -->|logs| S3[S3/MinIO]

    Jenkins -->|webhooks| API[FastAPI Analytics API]
    API <-->|store| PG[(PostgreSQL)]
    API <-->|cache| Redis[(Redis)]

    Prom --> Graf[Grafana Dashboards]

    API -->|ML suggestions| Jenkins
    API -->|train| ML[ML Optimizer]
    ML -->|predict| API

    style API fill:#3498db,stroke:#2980b9,color:#fff
    style ML fill:#e74c3c,stroke:#c0392b,color:#fff
    style CppAgent fill:#2ecc71,stroke:#27ae60,color:#fff
```

## 2. Optimization Flow

```mermaid
sequenceDiagram
    participant J as Jenkins
    participant API as InfraMind API
    participant ML as ML Optimizer
    participant K8s as Kubernetes

    J->>API: POST /optimize (context)
    API->>ML: Get suggestions
    ML->>ML: Predict duration for candidates
    ML->>ML: Apply safety guards
    ML-->>API: Best config + rationale
    API-->>J: Suggestions (CPU, mem, cache)
    J->>K8s: Apply optimized resources
    K8s-->>J: Start build with new config
    J->>API: POST /builds/complete (results)
    API->>ML: Update training data
```

## 3. Data Flow (Complete Build Lifecycle)

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

## 4. C++ Agent Architecture

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

## 5. ML Pipeline Overview

```mermaid
flowchart TB
    subgraph Input Features
        Static[Static Context<br/>repo, branch, image]
        Resources[Requested Resources<br/>CPU, mem, concurrency]
        Telemetry[Historical Telemetry<br/>RSS, I/O, cache hits]
    end

    subgraph ML Pipeline
        Features[Feature Engineering<br/>15+ features]
        Model[RandomForest<br/>Regressor]
        Predict[Duration Prediction]
    end

    subgraph Optimization
        Candidates[Generate Candidates<br/>Grid search ± deltas]
        Score[Score Each Config]
        Safety[Apply Safety Guards<br/>mem ≥ 1.2× RSS p95]
        Best[Select Best Config]
    end

    Static --> Features
    Resources --> Features
    Telemetry --> Features

    Features --> Model
    Model --> Predict

    Predict --> Candidates
    Candidates --> Score
    Score --> Safety
    Safety --> Best

    Best -->|Suggestions| Output[CPU, mem, concurrency,<br/>cache config]

    style Model fill:#e74c3c,stroke:#c0392b,color:#fff
    style Safety fill:#f39c12,stroke:#e67e22,color:#fff
    style Output fill:#2ecc71,stroke:#27ae60,color:#fff
```

## 6. Training Pipeline

```mermaid
flowchart LR
    subgraph Data Collection
        DB[(PostgreSQL)]
        Fetch[Fetch last 500<br/>successful runs]
        DB --> Fetch
    end

    subgraph Feature Engineering
        Raw[Raw Run Data]
        Compute[Compute Features<br/>CPU, mem, I/O, cache]
        Matrix[Feature Matrix X<br/>Labels y]
        Fetch --> Raw
        Raw --> Compute
        Compute --> Matrix
    end

    subgraph Training
        Split[Train/Test Split<br/>80/20]
        Train[Train RandomForest]
        Eval[Evaluate<br/>MAE, R²]
        Matrix --> Split
        Split --> Train
        Train --> Eval
    end

    subgraph Deployment
        Save[Save Model<br/>joblib]
        Version[Version: v20251025]
        Redis[(Redis<br/>im:model:active)]
        Eval --> Save
        Save --> Version
        Version --> Redis
    end

    style Train fill:#e74c3c,stroke:#c0392b,color:#fff
    style Eval fill:#3498db,stroke:#2980b9,color:#fff
    style Redis fill:#2ecc71,stroke:#27ae60,color:#fff
```

## 7. Optimization Strategy

```mermaid
flowchart TB
    Start[Optimization Request] --> Context[Receive Context<br/>tool, repo, metrics]

    Context --> LastSuccess{Last Successful<br/>Config?}
    LastSuccess -->|Yes| Base[Use as baseline]
    LastSuccess -->|No| Default[Use defaults<br/>cpu=4, mem=8GB]

    Base --> Grid[Generate Grid<br/>config ± Δ]
    Default --> Grid

    Grid --> Explore{15% chance}
    Explore -->|Explore| Random[Add random config]
    Explore -->|Exploit| Score

    Random --> Score[Score All Candidates]

    Score --> Loop{For each config}
    Loop --> Safety[Apply Safety Guards]
    Safety --> Predict[Predict Duration]
    Predict --> Compare{Best so far?}
    Compare -->|Yes| UpdateBest[Update best]
    Compare -->|No| Loop
    UpdateBest --> Loop

    Loop -->|Done| Return[Return Best Config<br/>+ Rationale + Confidence]

    style Safety fill:#f39c12,stroke:#e67e22,color:#fff
    style Predict fill:#e74c3c,stroke:#c0392b,color:#fff
    style Return fill:#2ecc71,stroke:#27ae60,color:#fff
```

## 8. Kubernetes Deployment

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

## 9. Docker Compose (Local)

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

## 10. API Request Flow

```mermaid
sequenceDiagram
    participant C as Client/Jenkins
    participant API as InfraMind API
    participant Auth as Auth Middleware
    participant DB as PostgreSQL
    participant Cache as Redis
    participant ML as ML Engine

    C->>API: POST /builds/start
    API->>Auth: Verify X-IM-Token
    Auth-->>API: Authorized
    API->>DB: Insert run record
    DB-->>API: Run ID
    API-->>C: {ok: true}

    C->>API: POST /optimize
    API->>Auth: Verify token
    API->>Cache: Check cached suggestion
    Cache-->>API: Cache miss
    API->>DB: Query history
    DB-->>API: Last 100 runs
    API->>ML: Generate suggestions
    ML-->>API: Best config + rationale
    API->>Cache: Cache suggestion
    API->>DB: Store suggestion
    API-->>C: Suggestions

    C->>API: POST /builds/step (telemetry)
    API->>DB: Store step data
    API-->>C: {ok: true}

    C->>API: POST /builds/complete
    API->>DB: Update run status
    DB-->>API: Updated
    API->>ML: Trigger feature computation
    API-->>C: {ok: true}
```

## 11. Demo Data Generation

```mermaid
flowchart LR
    Start[make seed-demo] --> Gen[Generate 50 Runs]
    Gen --> Vary[Vary configs:<br/>cpu=2-8, mem=4-32GB]
    Vary --> Store[(Store in PostgreSQL)]
    Store --> Features[Compute Features]
    Features --> Train[Train ML Model]
    Train --> Save[Save model to<br/>models/v*.joblib]
    Save --> Redis[(Update Redis<br/>active version)]
    Redis --> Done[✓ Ready to optimize]

    style Train fill:#e74c3c,stroke:#c0392b,color:#fff
    style Done fill:#2ecc71,stroke:#27ae60,color:#fff
```

## 12. Build Optimization Impact

```mermaid
sequenceDiagram
    autonumber
    participant Dev as Developer
    participant Jenkins
    participant IM as InfraMind
    participant K8s as Kubernetes

    Note over Dev,K8s: First Build (Baseline)
    Dev->>Jenkins: Push code
    Jenkins->>IM: Request suggestions
    IM-->>Jenkins: Default config (cpu=4, mem=8GB)
    Jenkins->>K8s: Start build
    K8s-->>Jenkins: Build takes 15 min
    Jenkins->>IM: Report: 15 min, cpu=60%, mem=75%

    Note over Dev,K8s: Second Build (Learning)
    Dev->>Jenkins: Push code
    Jenkins->>IM: Request suggestions
    IM->>IM: Analyze: CPU underused, mem OK
    IM-->>Jenkins: Try cpu=6, mem=8GB
    Jenkins->>K8s: Start build
    K8s-->>Jenkins: Build takes 12 min
    Jenkins->>IM: Report: 12 min, cpu=80%, mem=70%

    Note over Dev,K8s: Third Build (Optimized)
    Dev->>Jenkins: Push code
    Jenkins->>IM: Request suggestions
    IM->>IM: Model predicts 10 min with cpu=8
    IM-->>Jenkins: Optimized: cpu=8, mem=12GB
    Jenkins->>K8s: Start build
    K8s-->>Jenkins: Build takes 9 min
    Jenkins->>IM: Report: 9 min ✓

    Note over IM: Model continues learning<br/>and optimizing
```

---

**Usage**: These diagrams are rendered in GitHub/GitLab markdown viewers that support Mermaid. For local viewing, use tools like:
- VS Code with Mermaid extension
- Obsidian
- Typora
- Online: https://mermaid.live

---

For more details, see:
- [Architecture Documentation](docs/architecture.md)
- [ML Documentation](docs/ml.md)
- [API Reference](docs/api.md)
- [Benefits & ROI](docs/benefits.md)
