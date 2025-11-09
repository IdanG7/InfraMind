# Jenkins Integration Guide

This guide shows how to integrate InfraMind with Jenkins pipelines.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Option 1: Using the CLI Tool](#option-1-using-the-cli-tool)
- [Option 2: Using Direct API Calls](#option-2-using-direct-api-calls)
- [Option 3: Using the Shared Library](#option-3-using-the-shared-library)
- [Complete Examples](#complete-examples)

---

## Prerequisites

1. InfraMind API running and accessible from Jenkins agents
2. Jenkins pipeline with scripted or declarative syntax
3. Either:
   - Python 3.8+ available on Jenkins agents (for CLI method)
   - `curl` and `jq` available (for API method)
   - Access to install Jenkins Shared Library (for library method)

---

## Option 1: Using the CLI Tool

### Installation

Add this to your pipeline to install the CLI:

```groovy
stage('Setup') {
  steps {
    sh 'pip install inframind-cli'
  }
}
```

### Full Pipeline Example

```groovy
pipeline {
  agent any

  environment {
    INFRAMIND_URL = 'http://inframind-api.infra.svc.cluster.local:8081'
    INFRAMIND_API_KEY = credentials('inframind-api-key')
  }

  stages {
    stage('Setup') {
      steps {
        sh 'pip install inframind-cli'
      }
    }

    stage('Optimize') {
      steps {
        script {
          // Get optimization suggestions and export as environment variables
          sh '''
            inframind optimize \
              --repo ${GIT_URL} \
              --branch ${BRANCH_NAME} \
              --format env > opts.env
            source opts.env
          '''

          // Load into Jenkins environment
          def opts = readFile('opts.env').split('\n')
          opts.each { line ->
            if (line.startsWith('export ')) {
              def parts = line.replace('export ', '').split('=')
              env."${parts[0]}" = parts[1]
            }
          }
        }
      }
    }

    stage('Build') {
      steps {
        sh '''
          echo "Building with ${INFRAMIND_CPU} CPUs and ${INFRAMIND_MEMORY}MB memory"
          make build -j${INFRAMIND_CPU}
        '''
      }
    }

    stage('Test') {
      steps {
        sh 'make test'
      }
    }
  }

  post {
    always {
      script {
        def duration = currentBuild.duration / 1000 // Convert to seconds
        def status = currentBuild.result == 'SUCCESS' ? 'success' : 'failure'

        sh """
          inframind report \
            --repo ${GIT_URL} \
            --branch ${BRANCH_NAME} \
            --duration ${duration} \
            --status ${status} \
            --cpu \${INFRAMIND_CPU} \
            --memory \${INFRAMIND_MEMORY}
        """
      }
    }
  }
}
```

---

## Option 2: Using Direct API Calls

### Full Pipeline Example

```groovy
pipeline {
  agent any

  environment {
    INFRAMIND_URL = 'http://inframind-api.infra.svc.cluster.local:8081'
    INFRAMIND_API_KEY = credentials('inframind-api-key')
  }

  stages {
    stage('Optimize') {
      steps {
        script {
          // Call InfraMind API to get suggestions
          def response = sh(
            script: """
              curl -sf -X POST ${INFRAMIND_URL}/optimize \
                -H 'Content-Type: application/json' \
                -H 'X-API-Key: ${INFRAMIND_API_KEY}' \
                -d '{
                  "repo": "${env.GIT_URL}",
                  "branch": "${env.BRANCH_NAME}",
                  "build_type": "release"
                }'
            """,
            returnStdout: true
          ).trim()

          // Parse JSON response
          def opts = readJSON text: response

          // Set environment variables
          env.BUILD_CPU = opts.cpu
          env.BUILD_MEMORY = opts.memory
          env.BUILD_CONCURRENCY = opts.concurrency
          env.CACHE_ENABLED = opts.cache_enabled

          echo "InfraMind suggests: CPU=${opts.cpu}, Memory=${opts.memory}MB"
          echo "Rationale: ${opts.rationale}"
        }
      }
    }

    stage('Build') {
      steps {
        sh 'make build -j${BUILD_CPU}'
      }
    }
  }

  post {
    always {
      script {
        def duration = currentBuild.duration / 1000
        def status = currentBuild.result == 'SUCCESS' ? 'success' : 'failure'

        sh """
          curl -sf -X POST ${INFRAMIND_URL}/builds/complete \
            -H 'Content-Type: application/json' \
            -H 'X-API-Key: ${INFRAMIND_API_KEY}' \
            -d '{
              "repo": "${env.GIT_URL}",
              "branch": "${env.BRANCH_NAME}",
              "duration": ${duration},
              "status": "${status}",
              "cpu": ${env.BUILD_CPU},
              "memory": ${env.BUILD_MEMORY}
            }'
        """
      }
    }
  }
}
```

---

## Option 3: Using the Shared Library

### Install the Shared Library

1. Add the InfraMind repository as a Global Pipeline Library in Jenkins:
   - Go to: Manage Jenkins → Configure System → Global Pipeline Libraries
   - Add Library:
     - Name: `inframind`
     - Default version: `main`
     - Retrieval method: Modern SCM → Git
     - Project Repository: `https://github.com/yourorg/inframind.git`
     - Library Path: `services/jenkins-shared-lib`

### Full Pipeline Example

```groovy
@Library('inframind') _

pipeline {
  agent any

  environment {
    INFRAMIND_API_URL = 'http://inframind-api.infra.svc.cluster.local:8081'
  }

  stages {
    stage('Optimize') {
      steps {
        inframindOptimize(
          params: [
            tool: 'cmake',
            repo: env.GIT_URL,
            branch: env.BRANCH_NAME
          ]
        )
      }
    }

    stage('Build') {
      steps {
        inframindStage(name: 'compile') {
          sh 'cmake -S . -B build'
          sh 'cmake --build build -j${INFRAMIND_CPU}'
        }
      }
    }

    stage('Test') {
      steps {
        inframindStage(name: 'test') {
          sh 'ctest --test-dir build'
        }
      }
    }
  }

  post {
    always {
      inframindNotify()
    }
  }
}
```

---

## Complete Examples

### Example 1: C++ Project with CMake

```groovy
pipeline {
  agent {
    kubernetes {
      yaml '''
        apiVersion: v1
        kind: Pod
        spec:
          containers:
          - name: builder
            image: gcc:11
            command: ['cat']
            tty: true
      '''
    }
  }

  environment {
    INFRAMIND_URL = 'http://inframind-api.infra.svc.cluster.local:8081'
    INFRAMIND_API_KEY = credentials('inframind-api-key')
  }

  stages {
    stage('Setup') {
      steps {
        container('builder') {
          sh 'pip install inframind-cli'
        }
      }
    }

    stage('Optimize') {
      steps {
        container('builder') {
          script {
            sh 'inframind optimize --repo ${GIT_URL} --branch ${BRANCH_NAME} --format env > opts.env'
            load 'opts.env'
          }
        }
      }
    }

    stage('Build') {
      steps {
        container('builder') {
          sh '''
            cmake -S . -B build \
              -DCMAKE_BUILD_TYPE=Release \
              -DCMAKE_C_COMPILER_LAUNCHER=ccache \
              -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
            cmake --build build -j${INFRAMIND_CPU}
          '''
        }
      }
    }

    stage('Test') {
      steps {
        container('builder') {
          sh 'ctest --test-dir build --parallel ${INFRAMIND_CONCURRENCY}'
        }
      }
    }
  }

  post {
    always {
      container('builder') {
        script {
          def duration = currentBuild.duration / 1000
          def status = currentBuild.result == 'SUCCESS' ? 'success' : 'failure'

          sh """
            inframind report \
              --repo ${GIT_URL} \
              --branch ${BRANCH_NAME} \
              --duration ${duration} \
              --status ${status}
          """
        }
      }
    }
  }
}
```

### Example 2: Docker Build Optimization

```groovy
pipeline {
  agent any

  environment {
    INFRAMIND_URL = 'http://inframind-api.infra.svc.cluster.local:8081'
    INFRAMIND_API_KEY = credentials('inframind-api-key')
  }

  stages {
    stage('Optimize') {
      steps {
        script {
          def opts = sh(
            script: """
              curl -sf -X POST ${INFRAMIND_URL}/optimize \
                -H 'Content-Type: application/json' \
                -H 'X-API-Key: ${INFRAMIND_API_KEY}' \
                -d '{"repo":"${GIT_URL}","branch":"${BRANCH_NAME}"}'
            """,
            returnStdout: true
          )

          def suggestions = readJSON text: opts
          env.BUILD_CPUS = suggestions.cpu
          env.BUILD_MEMORY = suggestions.memory
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        sh """
          docker build \
            --cpus=${BUILD_CPUS} \
            --memory=${BUILD_MEMORY}m \
            --build-arg JOBS=${BUILD_CPUS} \
            -t myapp:${BUILD_NUMBER} .
        """
      }
    }

    stage('Push') {
      steps {
        sh 'docker push myapp:${BUILD_NUMBER}'
      }
    }
  }

  post {
    always {
      script {
        def duration = currentBuild.duration / 1000
        def status = currentBuild.result == 'SUCCESS' ? 'success' : 'failure'

        sh """
          curl -sf -X POST ${INFRAMIND_URL}/builds/complete \
            -H 'Content-Type: application/json' \
            -H 'X-API-Key: ${INFRAMIND_API_KEY}' \
            -d '{
              "repo": "${GIT_URL}",
              "branch": "${BRANCH_NAME}",
              "duration": ${duration},
              "status": "${status}",
              "cpu": ${BUILD_CPUS},
              "memory": ${BUILD_MEMORY}
            }'
        """
      }
    }
  }
}
```

---

## Configuration

### Storing API Credentials

Store the InfraMind API key as a Jenkins credential:

1. Go to: Manage Jenkins → Manage Credentials
2. Add Credentials:
   - Kind: Secret text
   - Secret: Your API key
   - ID: `inframind-api-key`
   - Description: InfraMind API Key

### Network Access

Ensure Jenkins agents can reach the InfraMind API:

- **Same Kubernetes cluster**: Use service name `http://inframind-api.infra.svc.cluster.local:8081`
- **External**: Use external URL `http://inframind.example.com:8081`
- **Firewall**: Ensure port 8081 is accessible

---

## Troubleshooting

### API Connection Issues

```groovy
stage('Debug') {
  steps {
    sh 'curl -v ${INFRAMIND_URL}/health'
  }
}
```

### Check Suggestions

```groovy
stage('Optimize') {
  steps {
    script {
      def opts = sh(script: "inframind optimize --repo ${GIT_URL} --branch ${BRANCH_NAME} --format json", returnStdout: true)
      echo "Suggestions: ${opts}"
    }
  }
}
```

### Verify Environment Variables

```groovy
stage('Build') {
  steps {
    sh 'env | grep INFRAMIND'
  }
}
```

---

## Best Practices

1. **Cache the CLI**: Install `inframind-cli` once and cache it
2. **Error Handling**: Add fallback values if API is unavailable
3. **Timeouts**: Set reasonable timeouts for API calls
4. **Logging**: Log optimization suggestions for debugging
5. **Metrics**: Track build time improvements over time

---

## Next Steps

- [View API Reference](../api.md)
- [Configure Grafana Dashboards](../deployment/production.md)
- [Learn about ML Models](../ml.md)
