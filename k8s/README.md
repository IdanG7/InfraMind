# Kubernetes Deployment Guide

This directory contains production-ready Kubernetes manifests for deploying InfraMind.

## 📋 Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` configured with cluster access
- Storage class that supports `ReadWriteOnce` and `ReadWriteMany` access modes
- Ingress controller (nginx recommended)
- cert-manager for TLS certificates (optional but recommended)
- Metrics server for HPA

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ingress (HTTPS)                           │
│  api.inframind.yourdomain.com │ grafana.inframind.yourdomain.com│
└────────┬────────────────────────┬────────────────────────────────┘
         │                        │
    ┌────▼────────┐         ┌────▼──────┐
    │ InfraMind   │         │  Grafana  │
    │ API (x3)    │◄────────┤           │
    └─┬─┬─────┬──┘          └────┬──────┘
      │ │     │                  │
      │ │     └─────────┐        │
      │ │               │        │
┌─────▼─▼──┐    ┌──────▼──┐ ┌───▼──────┐
│PostgreSQL │    │  Redis  │ │Prometheus│
│(StatefulSet)   │(StatefulSet) (Deployment)
└───────────┘    └─────────┘ └──────────┘

DaemonSet: InfraMind Agent (on all nodes)
```

## 📁 Files

| File | Description |
|------|-------------|
| `namespace.yaml` | Creates `infra` namespace |
| `secrets.example.yaml` | Template for secrets (DO NOT commit actual secrets!) |
| `api-deployment.yaml` | API deployment with HPA and PDB |
| `postgres-statefulset.yaml` | PostgreSQL with exporters and init scripts |
| `redis-deployment.yaml` | Redis StatefulSet with proper security |
| `agent-daemonset.yaml` | Telemetry agent DaemonSet with RBAC |
| `monitoring.yaml` | Prometheus and Grafana |
| `ingress.yaml` | Ingress with TLS and security headers |
| `network-policy.yaml` | Network policies for security |

## 🚀 Quick Start

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Create Secrets

```bash
# Copy the example secrets file
cp secrets.example.yaml secrets.yaml

# Generate secure passwords
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export API_KEY=$(openssl rand -hex 32)
export MINIO_ACCESS_KEY=$(openssl rand -hex 16)
export MINIO_SECRET_KEY=$(openssl rand -base64 32)
export GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Create the secret
kubectl create secret generic inframind-secrets \
  --namespace=infra \
  --from-literal=api-key=$API_KEY \
  --from-literal=postgres-password=$POSTGRES_PASSWORD \
  --from-literal=database-url="postgresql://inframind:$POSTGRES_PASSWORD@postgres.infra.svc.cluster.local:5432/inframind" \
  --from-literal=postgres-exporter-dsn="postgresql://inframind:$POSTGRES_PASSWORD@localhost:5432/inframind?sslmode=disable" \
  --from-literal=redis-password=$REDIS_PASSWORD \
  --from-literal=redis-url="redis://:$REDIS_PASSWORD@redis.infra.svc.cluster.local:6379/0" \
  --from-literal=minio-access-key=$MINIO_ACCESS_KEY \
  --from-literal=minio-secret-key=$MINIO_SECRET_KEY \
  --from-literal=grafana-admin-password=$GRAFANA_PASSWORD

# Save credentials securely!
cat > .inframind-credentials << EOF
API Key: $API_KEY
Postgres Password: $POSTGRES_PASSWORD
Redis Password: $REDIS_PASSWORD
MinIO Access Key: $MINIO_ACCESS_KEY
MinIO Secret Key: $MINIO_SECRET_KEY
Grafana Admin Password: $GRAFANA_PASSWORD
EOF

echo "Credentials saved to .inframind-credentials - KEEP THIS SECURE!"
```

### 3. Deploy Infrastructure

```bash
# Deploy in order:
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f minio-deployment.yaml  # If using MinIO

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n infra --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n infra --timeout=300s
```

### 4. Deploy API and Agent

```bash
kubectl apply -f api-deployment.yaml
kubectl apply -f agent-daemonset.yaml

# Wait for API to be ready
kubectl wait --for=condition=ready pod -l app=inframind-api -n infra --timeout=300s
```

### 5. Deploy Monitoring

```bash
kubectl apply -f monitoring.yaml

# Wait for Grafana to be ready
kubectl wait --for=condition=ready pod -l app=grafana -n infra --timeout=300s
```

### 6. Deploy Ingress

**Update domain names in `ingress.yaml` first!**

```bash
# Edit ingress.yaml and replace 'yourdomain.com' with your actual domain
sed -i 's/yourdomain.com/example.com/g' ingress.yaml

# Apply ingress
kubectl apply -f ingress.yaml
```

### 7. Apply Network Policies (Optional but Recommended)

```bash
kubectl apply -f network-policy.yaml
```

## ✅ Verification

### Check All Pods

```bash
kubectl get pods -n infra
```

Expected output:
```
NAME                              READY   STATUS    RESTARTS   AGE
inframind-api-xxxxx-xxxxx         1/1     Running   0          5m
inframind-api-xxxxx-xxxxx         1/1     Running   0          5m
inframind-api-xxxxx-xxxxx         1/1     Running   0          5m
inframind-agent-xxxxx             1/1     Running   0          5m
postgres-0                        2/2     Running   0          10m
redis-0                           2/2     Running   0          10m
prometheus-xxxxx-xxxxx            1/1     Running   0          5m
grafana-xxxxx-xxxxx               1/1     Running   0          5m
```

### Check Services

```bash
kubectl get svc -n infra
```

### Check Ingress

```bash
kubectl get ingress -n infra
```

### Test API Health

```bash
# Port-forward if ingress not set up yet
kubectl port-forward -n infra svc/inframind-api 8080:8080

# Test in another terminal
curl http://localhost:8080/health
```

## 🔒 Security Checklist

- [ ] All secrets created and stored securely
- [ ] TLS certificates configured (cert-manager)
- [ ] Network policies applied
- [ ] Pod security contexts configured (already in manifests)
- [ ] RBAC for agent configured (already in agent-daemonset.yaml)
- [ ] Image pull secrets configured (if using private registry)
- [ ] Ingress rate limiting configured
- [ ] Resource quotas set
- [ ] Backup strategy in place for StatefulSets

## 📊 Monitoring

### Access Grafana

```bash
# Get Grafana password
kubectl get secret inframind-secrets -n infra -o jsonpath='{.data.grafana-admin-password}' | base64 -d

# Port-forward
kubectl port-forward -n infra svc/grafana-service 3000:3000

# Open http://localhost:3000
# Username: admin
# Password: (from above)
```

### Access Prometheus

```bash
kubectl port-forward -n infra svc/prometheus-service 9090:9090
# Open http://localhost:9090
```

## 🔧 Scaling

### Manual Scaling

```bash
# Scale API
kubectl scale deployment inframind-api -n infra --replicas=5

# HPA will auto-scale based on CPU/memory
kubectl get hpa -n infra
```

### Adjust HPA

Edit `api-deployment.yaml` and modify HPA settings:
```yaml
minReplicas: 3
maxReplicas: 10
```

## 🔄 Updates

### Rolling Update

```bash
# Update API image
kubectl set image deployment/inframind-api api=ghcr.io/yourusername/inframind/api:v0.2.0 -n infra

# Check rollout status
kubectl rollout status deployment/inframind-api -n infra

# Rollback if needed
kubectl rollout undo deployment/inframind-api -n infra
```

## 💾 Backup

### PostgreSQL Backup

```bash
# Manual backup
kubectl exec -n infra postgres-0 -- pg_dump -U inframind inframind > backup-$(date +%Y%m%d).sql

# Automated backups (use Velero or similar)
velero backup create inframind-backup --include-namespaces infra
```

### Restore

```bash
# Restore from backup
kubectl exec -i -n infra postgres-0 -- psql -U inframind inframind < backup-20240101.sql
```

## 🐛 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n infra

# Check logs
kubectl logs <pod-name> -n infra

# Check events
kubectl get events -n infra --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
kubectl exec -it -n infra postgres-0 -- psql -U inframind

# Test Redis connection
kubectl exec -it -n infra redis-0 -- redis-cli -a $REDIS_PASSWORD ping
```

### Network Policy Issues

```bash
# Temporarily disable network policies for debugging
kubectl delete networkpolicies --all -n infra

# Re-apply after fixing
kubectl apply -f network-policy.yaml
```

## 🔥 Production Hardening

### 1. Resource Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: infra-quota
  namespace: infra
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"
```

### 2. Pod Security Standards

```bash
kubectl label namespace infra \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted
```

### 3. Image Pull Secrets

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n infra

# Add to deployments:
# imagePullSecrets:
# - name: ghcr-secret
```

## 📚 Additional Resources

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)

## 🆘 Support

For issues or questions:
- GitHub Issues: https://github.com/yourorg/inframind/issues
- Documentation: ../docs/
