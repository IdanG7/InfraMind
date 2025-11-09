# GitHub Actions Integration Guide

This guide shows how to integrate InfraMind with GitHub Actions workflows.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Basic Integration](#basic-integration)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)

---

## Prerequisites

1. InfraMind API running and accessible from GitHub Actions runners
2. GitHub repository with Actions enabled
3. API key stored as GitHub Secret

### Setup GitHub Secrets

Add these secrets to your repository:

1. Go to: Repository → Settings → Secrets and variables → Actions
2. Add secrets:
   - `INFRAMIND_URL`: Your InfraMind API URL (e.g., `http://inframind.example.com:8081`)
   - `INFRAMIND_API_KEY`: Your API key

---

## Basic Integration

### Simple Workflow

```yaml
name: Build with InfraMind

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install InfraMind CLI
        run: pip install inframind-cli

      - name: Get Optimization Suggestions
        id: optimize
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          OPTS=$(inframind optimize \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --format json)

          echo "cpu=$(echo $OPTS | jq -r '.cpu')" >> $GITHUB_OUTPUT
          echo "memory=$(echo $OPTS | jq -r '.memory')" >> $GITHUB_OUTPUT
          echo "concurrency=$(echo $OPTS | jq -r '.concurrency')" >> $GITHUB_OUTPUT

      - name: Build Project
        run: make build -j${{ steps.optimize.outputs.cpu }}
        env:
          BUILD_MEMORY: ${{ steps.optimize.outputs.memory }}

      - name: Report Results
        if: always()
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          DURATION=$(($(date +%s) - ${{ github.event.created_at }}))
          STATUS="${{ job.status }}"

          inframind report \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --duration $DURATION \
            --status $([ "$STATUS" == "success" ] && echo "success" || echo "failure") \
            --cpu ${{ steps.optimize.outputs.cpu }} \
            --memory ${{ steps.optimize.outputs.memory }}
```

---

## Complete Examples

### Example 1: C++ Project with CMake

```yaml
name: Build C++ Project

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y cmake ninja-build ccache
          pip install inframind-cli

      - name: Setup ccache
        uses: actions/cache@v4
        with:
          path: ~/.ccache
          key: ccache-${{ github.sha }}
          restore-keys: ccache-

      - name: Get InfraMind Suggestions
        id: optimize
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          inframind optimize \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --build-type release \
            --format env >> $GITHUB_ENV

      - name: Configure CMake
        run: |
          cmake -S . -B build \
            -G Ninja \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_C_COMPILER_LAUNCHER=ccache \
            -DCMAKE_CXX_COMPILER_LAUNCHER=ccache

      - name: Build
        run: cmake --build build --parallel ${{ env.INFRAMIND_CPU }}

      - name: Test
        run: ctest --test-dir build --parallel ${{ env.INFRAMIND_CONCURRENCY }}

      - name: Report Build Results
        if: always()
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          inframind report \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --duration ${{ github.event.head_commit.timestamp }} \
            --status ${{ job.status }}
```

### Example 2: Docker Build

```yaml
name: Build Docker Image

on:
  push:
    branches: [main]

jobs:
  docker:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Install InfraMind CLI
        run: pip install inframind-cli

      - name: Get Build Optimization
        id: optimize
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          OPTS=$(inframind optimize \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --format json)

          echo "cpu=$(echo $OPTS | jq -r '.cpu')" >> $GITHUB_OUTPUT
          echo "memory=$(echo $OPTS | jq -r '.memory')" >> $GITHUB_OUTPUT

      - name: Build and Push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: myregistry/myapp:${{ github.sha }}
          build-args: |
            JOBS=${{ steps.optimize.outputs.cpu }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Report Results
        if: always()
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          inframind report \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --duration ${{ github.event.head_commit.timestamp }} \
            --status ${{ job.status }}
```

### Example 3: Node.js Build

```yaml
name: Build Node.js App

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install InfraMind CLI
        run: pip install inframind-cli

      - name: Get Optimization
        id: optimize
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          inframind optimize \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --format env >> $GITHUB_ENV

      - name: Install Dependencies
        run: npm ci

      - name: Build
        run: npm run build
        env:
          NODE_OPTIONS: "--max-old-space-size=${{ env.INFRAMIND_MEMORY }}"

      - name: Test
        run: npm test -- --max-workers=${{ env.INFRAMIND_CONCURRENCY }}

      - name: Report Results
        if: always()
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          inframind report \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --duration ${{ github.event.head_commit.timestamp }} \
            --status ${{ job.status }}
```

### Example 4: Matrix Builds

```yaml
name: Matrix Build

on: [push]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        build_type: [Debug, Release]

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Install InfraMind CLI
        run: pip install inframind-cli

      - name: Get Optimization
        id: optimize
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          inframind optimize \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --build-type ${{ matrix.build_type }} \
            --format env >> $GITHUB_ENV

      - name: Build
        run: |
          cmake -S . -B build -DCMAKE_BUILD_TYPE=${{ matrix.build_type }}
          cmake --build build --parallel ${{ env.INFRAMIND_CPU }}

      - name: Report Results
        if: always()
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          inframind report \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --duration ${{ github.event.head_commit.timestamp }} \
            --status ${{ job.status }}
```

---

## Using Reusable Workflows

Create a reusable workflow for InfraMind integration:

### `.github/workflows/inframind-optimize.yml`

```yaml
name: InfraMind Optimize

on:
  workflow_call:
    inputs:
      build_type:
        required: false
        type: string
        default: 'release'
    outputs:
      cpu:
        description: "Recommended CPU count"
        value: ${{ jobs.optimize.outputs.cpu }}
      memory:
        description: "Recommended memory (MB)"
        value: ${{ jobs.optimize.outputs.memory }}
      concurrency:
        description: "Recommended concurrency"
        value: ${{ jobs.optimize.outputs.concurrency }}

jobs:
  optimize:
    runs-on: ubuntu-latest
    outputs:
      cpu: ${{ steps.opt.outputs.cpu }}
      memory: ${{ steps.opt.outputs.memory }}
      concurrency: ${{ steps.opt.outputs.concurrency }}

    steps:
      - name: Install CLI
        run: pip install inframind-cli

      - name: Get Suggestions
        id: opt
        env:
          INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
          INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
        run: |
          OPTS=$(inframind optimize \
            --repo ${{ github.repository }} \
            --branch ${{ github.ref_name }} \
            --build-type ${{ inputs.build_type }} \
            --format json)

          echo "cpu=$(echo $OPTS | jq -r '.cpu')" >> $GITHUB_OUTPUT
          echo "memory=$(echo $OPTS | jq -r '.memory')" >> $GITHUB_OUTPUT
          echo "concurrency=$(echo $OPTS | jq -r '.concurrency')" >> $GITHUB_OUTPUT
```

### Use the reusable workflow:

```yaml
name: Build

on: [push]

jobs:
  optimize:
    uses: ./.github/workflows/inframind-optimize.yml
    secrets: inherit

  build:
    needs: optimize
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: make build -j${{ needs.optimize.outputs.cpu }}
```

---

## Best Practices

### 1. Cache the CLI Installation

```yaml
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'

- name: Install InfraMind CLI
  run: pip install inframind-cli
```

### 2. Handle API Failures Gracefully

```yaml
- name: Get Optimization
  id: optimize
  continue-on-error: true
  env:
    INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
    INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
  run: |
    inframind optimize --repo ${{ github.repository }} --branch ${{ github.ref_name }} --format env >> $GITHUB_ENV || echo "INFRAMIND_CPU=4" >> $GITHUB_ENV
```

### 3. Track Build Duration Accurately

```yaml
- name: Start Time
  id: start
  run: echo "start_time=$(date +%s)" >> $GITHUB_OUTPUT

- name: Build
  run: make build

- name: Report Results
  env:
    INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
    INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
  run: |
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - ${{ steps.start.outputs.start_time }}))

    inframind report \
      --repo ${{ github.repository }} \
      --branch ${{ github.ref_name }} \
      --duration $DURATION \
      --status ${{ job.status }}
```

### 4. Use Separate Jobs for Optimization and Building

```yaml
jobs:
  optimize:
    runs-on: ubuntu-latest
    outputs:
      cpu: ${{ steps.opt.outputs.cpu }}
      memory: ${{ steps.opt.outputs.memory }}
    steps:
      - name: Get Suggestions
        id: opt
        # ... optimization steps

  build:
    needs: optimize
    runs-on: ubuntu-latest
    steps:
      - name: Build
        run: make build -j${{ needs.optimize.outputs.cpu }}
```

---

## Troubleshooting

### Check API Connectivity

```yaml
- name: Test InfraMind API
  run: |
    curl -v ${{ secrets.INFRAMIND_URL }}/health
```

### Debug Suggestions

```yaml
- name: Debug
  env:
    INFRAMIND_URL: ${{ secrets.INFRAMIND_URL }}
    INFRAMIND_API_KEY: ${{ secrets.INFRAMIND_API_KEY }}
  run: |
    inframind optimize --repo ${{ github.repository }} --branch ${{ github.ref_name }} --format json
```

---

## Next Steps

- [View API Reference](../api.md)
- [Learn about ML Models](../ml.md)
- [GitLab CI Integration](./gitlab-ci.md)
