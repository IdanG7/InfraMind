# InfraMind Integration Guides

This directory contains integration guides for various CI/CD platforms.

## Available Guides

- **[Jenkins](./jenkins.md)** - Integrate with Jenkins pipelines using Groovy scripts or Shared Library
- **[GitHub Actions](./github-actions.md)** - Integrate with GitHub Actions workflows
- **[GitLab CI](./gitlab-ci.md)** - Integrate with GitLab CI/CD pipelines
- **[Generic/API](./generic.md)** - Use the REST API directly with any CI/CD platform

## Quick Comparison

| Platform | Installation | Complexity | Best Method |
|----------|--------------|------------|-------------|
| Jenkins | Groovy/Shared Library | Medium | Shared Library or CLI |
| GitHub Actions | pip install | Easy | CLI Tool |
| GitLab CI | pip install | Easy | CLI Tool |
| CircleCI | pip install | Easy | CLI Tool |
| Azure Pipelines | pip install | Easy | CLI Tool |
| Travis CI | pip install | Easy | CLI Tool |
| Any other | REST API | Easy | Direct API calls |

## General Integration Pattern

All integrations follow the same pattern:

### 1. Before Build - Get Optimization Suggestions

```bash
# Using CLI
inframind optimize --repo REPO --branch BRANCH --format env

# Using API
curl -X POST http://inframind:8081/optimize \
  -H 'Content-Type: application/json' \
  -d '{"repo":"REPO","branch":"BRANCH"}'
```

### 2. During Build - Apply Suggestions

Use the suggested values for:
- CPU cores: `-j${CPU}`, `--parallel ${CPU}`
- Memory: Environment variables, Docker limits
- Concurrency: Test runners, parallel jobs
- Cache: Enable/disable caching strategies

### 3. After Build - Report Results

```bash
# Using CLI
inframind report --repo REPO --branch BRANCH \
  --duration SECONDS --status success|failure

# Using API
curl -X POST http://inframind:8081/builds/complete \
  -H 'Content-Type: application/json' \
  -d '{"repo":"REPO","branch":"BRANCH","duration":180,"status":"success"}'
```

## Prerequisites

All integrations require:

1. **InfraMind API** running and accessible from CI/CD runners
2. **API credentials** stored as secrets/environment variables
3. One of:
   - Python 3.8+ (for CLI method)
   - `curl` (for API method)

## Common Environment Variables

Set these in your CI/CD platform:

- `INFRAMIND_URL` - API base URL (e.g., `http://inframind.example.com:8081`)
- `INFRAMIND_API_KEY` - Authentication key (optional but recommended)

## Platform-Specific Guides

### Jenkins

Best for: Large enterprises, complex pipelines

```groovy
@Library('inframind') _
pipeline {
  stages {
    stage('Optimize') { steps { inframindOptimize() } }
    stage('Build') { steps { sh 'make build -j${INFRAMIND_CPU}' } }
  }
  post { always { inframindNotify() } }
}
```

[Full Jenkins Guide →](./jenkins.md)

### GitHub Actions

Best for: GitHub-hosted projects, modern workflows

```yaml
- name: Get Suggestions
  run: |
    inframind optimize --repo ${{ github.repository }} --branch ${{ github.ref_name }} --format env >> $GITHUB_ENV

- name: Build
  run: make build -j${INFRAMIND_CPU}
```

[Full GitHub Actions Guide →](./github-actions.md)

### GitLab CI

Best for: GitLab-hosted projects, Docker-based builds

```yaml
optimize:
  script:
    - inframind optimize --repo ${CI_PROJECT_PATH} --branch ${CI_COMMIT_BRANCH} --format shell > build.env
  artifacts:
    reports:
      dotenv: build.env
```

[Full GitLab CI Guide →](./gitlab-ci.md)

### Generic/API

Best for: Custom CI/CD, scripts, any platform

```bash
#!/bin/bash
OPTS=$(curl -sf http://inframind:8081/optimize -d '{"repo":"myrepo","branch":"main"}')
CPU=$(echo $OPTS | jq -r '.cpu')
make build -j${CPU}
```

[Full API Guide →](./generic.md)

## CLI Tool

The InfraMind CLI tool provides the easiest integration:

### Installation

```bash
pip install inframind-cli
```

### Usage

```bash
# Get optimization suggestions
inframind optimize --repo myorg/myrepo --branch main

# Output as environment variables
inframind optimize --repo myorg/myrepo --branch main --format env

# Report build results
inframind report --repo myorg/myrepo --branch main \
  --duration 180 --status success
```

[CLI Documentation →](../../cli/README.md)

## Troubleshooting

### Connection Issues

Test API connectivity:

```bash
curl -v http://inframind:8081/health
```

### Authentication Issues

Verify API key:

```bash
curl -H "X-API-Key: YOUR_KEY" http://inframind:8081/health
```

### Missing Suggestions

Check if data exists for your repo:

```bash
inframind optimize --repo YOUR_REPO --branch main --format json
```

## Best Practices

1. **Always report results** - ML model needs data to improve
2. **Use artifacts/cache** - Cache CLI installation and dependencies
3. **Handle failures** - Provide fallback values if API is unavailable
4. **Track metrics** - Monitor build time improvements over time
5. **Start simple** - Begin with basic integration, add complexity later

## Examples by Language/Framework

### C/C++ with CMake

```bash
cmake --build build --parallel ${INFRAMIND_CPU}
```

### Node.js

```bash
npm test -- --max-workers=${INFRAMIND_CONCURRENCY}
NODE_OPTIONS="--max-old-space-size=${INFRAMIND_MEMORY}" npm run build
```

### Java/Maven

```bash
mvn clean package -T ${INFRAMIND_CPU}
```

### Python

```bash
pytest -n ${INFRAMIND_CONCURRENCY}
```

### Go

```bash
go build -p ${INFRAMIND_CPU}
```

### Rust

```bash
cargo build --jobs ${INFRAMIND_CPU}
```

### Docker

```bash
docker build --cpus=${INFRAMIND_CPU} --memory=${INFRAMIND_MEMORY}m .
```

## Support

- **Documentation**: [docs.inframind.dev](https://docs.inframind.dev)
- **Issues**: [GitHub Issues](https://github.com/yourorg/inframind/issues)
- **API Reference**: [../api.md](../api.md)

---

**Ready to integrate?** Pick your platform from the guides above and start optimizing your builds!
