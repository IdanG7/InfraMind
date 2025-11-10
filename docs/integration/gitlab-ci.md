# GitLab CI Integration Guide

This guide shows how to integrate InfraMind with GitLab CI/CD pipelines.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Basic Integration](#basic-integration)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)

---

## Prerequisites

1. InfraMind API running and accessible from GitLab runners
2. GitLab CI/CD enabled for your project
3. API credentials stored as GitLab CI/CD variables

### Setup GitLab CI/CD Variables

Add these variables to your project:

1. Go to: Project → Settings → CI/CD → Variables
2. Add variables:
   - `INFRAMIND_URL`: Your InfraMind API URL (e.g., `http://inframind.example.com:8081`)
   - `INFRAMIND_API_KEY`: Your API key (mark as "Masked" and "Protected")

---

## Basic Integration

### Simple `.gitlab-ci.yml`

```yaml
stages:
  - optimize
  - build
  - report

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

optimize:
  stage: optimize
  image: python:3.11-slim
  script:
    - pip install InfraMind
    - inframind optimize --repo ${CI_PROJECT_PATH} --branch ${CI_COMMIT_BRANCH} --format shell > build.env
  artifacts:
    reports:
      dotenv: build.env

build:
  stage: build
  image: gcc:11
  dependencies:
    - optimize
  script:
    - echo "Building with $INFRAMIND_CPU CPUs and ${INFRAMIND_MEMORY}MB memory"
    - make build -j${INFRAMIND_CPU}
  artifacts:
    paths:
      - build/

report:
  stage: report
  image: python:3.11-slim
  when: always
  dependencies:
    - optimize
  script:
    - pip install InfraMind
    - |
      STATUS=$([ "$CI_JOB_STATUS" == "success" ] && echo "success" || echo "failure")
      inframind report \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --duration ${CI_JOB_DURATION} \
        --status ${STATUS} \
        --cpu ${INFRAMIND_CPU} \
        --memory ${INFRAMIND_MEMORY}
```

---

## Complete Examples

### Example 1: C++ Project with CMake

```yaml
stages:
  - setup
  - optimize
  - build
  - test
  - report

variables:
  GIT_SUBMODULE_STRATEGY: recursive
  CCACHE_DIR: "$CI_PROJECT_DIR/.ccache"

cache:
  key: "$CI_COMMIT_REF_SLUG"
  paths:
    - .ccache/
    - .cache/pip

setup:
  stage: setup
  image: python:3.11-slim
  script:
    - pip install InfraMind
  cache:
    key: pip-cache
    paths:
      - .cache/pip

optimize:
  stage: optimize
  image: python:3.11-slim
  script:
    - pip install InfraMind
    - |
      inframind optimize \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --build-type release \
        --format shell > build.env
    - cat build.env
  artifacts:
    reports:
      dotenv: build.env
    expire_in: 1 hour

build:
  stage: build
  image: gcc:11
  dependencies:
    - optimize
  before_script:
    - apt-get update && apt-get install -y cmake ninja-build ccache
  script:
    - echo "Optimized build with $INFRAMIND_CPU CPUs"
    - |
      cmake -S . -B build \
        -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_C_COMPILER_LAUNCHER=ccache \
        -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
    - cmake --build build --parallel ${INFRAMIND_CPU}
  artifacts:
    paths:
      - build/
    expire_in: 1 day

test:
  stage: test
  image: gcc:11
  dependencies:
    - build
    - optimize
  script:
    - ctest --test-dir build --parallel ${INFRAMIND_CONCURRENCY} --output-on-failure
  artifacts:
    reports:
      junit: build/test-results.xml

report:
  stage: report
  image: python:3.11-slim
  when: always
  dependencies:
    - optimize
  script:
    - pip install InfraMind
    - |
      STATUS=$([ "$CI_JOB_STATUS" == "success" ] && echo "success" || echo "failure")
      inframind report \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --duration ${CI_JOB_DURATION} \
        --status ${STATUS}
```

### Example 2: Docker Build

```yaml
stages:
  - optimize
  - build
  - push
  - report

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

services:
  - docker:24-dind

optimize:
  stage: optimize
  image: python:3.11-slim
  script:
    - pip install InfraMind
    - inframind optimize --repo ${CI_PROJECT_PATH} --branch ${CI_COMMIT_BRANCH} --format shell > build.env
  artifacts:
    reports:
      dotenv: build.env

build:
  stage: build
  image: docker:24
  dependencies:
    - optimize
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - |
      docker build \
        --build-arg JOBS=${INFRAMIND_CPU} \
        --build-arg MEMORY=${INFRAMIND_MEMORY} \
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA \
        --tag $CI_REGISTRY_IMAGE:latest \
        .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest

report:
  stage: report
  image: python:3.11-slim
  when: always
  dependencies:
    - optimize
  script:
    - pip install InfraMind
    - |
      STATUS=$([ "$CI_JOB_STATUS" == "success" ] && echo "success" || echo "failure")
      inframind report \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --duration ${CI_JOB_DURATION} \
        --status ${STATUS}
```

### Example 3: Multi-Stage Pipeline

```yaml
stages:
  - prepare
  - build
  - test
  - deploy
  - report

.inframind_optimize:
  image: python:3.11-slim
  before_script:
    - pip install InfraMind
  script:
    - |
      inframind optimize \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --build-type ${BUILD_TYPE:-release} \
        --format shell > build.env
  artifacts:
    reports:
      dotenv: build.env
    expire_in: 1 hour

.inframind_report:
  image: python:3.11-slim
  when: always
  before_script:
    - pip install InfraMind
  script:
    - |
      STATUS=$([ "$CI_JOB_STATUS" == "success" ] && echo "success" || echo "failure")
      inframind report \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --duration ${CI_JOB_DURATION} \
        --status ${STATUS}

optimize:debug:
  extends: .inframind_optimize
  stage: prepare
  variables:
    BUILD_TYPE: debug
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'

optimize:release:
  extends: .inframind_optimize
  stage: prepare
  variables:
    BUILD_TYPE: release
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

build:
  stage: build
  image: gcc:11
  script:
    - cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    - cmake --build build --parallel ${INFRAMIND_CPU}
  artifacts:
    paths:
      - build/

test:
  stage: test
  image: gcc:11
  dependencies:
    - build
  script:
    - ctest --test-dir build --parallel ${INFRAMIND_CONCURRENCY}

deploy:
  stage: deploy
  script:
    - ./deploy.sh
  only:
    - main

report:
  extends: .inframind_report
  stage: report
```

### Example 4: Parallel Jobs

```yaml
stages:
  - optimize
  - build
  - report

optimize:
  stage: optimize
  image: python:3.11-slim
  script:
    - pip install InfraMind
    - inframind optimize --repo ${CI_PROJECT_PATH} --branch ${CI_COMMIT_BRANCH} --format shell > build.env
  artifacts:
    reports:
      dotenv: build.env

.build_template:
  stage: build
  image: gcc:11
  dependencies:
    - optimize
  before_script:
    - apt-get update && apt-get install -y cmake ninja-build
  script:
    - |
      cmake -S . -B build \
        -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
        -DPLATFORM=${PLATFORM}
    - cmake --build build --parallel ${INFRAMIND_CPU}
  artifacts:
    paths:
      - build-${PLATFORM}-${BUILD_TYPE}/

build:linux:debug:
  extends: .build_template
  variables:
    PLATFORM: linux
    BUILD_TYPE: Debug

build:linux:release:
  extends: .build_template
  variables:
    PLATFORM: linux
    BUILD_TYPE: Release

build:windows:release:
  extends: .build_template
  variables:
    PLATFORM: windows
    BUILD_TYPE: Release
  tags:
    - windows

report:
  stage: report
  image: python:3.11-slim
  when: always
  dependencies:
    - optimize
  script:
    - pip install InfraMind
    - |
      STATUS=$([ "$CI_JOB_STATUS" == "success" ] && echo "success" || echo "failure")
      inframind report \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --duration ${CI_JOB_DURATION} \
        --status ${STATUS}
```

---

## Using GitLab CI/CD Templates

Create a reusable template in `.gitlab/ci/inframind.yml`:

```yaml
# .gitlab/ci/inframind.yml

.inframind:optimize:
  image: python:3.11-slim
  before_script:
    - pip install InfraMind
  script:
    - |
      inframind optimize \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --build-type ${BUILD_TYPE:-release} \
        --format shell > build.env
  artifacts:
    reports:
      dotenv: build.env
    expire_in: 1 hour

.inframind:report:
  image: python:3.11-slim
  when: always
  before_script:
    - pip install InfraMind
  script:
    - |
      STATUS=$([ "$CI_JOB_STATUS" == "success" ] && echo "success" || echo "failure")
      DURATION=${CI_JOB_DURATION:-0}

      inframind report \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --duration ${DURATION} \
        --status ${STATUS} \
        --cpu ${INFRAMIND_CPU:-4} \
        --memory ${INFRAMIND_MEMORY:-8192}
```

Use the template in your `.gitlab-ci.yml`:

```yaml
include:
  - local: '.gitlab/ci/inframind.yml'

stages:
  - optimize
  - build
  - report

optimize:
  extends: .inframind:optimize
  stage: optimize

build:
  stage: build
  dependencies:
    - optimize
  script:
    - make build -j${INFRAMIND_CPU}

report:
  extends: .inframind:report
  stage: report
  dependencies:
    - optimize
```

---

## Best Practices

### 1. Use Artifacts for Environment Variables

```yaml
optimize:
  script:
    - inframind optimize --repo ${CI_PROJECT_PATH} --branch ${CI_COMMIT_BRANCH} --format shell > build.env
  artifacts:
    reports:
      dotenv: build.env  # Automatically loads as environment variables
```

### 2. Cache Dependencies

```yaml
variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  key: "$CI_COMMIT_REF_SLUG"
  paths:
    - .cache/pip
    - .ccache
```

### 3. Handle Failures Gracefully

```yaml
optimize:
  script:
    - |
      if ! inframind optimize --repo ${CI_PROJECT_PATH} --branch ${CI_COMMIT_BRANCH} --format shell > build.env; then
        echo "INFRAMIND_CPU=4" > build.env
        echo "INFRAMIND_MEMORY=8192" >> build.env
        echo "INFRAMIND_CONCURRENCY=4" >> build.env
      fi
  allow_failure: true
```

### 4. Use Rules for Conditional Execution

```yaml
optimize:
  script:
    - inframind optimize --repo ${CI_PROJECT_PATH} --branch ${CI_COMMIT_BRANCH} --format shell > build.env
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
    - if: '$CI_COMMIT_BRANCH == "develop"'
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

### 5. Leverage GitLab CI/CD Variables

```yaml
optimize:
  script:
    - |
      inframind optimize \
        --repo ${CI_PROJECT_PATH} \
        --branch ${CI_COMMIT_BRANCH} \
        --build-type ${CI_COMMIT_TAG:+release}${CI_COMMIT_TAG:-debug} \
        --format shell > build.env
```

---

## Troubleshooting

### Check API Connectivity

```yaml
test:api:
  stage: .pre
  image: curlimages/curl:latest
  script:
    - curl -v ${INFRAMIND_URL}/health
```

### Debug Environment Variables

```yaml
build:
  script:
    - echo "CPU=$INFRAMIND_CPU"
    - echo "Memory=$INFRAMIND_MEMORY"
    - echo "Concurrency=$INFRAMIND_CONCURRENCY"
    - env | grep INFRAMIND
```

### Test CLI Installation

```yaml
test:cli:
  stage: .pre
  image: python:3.11-slim
  script:
    - pip install InfraMind
    - inframind --help
    - inframind health
```

---

## Advanced Features

### Using Merge Request Pipelines

```yaml
optimize:mr:
  extends: .inframind:optimize
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  variables:
    BUILD_TYPE: debug

optimize:main:
  extends: .inframind:optimize
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  variables:
    BUILD_TYPE: release
```

### Parent-Child Pipelines

```yaml
# .gitlab-ci.yml
trigger:build:
  trigger:
    include: .gitlab/ci/build-pipeline.yml
    strategy: depend

# .gitlab/ci/build-pipeline.yml
stages:
  - optimize
  - build

optimize:
  extends: .inframind:optimize

build:
  dependencies:
    - optimize
  script:
    - make build -j${INFRAMIND_CPU}
```

---

## Next Steps

- [View API Reference](../api.md)
- [Configure Grafana Dashboards](../deployment/production.md)
- [Learn about ML Models](../ml.md)
- [GitHub Actions Integration](./github-actions.md)
