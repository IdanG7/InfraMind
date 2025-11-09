# GitHub Deployment Guide - No Domain Needed

**This guide shows you how to commit safely and deploy without a domain.**

---

## ✅ Safe to Commit to GitHub

Your `.gitignore` is already configured to protect secrets. Here's what's safe:

### What WILL Be Committed (Safe ✅)
- All code files
- Kubernetes manifests templates
- `k8s/secrets.yaml.example` (template - no real secrets)
- `.env.example` (template - no real secrets)
- `.env.production` (template - no real secrets)
- All documentation
- Docker Compose configuration

### What WON'T Be Committed (Protected ❌)
- `.env` (your real secrets) - **Protected by .gitignore**
- `k8s/secrets.yaml` (your real secrets) - **Protected by .gitignore**

---

## 🚀 How to Commit Everything to GitHub

### Step 1: Verify Secrets Are Protected

```bash
# Check what Git sees
git status

# Make sure these files are NOT listed:
# - .env
# - k8s/secrets.yaml

# If they appear, they're protected by .gitignore ✅
```

### Step 2: Commit Everything

```bash
# Add all files
git add .

# Commit
git commit -m "Add production-ready Kubernetes deployment and configuration

- Added complete K8s manifests for API, database, monitoring
- Generated production secrets and configuration
- Added comprehensive deployment documentation
- Created Grafana dashboards for monitoring
- Set up CI/CD workflows for automated deployment
- Phase 1 complete: Production ready"

# Push to GitHub
git push origin main
```

**That's it!** Your secrets are safe because:
- `.gitignore` excludes `.env`
- `.gitignore` excludes `secrets.yaml`

---

## 🏠 Deployment Option 1: Docker Compose (Easiest - No Domain Needed)

**Perfect for:**
- Local development
- Testing
- Internal company use
- No Kubernetes required
- No domain needed

### Deploy Now:

```bash
# You already have .env with production secrets!
# Just restart to use them:
docker-compose down
docker-compose up -d

# Wait 30 seconds for services to start
sleep 30

# Verify everything is running
docker-compose ps

# Should show all services as "Up" or "healthy"
```

### Access Your Services:

```
✅ API:        http://localhost:8081
✅ API Docs:   http://localhost:8081/docs
✅ Grafana:    http://localhost:3001 (admin / SroXZL0f0O05Rrgmiu3KHQ==)
✅ Prometheus: http://localhost:9091
```

### Test API:

```bash
curl -X POST http://localhost:8081/optimize \
  -H "Content-Type: application/json" \
  -H "X-IM-Token: 52bed4a8e5b3c73c30bd8e28a11dd4c9a283ce97ee392dc673ae0d249fe8445d" \
  -d '{
    "pipeline": "test/pipeline",
    "context": {
      "tool": "cmake",
      "max_rss_gb": 4.0,
      "num_steps": 5
    }
  }'
```

**Done!** InfraMind is running locally with production-grade security.

---

## ☸️ Deployment Option 2: Kubernetes Without Domain

**Perfect for:**
- Cloud deployment
- Scalability
- High availability
- Still no domain needed!

### Step 1: Set Up Kubernetes Cluster

Choose one:

**Google Cloud (GKE):**
```bash
gcloud container clusters create inframind \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4

gcloud container clusters get-credentials inframind --zone us-central1-a
```

**AWS (EKS):**
```bash
eksctl create cluster \
  --name inframind \
  --region us-east-1 \
  --nodegroup-name workers \
  --node-type t3.xlarge \
  --nodes 3

aws eks update-kubeconfig --name inframind --region us-east-1
```

**Azure (AKS):**
```bash
az group create --name inframind-rg --location eastus

az aks create \
  --resource-group inframind-rg \
  --name inframind \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3

az aks get-credentials --resource-group inframind-rg --name inframind
```

### Step 2: Deploy to Kubernetes

```bash
# Create namespace and apply secrets
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy infrastructure
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/minio-deployment.yaml

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n infra --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n infra --timeout=180s
kubectl wait --for=condition=ready pod -l app=minio -n infra --timeout=180s

# Deploy application
kubectl apply -f k8s/api-deployment.yaml

# Create ConfigMaps for monitoring
kubectl create configmap prometheus-config \
  --from-file=observability/prometheus.yml \
  -n infra

kubectl create configmap grafana-dashboards \
  --from-file=observability/grafana_dashboards/ \
  -n infra

kubectl create configmap grafana-datasources \
  --from-file=observability/grafana_datasources.yml \
  -n infra

# Deploy monitoring
kubectl apply -f k8s/monitoring.yaml

# DON'T apply ingress (no domain needed)
# Skip: kubectl apply -f k8s/ingress.yaml
```

### Step 3: Access Services (Port Forwarding)

```bash
# API
kubectl port-forward -n infra svc/inframind-api 8080:8080 &

# Grafana
kubectl port-forward -n infra svc/grafana-service 3000:3000 &

# Prometheus (optional)
kubectl port-forward -n infra svc/prometheus-service 9090:9090 &
```

### Step 4: Test

```
✅ API:        http://localhost:8080
✅ API Docs:   http://localhost:8080/docs
✅ Grafana:    http://localhost:3000 (admin / SroXZL0f0O05Rrgmiu3KHQ==)
✅ Prometheus: http://localhost:9090
```

**Test API:**
```bash
curl -X POST http://localhost:8080/optimize \
  -H "Content-Type: application/json" \
  -H "X-IM-Token: 52bed4a8e5b3c73c30bd8e28a11dd4c9a283ce97ee392dc673ae0d249fe8445d" \
  -d '{"pipeline":"test","context":{"tool":"cmake","max_rss_gb":4}}'
```

---

## 🌐 Future: When You Want a Domain

### Why You Might Want One:
- Public internet access
- Clean URLs (api.yourcompany.com)
- Automatic HTTPS/SSL
- Easier team access

### Steps When Ready:

1. **Buy a domain** ($10-15/year):
   - Namecheap: https://www.namecheap.com
   - Google Domains: https://domains.google
   - Cloudflare: https://www.cloudflare.com

2. **Update ingress**:
   ```bash
   # Edit k8s/ingress.yaml
   # Replace "yourdomain.com" with your actual domain

   # Apply ingress
   kubectl apply -f k8s/ingress.yaml
   ```

3. **Point DNS**:
   ```bash
   # Get ingress IP
   kubectl get ingress -n infra

   # Create DNS A records:
   # api.inframind.yourdomain.com -> <INGRESS_IP>
   # grafana.inframind.yourdomain.com -> <INGRESS_IP>
   ```

4. **Access via domain**:
   ```
   https://api.inframind.yourdomain.com
   https://grafana.inframind.yourdomain.com
   ```

---

## 🔑 Your Secrets Reference

**Store these somewhere safe (NOT in GitHub):**

```
API Key:               52bed4a8e5b3c73c30bd8e28a11dd4c9a283ce97ee392dc673ae0d249fe8445d
PostgreSQL Password:   kZTqFe1LmeMKJuSIz96XgmU+uM1vgW7Uq3ns9snRFhQ=
MinIO Secret:          Pi3nhLQuToqcYrqkzGUKjm5RIaSwDYZkOE10SsXDWQo=
Grafana Password:      SroXZL0f0O05Rrgmiu3KHQ==
Redis Password:        QtT8lmiUHKkcvzXvZC3LUQ==
```

---

## 📋 Quick Decision Guide

**Choose Docker Compose if:**
- ✅ You want to test locally first
- ✅ You're not familiar with Kubernetes
- ✅ It's for internal/development use
- ✅ You want the quickest setup (5 minutes)

**Choose Kubernetes if:**
- ✅ You want cloud deployment
- ✅ You need high availability (3 API replicas)
- ✅ You want auto-scaling
- ✅ You're planning production use
- ✅ You want to use the full infrastructure

**Both options work great!** Start with Docker Compose, move to Kubernetes when ready.

---

## ✅ What You Should Do Right Now

### Step 1: Commit to GitHub
```bash
git add .
git commit -m "Add production-ready deployment configuration"
git push origin main
```

### Step 2: Choose Deployment Method

**Option A - Quick Test (5 minutes):**
```bash
docker-compose down
docker-compose up -d
# Visit: http://localhost:8081/docs
```

**Option B - Kubernetes (30 minutes):**
```bash
# Set up K8s cluster, then:
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/minio-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
# Access via port forwarding
```

### Step 3: Start Using It!

Test with real build data:
```bash
# Use your CI/CD to start sending build data to InfraMind
# Or seed demo data:
cd services/api
python app/scripts/seed_demo.py
```

---

## 🎯 Summary

**You have everything you need right now:**
- ✅ Production secrets generated
- ✅ Safe to commit to GitHub (.gitignore protects secrets)
- ✅ Can deploy locally with Docker Compose
- ✅ Can deploy to Kubernetes without a domain
- ✅ Domain only needed for public internet access

**Next step:** Just commit to GitHub and start using it!

**Questions?**
- Docker Compose issues: Check `docker-compose logs`
- Kubernetes issues: Check `kubectl get pods -n infra`
- API not responding: Check logs with `docker-compose logs api` or `kubectl logs -n infra -l app=inframind-api`

---

**Last Updated**: October 25, 2025
**Status**: Ready to commit and deploy!
