# InfraMind Production Deployment Checklist

**Use this checklist when deploying to production**

---

## ✅ Pre-Deployment

### Infrastructure Setup
- [ ] Kubernetes cluster created (GKE/EKS/AKS)
- [ ] kubectl installed locally
- [ ] kubectl configured to access cluster
- [ ] Cluster has sufficient resources (3+ nodes, 4GB RAM each)
- [ ] Storage class available (check with `kubectl get storageclass`)

### Domain & DNS
- [ ] Domain name registered
- [ ] DNS provider accessible
- [ ] Subdomains planned:
  - [ ] `api.inframind.yourdomain.com`
  - [ ] `grafana.inframind.yourdomain.com`

### Secrets Management
- [ ] All secrets stored in password manager:
  - [ ] API Key: `52bed4a8e5b3c73c30bd8e28a11dd4c9a283ce97ee392dc673ae0d249fe8445d`
  - [ ] PostgreSQL Password: `kZTqFe1LmeMKJuSIz96XgmU+uM1vgW7Uq3ns9snRFhQ=`
  - [ ] MinIO Secret: `Pi3nhLQuToqcYrqkzGUKjm5RIaSwDYZkOE10SsXDWQo=`
  - [ ] Grafana Password: `SroXZL0f0O05Rrgmiu3KHQ==`
  - [ ] Redis Password: `QtT8lmiUHKkcvzXvZC3LUQ==`

### Files Review
- [ ] Reviewed `k8s/secrets.yaml` (secrets look correct)
- [ ] Updated `k8s/ingress.yaml` with your domain
- [ ] Updated `k8s/api-deployment.yaml` image registry
- [ ] Reviewed resource limits in all deployments

---

## 📦 Deployment Steps

### Step 1: Create Namespace
```bash
kubectl apply -f k8s/namespace.yaml
```
- [ ] Namespace created
- [ ] Verified: `kubectl get namespace infra`

### Step 2: Apply Secrets
```bash
kubectl apply -f k8s/secrets.yaml
```
- [ ] Secrets created
- [ ] Verified: `kubectl get secrets -n infra`
- [ ] Two secrets visible: `inframind-secrets`, `inframind-monitoring`

### Step 3: Deploy Database
```bash
kubectl apply -f k8s/postgres-statefulset.yaml
```
- [ ] StatefulSet created
- [ ] Wait for ready: `kubectl wait --for=condition=ready pod -l app=postgres -n infra --timeout=300s`
- [ ] Verified: `kubectl get pods -n infra -l app=postgres`
- [ ] Check logs: `kubectl logs -n infra -l app=postgres --tail=20`

### Step 4: Deploy Redis
```bash
kubectl apply -f k8s/redis-deployment.yaml
```
- [ ] Deployment created
- [ ] Wait for ready: `kubectl wait --for=condition=ready pod -l app=redis -n infra --timeout=180s`
- [ ] Test: `kubectl exec -n infra -it $(kubectl get pod -n infra -l app=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli -a QtT8lmiUHKkcvzXvZC3LUQ== ping`
- [ ] Returns: `PONG`

### Step 5: Deploy MinIO
```bash
kubectl apply -f k8s/minio-deployment.yaml
```
- [ ] Deployment created
- [ ] Wait for ready: `kubectl wait --for=condition=ready pod -l app=minio -n infra --timeout=180s`
- [ ] Verified: `kubectl get pods -n infra -l app=minio`

### Step 6: Deploy API
```bash
# First, ensure image is built and pushed
kubectl apply -f k8s/api-deployment.yaml
```
- [ ] Deployment created
- [ ] Wait for all replicas: `kubectl wait --for=condition=ready pod -l app=inframind-api -n infra --timeout=300s`
- [ ] 3 replicas running
- [ ] Health check: `kubectl exec -n infra $(kubectl get pod -n infra -l app=inframind-api -o jsonpath='{.items[0].metadata.name}') -- curl -s http://localhost:8080/healthz`
- [ ] Returns: `{"status":"ok",...}`

### Step 7: Deploy Monitoring

Create ConfigMaps first:
```bash
kubectl create configmap prometheus-config --from-file=observability/prometheus.yml -n infra
kubectl create configmap grafana-dashboards --from-file=observability/grafana_dashboards/ -n infra
kubectl create configmap grafana-datasources --from-file=observability/grafana_datasources.yml -n infra
```

Then deploy:
```bash
kubectl apply -f k8s/monitoring.yaml
```

- [ ] ConfigMaps created
- [ ] Deployments created
- [ ] Prometheus ready: `kubectl wait --for=condition=ready pod -l app=prometheus -n infra --timeout=180s`
- [ ] Grafana ready: `kubectl wait --for=condition=ready pod -l app=grafana -n infra --timeout=180s`

### Step 8: Install Ingress Controller

```bash
# For GKE/Generic
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

- [ ] NGINX Ingress installed
- [ ] Wait for external IP: `kubectl get svc -n ingress-nginx ingress-nginx-controller`
- [ ] External IP assigned (not `<pending>`)
- [ ] Note external IP: ___________________

### Step 9: Install cert-manager (SSL)

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

Create ClusterIssuer:
```bash
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # UPDATE THIS
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

- [ ] cert-manager installed
- [ ] ClusterIssuer created with YOUR email
- [ ] Verified: `kubectl get clusterissuer`

### Step 10: Update Ingress & Apply

Edit `k8s/ingress.yaml`:
- [ ] Replace `yourdomain.com` with your actual domain
- [ ] Verify email in cert-manager issuer above

```bash
kubectl apply -f k8s/ingress.yaml
```

- [ ] Ingress created
- [ ] Verified: `kubectl get ingress -n infra`
- [ ] TLS secret will be created by cert-manager (wait ~2 min)

### Step 11: Configure DNS

Point DNS A records to ingress IP:
- [ ] `api.inframind.yourdomain.com` → `<INGRESS_IP>`
- [ ] `grafana.inframind.yourdomain.com` → `<INGRESS_IP>`
- [ ] DNS propagation started (can take 5-30 minutes)

---

## ✅ Post-Deployment Verification

### Check All Pods Running
```bash
kubectl get pods -n infra
```
- [ ] All pods in `Running` state
- [ ] No `CrashLoopBackOff` or `Error` states
- [ ] API has 3 replicas running

### Check Services
```bash
kubectl get svc -n infra
```
- [ ] All services have ClusterIP assigned
- [ ] Services visible:
  - [ ] inframind-api
  - [ ] postgres-service
  - [ ] redis-service
  - [ ] minio-service
  - [ ] prometheus-service
  - [ ] grafana-service

### Check Storage
```bash
kubectl get pvc -n infra
```
- [ ] All PVCs in `Bound` state
- [ ] Storage allocated:
  - [ ] postgres-storage-postgres-0 (50Gi)
  - [ ] redis-pvc (10Gi)
  - [ ] minio-pvc (100Gi)
  - [ ] prometheus-pvc (50Gi)
  - [ ] grafana-pvc (10Gi)
  - [ ] inframind-models-pvc (10Gi)

### Test Internal Connectivity

```bash
# API health check
kubectl exec -n infra $(kubectl get pod -n infra -l app=inframind-api -o jsonpath='{.items[0].metadata.name}') -- curl -s http://localhost:8080/healthz

# Should return: {"status":"ok","version":"0.1.0",...}
```

- [ ] API health check passes
- [ ] Response contains `"status":"ok"`

### Wait for SSL Certificate

```bash
kubectl get certificate -n infra
```

- [ ] Certificate issued (status: `True`)
- [ ] May take 2-5 minutes
- [ ] If stuck, check: `kubectl describe certificate -n infra`

### Test External Access

Wait for DNS propagation, then:

```bash
# Test API
curl https://api.inframind.yourdomain.com/healthz

# Test Grafana
curl https://grafana.inframind.yourdomain.com/login
```

- [ ] API returns 200 OK
- [ ] Grafana login page loads
- [ ] SSL certificate valid (HTTPS works)

### Access Grafana

1. Visit: `https://grafana.inframind.yourdomain.com`
2. Login:
   - Username: `admin`
   - Password: `SroXZL0f0O05Rrgmiu3KHQ==`

- [ ] Grafana accessible
- [ ] Login successful
- [ ] Dashboards visible:
  - [ ] InfraMind - Pipelines Overview
  - [ ] InfraMind - ML Performance
  - [ ] InfraMind - System Metrics

### Test API with Request

```bash
curl -X POST https://api.inframind.yourdomain.com/optimize \
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

- [ ] Request succeeds (200 OK)
- [ ] Returns JSON with `suggestions`, `rationale`, `confidence`
- [ ] No authentication errors

---

## 🔧 Optional Configuration

### Enable Horizontal Pod Autoscaling

```bash
kubectl autoscale deployment inframind-api \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n infra
```

- [ ] HPA created
- [ ] Verified: `kubectl get hpa -n infra`

### Set Up Database Backups

- [ ] Created backup CronJob (see PRODUCTION_DEPLOYMENT.md)
- [ ] Tested backup manually
- [ ] Backup storage configured

### Configure Alerts

Update monitoring secret:
```bash
kubectl create secret generic inframind-monitoring \
  --from-literal=slack-webhook-url="YOUR_SLACK_WEBHOOK" \
  --from-literal=pagerduty-key="YOUR_PAGERDUTY_KEY" \
  -n infra \
  --dry-run=client -o yaml | kubectl apply -f -
```

- [ ] Slack webhook configured
- [ ] PagerDuty key configured
- [ ] Test alert sent

### Seed Demo Data (Optional)

```bash
kubectl port-forward -n infra svc/inframind-api 8080:8080 &
cd services/api
python app/scripts/seed_demo.py
```

- [ ] Demo data seeded
- [ ] 50 runs created
- [ ] ML model trained
- [ ] Visible in Grafana

---

## 📊 Monitoring Setup

### Grafana Dashboards

Access: `https://grafana.inframind.yourdomain.com`

- [ ] **Pipelines Overview** dashboard loaded
  - [ ] Build Duration Trend chart visible
  - [ ] Cache Hit Ratio showing
  - [ ] Success Rate stat visible

- [ ] **ML Performance** dashboard loaded
  - [ ] Model Prediction Accuracy chart visible
  - [ ] API Latency graph showing
  - [ ] Training Data Size stat visible

- [ ] **System Metrics** dashboard loaded
  - [ ] API Request Rate graph showing
  - [ ] Database Connections visible
  - [ ] Memory Usage chart active

### Prometheus

Port forward (for testing):
```bash
kubectl port-forward -n infra svc/prometheus-service 9090:9090
```

Visit: `http://localhost:9090`

- [ ] Prometheus accessible
- [ ] Targets up and healthy
- [ ] Metrics being scraped

---

## 🎯 Success Criteria

### All Systems Operational
- [ ] All pods running (0 crashes)
- [ ] All services accessible internally
- [ ] All PVCs bound
- [ ] Ingress routing traffic
- [ ] SSL certificates issued

### API Functional
- [ ] Health endpoint responds
- [ ] Authentication working (API key required)
- [ ] Optimization endpoint returns suggestions
- [ ] Database queries working
- [ ] Redis caching functional

### Monitoring Active
- [ ] Grafana accessible externally
- [ ] All 3 dashboards loaded
- [ ] Prometheus collecting metrics
- [ ] No alerts firing (or expected alerts only)

### Performance Baseline
- [ ] API latency < 100ms (p95)
- [ ] Zero error rate
- [ ] CPU usage < 50%
- [ ] Memory usage < 60%

---

## 🚨 Rollback Plan

If something goes wrong:

### Rollback Deployment
```bash
kubectl rollout undo deployment/inframind-api -n infra
kubectl rollout status deployment/inframind-api -n infra
```

### Delete Everything
```bash
kubectl delete namespace infra
# Wait for cleanup, then redeploy
```

### Check Logs
```bash
kubectl logs -n infra -l app=inframind-api --tail=100
kubectl logs -n infra -l app=postgres --tail=100
kubectl describe pod <failing-pod> -n infra
```

---

## 📝 Post-Deployment Notes

### Record for Team

- **Deployment Date**: _______________
- **Deployed By**: _______________
- **Cluster**: _______________
- **Region/Zone**: _______________
- **API URL**: https://api.inframind.yourdomain.com
- **Grafana URL**: https://grafana.inframind.yourdomain.com
- **External IP**: _______________
- **Initial Version**: v0.1.0

### Issues Encountered

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Resolutions

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

---

## ✅ Final Sign-Off

- [ ] All items in this checklist completed
- [ ] Deployment verified successful
- [ ] Monitoring operational
- [ ] Team notified
- [ ] Documentation updated
- [ ] Secrets secured in password manager
- [ ] Production ready ✅

**Deployed by**: _______________
**Date**: _______________
**Sign**: _______________

---

## 🎉 Congratulations!

Your InfraMind production deployment is complete!

**Next Steps**:
1. Integrate with your CI/CD pipeline
2. Start collecting real build data
3. Monitor performance in Grafana
4. Set up alerts for critical issues
5. Plan Phase 2 enhancements (see NEXT_STEPS.md)

**Support**:
- Documentation: See `PRODUCTION_DEPLOYMENT.md`
- Troubleshooting: See deployment guide
- Updates: Follow the roadmap in `NEXT_STEPS.md`

---

**Last Updated**: October 25, 2025
**Version**: 0.1.0
