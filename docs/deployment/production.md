# InfraMind - Production Deployment Guide

**Status**: ✅ Ready for Production Deployment
**Date**: October 25, 2025
**Version**: 0.1.0

---

## 🎉 You're Production Ready!

All secrets have been generated and all Kubernetes manifests are configured. Here's your complete deployment guide.

---

## 📋 Pre-Deployment Checklist

### ✅ Already Complete

- [x] Production secrets generated
- [x] `.env` file created with real secrets
- [x] Kubernetes manifests created (8 files)
- [x] Docker images buildable
- [x] CI/CD pipelines configured
- [x] Monitoring dashboards created
- [x] Integration tests written

### 🔧 What You Need

- [ ] Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- [ ] kubectl installed and configured
- [ ] Domain name (for Ingress)
- [ ] SSL certificates (or cert-manager)
- [ ] Container registry access (GitHub Container Registry configured)

---

## 🚀 Quick Deployment (Kubernetes)

### Option 1: Deploy Everything at Once

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply secrets
kubectl apply -f k8s/secrets.yaml

# 3. Deploy database and storage
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/minio-deployment.yaml

# 4. Wait for storage to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n infra --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n infra --timeout=300s
kubectl wait --for=condition=ready pod -l app=minio -n infra --timeout=300s

# 5. Deploy API
kubectl apply -f k8s/api-deployment.yaml

# 6. Deploy monitoring
kubectl apply -f k8s/monitoring.yaml

# 7. Set up ingress (update domain first!)
# Edit k8s/ingress.yaml with your domain
kubectl apply -f k8s/ingress.yaml

# 8. Verify deployment
kubectl get pods -n infra
kubectl get svc -n infra
```

### Option 2: Step-by-Step Deployment

Follow the detailed steps below for better control.

---

## 📖 Detailed Deployment Steps

### Step 1: Set Up Kubernetes Cluster

**For Google Cloud (GKE):**
```bash
# Create cluster
gcloud container clusters create inframind-prod \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10

# Get credentials
gcloud container clusters get-credentials inframind-prod --zone us-central1-a
```

**For AWS (EKS):**
```bash
# Create cluster
eksctl create cluster \
  --name inframind-prod \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10

# Update kubeconfig
aws eks update-kubeconfig --name inframind-prod --region us-east-1
```

**For Azure (AKS):**
```bash
# Create resource group
az group create --name inframind-rg --location eastus

# Create cluster
az aks create \
  --resource-group inframind-rg \
  --name inframind-prod \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 10

# Get credentials
az aks get-credentials --resource-group inframind-rg --name inframind-prod
```

### Step 2: Verify kubectl Access

```bash
# Check connection
kubectl cluster-info

# Should show your cluster URL
```

### Step 3: Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml

# Verify
kubectl get namespace infra
```

### Step 4: Apply Secrets

```bash
# Apply the secrets
kubectl apply -f k8s/secrets.yaml

# Verify secrets are created
kubectl get secrets -n infra

# Should show:
# inframind-secrets
# inframind-monitoring
```

### Step 5: Deploy Database (PostgreSQL)

```bash
# Deploy PostgreSQL StatefulSet
kubectl apply -f k8s/postgres-statefulset.yaml

# Watch the deployment
kubectl get pods -n infra -w

# Wait for ready (Ctrl+C when ready)
kubectl wait --for=condition=ready pod -l app=postgres -n infra --timeout=300s

# Verify
kubectl logs -n infra -l app=postgres --tail=50
```

### Step 6: Deploy Redis

```bash
# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=redis -n infra --timeout=180s

# Test Redis
kubectl exec -n infra -it $(kubectl get pod -n infra -l app=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli -a QtT8lmiUHKkcvzXvZC3LUQ== ping
# Should return: PONG
```

### Step 7: Deploy MinIO (Object Storage)

```bash
# Deploy MinIO
kubectl apply -f k8s/minio-deployment.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=minio -n infra --timeout=180s

# Verify
kubectl logs -n infra -l app=minio --tail=20
```

### Step 8: Initialize Database Schema

```bash
# Get API pod name (we'll use it to run migrations)
API_POD=$(kubectl get pod -n infra -l app=inframind-api -o jsonpath='{.items[0].metadata.name}')

# Run database migrations (once API is deployed in next step)
# kubectl exec -n infra $API_POD -- alembic upgrade head
```

### Step 9: Deploy API

```bash
# First, build and push Docker image
docker build -t ghcr.io/yourusername/inframind/api:latest ./services/api
docker push ghcr.io/yourusername/inframind/api:latest

# Or use GitHub Actions to build automatically (recommended)

# Deploy API
kubectl apply -f k8s/api-deployment.yaml

# Watch deployment
kubectl get pods -n infra -w

# Wait for all replicas to be ready
kubectl wait --for=condition=ready pod -l app=inframind-api -n infra --timeout=300s

# Check logs
kubectl logs -n infra -l app=inframind-api --tail=50
```

### Step 10: Deploy Monitoring

```bash
# First, create ConfigMaps for Prometheus and Grafana
kubectl create configmap prometheus-config \
  --from-file=observability/prometheus.yml \
  -n infra

kubectl create configmap grafana-dashboards \
  --from-file=observability/grafana_dashboards/ \
  -n infra

kubectl create configmap grafana-datasources \
  --from-file=observability/grafana_datasources.yml \
  -n infra

# Deploy monitoring stack
kubectl apply -f k8s/monitoring.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=prometheus -n infra --timeout=180s
kubectl wait --for=condition=ready pod -l app=grafana -n infra --timeout=180s
```

### Step 11: Set Up Ingress

**First, install NGINX Ingress Controller (if not already installed):**

```bash
# For GKE/Generic K8s
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# For AWS (EKS)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/aws/deploy.yaml

# Wait for external IP
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

**Install cert-manager for SSL (optional but recommended):**

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create Let's Encrypt issuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

**Update Ingress with your domain:**

```bash
# Edit k8s/ingress.yaml
# Replace 'yourdomain.com' with your actual domain

# Apply ingress
kubectl apply -f k8s/ingress.yaml

# Get external IP
kubectl get ingress -n infra
```

**Point your DNS to the ingress IP:**

```
A record: api.inframind.yourdomain.com → <INGRESS_IP>
A record: grafana.inframind.yourdomain.com → <INGRESS_IP>
```

### Step 12: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n infra

# All should be Running/Completed

# Check services
kubectl get svc -n infra

# Test API health
kubectl exec -n infra -it $(kubectl get pod -n infra -l app=inframind-api -o jsonpath='{.items[0].metadata.name}') -- curl -s http://localhost:8080/healthz

# Should return: {"status":"ok",...}
```

### Step 13: Test from Outside

```bash
# Wait for DNS propagation (5-30 minutes)

# Test API (replace with your domain)
curl https://api.inframind.yourdomain.com/healthz

# Access Grafana (replace with your domain)
# https://grafana.inframind.yourdomain.com
# Login: admin / SroXZL0f0O05Rrgmiu3KHQ==
```

---

## 🔐 Your Production Secrets

**IMPORTANT: Keep these secure!**

```
API Key: 52bed4a8e5b3c73c30bd8e28a11dd4c9a283ce97ee392dc673ae0d249fe8445d
PostgreSQL Password: kZTqFe1LmeMKJuSIz96XgmU+uM1vgW7Uq3ns9snRFhQ=
MinIO Secret Key: Pi3nhLQuToqcYrqkzGUKjm5RIaSwDYZkOE10SsXDWQo=
Grafana Admin Password: SroXZL0f0O05Rrgmiu3KHQ==
Redis Password: QtT8lmiUHKkcvzXvZC3LUQ==
```

**Store these in a password manager immediately!**

---

## 📊 Accessing Your Services

### Internal (within cluster):

- API: `http://inframind-api.infra.svc.cluster.local:8080`
- PostgreSQL: `postgres-service.infra.svc.cluster.local:5432`
- Redis: `redis-service.infra.svc.cluster.local:6379`
- MinIO: `minio-service.infra.svc.cluster.local:9000`
- Prometheus: `prometheus-service.infra.svc.cluster.local:9090`
- Grafana: `grafana-service.infra.svc.cluster.local:3000`

### External (via Ingress):

- API: `https://api.inframind.yourdomain.com`
- Grafana: `https://grafana.inframind.yourdomain.com`

### Port Forward (for testing):

```bash
# API
kubectl port-forward -n infra svc/inframind-api 8080:8080
# Access at: http://localhost:8080

# Grafana
kubectl port-forward -n infra svc/grafana-service 3000:3000
# Access at: http://localhost:3000

# Prometheus
kubectl port-forward -n infra svc/prometheus-service 9090:9090
# Access at: http://localhost:9090
```

---

## 🔄 CI/CD Deployment (Automated)

### Set Up GitHub Secrets

```bash
# Get your kubeconfig
kubectl config view --flatten > kubeconfig.yaml

# Encode it
cat kubeconfig.yaml | base64

# Add to GitHub Secrets:
# Go to: Settings → Secrets and variables → Actions
# Add: KUBECONFIG_PRODUCTION = <base64 output>
```

### Trigger Deployment

**Automatic on tag:**
```bash
git tag v0.1.0
git push origin v0.1.0

# GitHub Actions will automatically:
# 1. Build Docker images
# 2. Push to ghcr.io
# 3. Deploy to production
# 4. Run smoke tests
```

**Manual deployment:**
```bash
# Go to: Actions → Deploy → Run workflow
# Select: production
# Click: Run workflow
```

---

## 📈 Post-Deployment Tasks

### 1. Seed Demo Data (Optional)

```bash
# Port forward to API
kubectl port-forward -n infra svc/inframind-api 8080:8080 &

# Run seed script
cd services/api
python app/scripts/seed_demo.py

# Kill port forward
fg
# Press Ctrl+C
```

### 2. Configure Monitoring Alerts

Edit `.env` and add:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PAGERDUTY_KEY=your-pagerduty-key
```

Update the secret:
```bash
kubectl create secret generic inframind-monitoring \
  --from-literal=slack-webhook-url="YOUR_SLACK_WEBHOOK" \
  --from-literal=pagerduty-key="YOUR_PAGERDUTY_KEY" \
  -n infra \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Set Up Backups

**PostgreSQL Backup:**
```bash
# Create backup CronJob
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: infra
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16-alpine
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: inframind-secrets
                  key: postgres-password
            command:
            - sh
            - -c
            - pg_dump -h postgres-service -U inframind inframind > /backup/db-\$(date +%Y%m%d-%H%M%S).sql
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
EOF
```

### 4. Enable Horizontal Pod Autoscaling

```bash
# Create HPA for API
kubectl autoscale deployment inframind-api \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n infra

# Verify
kubectl get hpa -n infra
```

### 5. Set Up Monitoring Dashboards

1. Access Grafana: `https://grafana.inframind.yourdomain.com`
2. Login with admin / `SroXZL0f0O05Rrgmiu3KHQ==`
3. Dashboards should be auto-loaded from ConfigMap
4. Verify you see:
   - Pipelines Overview
   - ML Performance
   - System Metrics

---

## 🐛 Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n infra

# Describe problematic pod
kubectl describe pod <pod-name> -n infra

# Check logs
kubectl logs <pod-name> -n infra

# Common issues:
# - Image pull errors: Check registry credentials
# - CrashLoopBackOff: Check environment variables
# - Pending: Check resource availability
```

### Database connection issues

```bash
# Test PostgreSQL connection
kubectl exec -n infra -it $(kubectl get pod -n infra -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U inframind -d inframind -c "SELECT 1"

# Check database password
kubectl get secret inframind-secrets -n infra -o jsonpath='{.data.postgres-password}' | base64 -d
```

### API not responding

```bash
# Check API logs
kubectl logs -n infra -l app=inframind-api --tail=100

# Check health endpoint
kubectl exec -n infra $(kubectl get pod -n infra -l app=inframind-api -o jsonpath='{.items[0].metadata.name}') -- curl -s http://localhost:8080/healthz

# Restart API pods
kubectl rollout restart deployment/inframind-api -n infra
```

### Ingress not working

```bash
# Check ingress
kubectl get ingress -n infra
kubectl describe ingress inframind-ingress -n infra

# Check NGINX ingress logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Verify DNS
nslookup api.inframind.yourdomain.com
```

---

## 🎯 Success Metrics

After deployment, verify:

- [ ] All pods running (0 crashes)
- [ ] API health check returns 200
- [ ] Grafana accessible and dashboards loaded
- [ ] Can make API requests with API key
- [ ] Database persisting data
- [ ] Logs visible in kubectl logs
- [ ] Ingress routing traffic
- [ ] SSL certificates issued (if using cert-manager)

---

## 📞 Next Steps

1. **Integrate with your CI/CD**: Connect Jenkins/GitHub Actions
2. **Collect real data**: Start ingesting actual build runs
3. **Train ML model**: With real data (500+ runs recommended)
4. **Monitor performance**: Watch Grafana dashboards
5. **Set up alerts**: Configure Slack/PagerDuty
6. **Scale as needed**: Adjust replicas and resources

---

## 🎉 Congratulations!

You've successfully deployed InfraMind to production!

Your system is now:
- ✅ Running on Kubernetes
- ✅ Secured with real secrets
- ✅ Monitored with Grafana
- ✅ Auto-deploying via CI/CD
- ✅ Scalable and resilient

**Production URLs:**
- API: https://api.inframind.yourdomain.com
- Docs: https://api.inframind.yourdomain.com/docs
- Grafana: https://grafana.inframind.yourdomain.com

**Quick Test:**
```bash
curl -X POST https://api.inframind.yourdomain.com/optimize \
  -H "Content-Type: application/json" \
  -H "X-IM-Token: 52bed4a8e5b3c73c30bd8e28a11dd4c9a283ce97ee392dc673ae0d249fe8445d" \
  -d '{"pipeline":"test/pipeline","context":{"tool":"cmake","max_rss_gb":4}}'
```

---

**Last Updated**: October 25, 2025
**Support**: See CONTRIBUTING.md or open an issue
