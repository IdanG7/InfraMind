# 🚀 Getting Started - Deploy InfraMind

**Your Step-by-Step Guide to Getting InfraMind Running**

---

## 📍 Where You Are Now

You have InfraMind running **locally on your computer** via Docker Compose:
- API: http://localhost:8081
- Grafana: http://localhost:3001
- Everything is working!

---

## 🎯 What You Want to Do

You have **3 options**:

### **Option 1: Keep Using It Locally** ⭐ EASIEST
Continue using it on your computer for testing and development.

### **Option 2: Deploy to GitHub (Make it Public)**
Push your code to GitHub and share it with others.

### **Option 3: Deploy to Production (Kubernetes/Cloud)**
Run it on a server so your team can access it 24/7.

---

## 📋 Let's Walk Through Each Option

---

## ✅ **OPTION 1: Use It Locally (Recommended to Start)**

**What this means**: Keep running InfraMind on your laptop/computer.

**Pros**:
- Already working!
- No need to set up cloud infrastructure
- Free
- Great for testing and learning

**Cons**:
- Only you can access it
- Stops when you shut down your computer

### Steps:

**1. Keep it running:**
```bash
# It's already running! Check status:
docker-compose ps

# If you need to restart:
make down
make up

# View logs:
docker-compose logs -f api
```

**2. Use it to optimize your builds:**

```bash
# Get optimization suggestions:
curl -X POST http://localhost:8081/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline": "my-project",
    "context": {
      "branch": "main",
      "prev_duration_s": 600
    }
  }'

# Track a build:
curl -X POST http://localhost:8081/builds/start \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline": "my-project",
    "run_id": "build-001",
    "branch": "main",
    "commit": "abc123",
    "image": "ubuntu:22.04"
  }'

# Complete the build:
curl -X POST http://localhost:8081/builds/complete \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "build-001",
    "status": "success",
    "duration_s": 300
  }'
```

**3. View dashboards:**
```bash
# Open Grafana
open http://localhost:3001
# Login: admin/admin
# Go to Dashboards → InfraMind
```

**4. When done for the day:**
```bash
# Stop services (keeps data)
docker-compose stop

# Or completely remove (deletes data)
docker-compose down -v
```

**✅ This is perfect for: Testing, learning, personal use**

---

## ✅ **OPTION 2: Push to GitHub (Share Your Code)**

**What this means**: Upload your code to GitHub so others can see it and use it.

**Pros**:
- Share with the world
- GitHub Actions will run tests automatically
- Free hosting for code
- Others can contribute

**Cons**:
- Code is public (unless you use private repo)
- Doesn't automatically deploy (just stores code)

### Steps:

**1. Clean up secrets (IMPORTANT!):**
```bash
# Make sure .env is NOT committed
cat .gitignore | grep .env
# Should see: .env

# Check what will be committed
git status

# Make sure you see:
# - No .env file
# - No passwords or API keys in any file
```

**2. Commit your changes:**
```bash
cd /Users/idang/Projects/InfraRead

# See what changed
git status

# Add all changes
git add .

# Commit
git commit -m "feat: add production monitoring with Prometheus and rate limiting

- Added Prometheus metrics endpoint (/metrics)
- Implemented distributed rate limiting via Redis (100 req/min)
- Enhanced health checks with dependency verification
- Created 3 Grafana dashboards (28 panels)
- Updated all documentation for production release"

# Check your commit
git log -1
```

**3. Create a GitHub repository:**

**Option A: Use GitHub CLI (gh):**
```bash
# Create a new public repo
gh repo create InfraMind --public --source=. --remote=origin

# Push your code
git push -u origin master
```

**Option B: Use GitHub Website:**
1. Go to https://github.com/new
2. Name: `InfraMind`
3. Description: "ML-powered CI/CD optimization engine"
4. Public or Private (your choice)
5. DON'T initialize with README (you already have one)
6. Click "Create repository"

Then run:
```bash
# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/InfraMind.git

# Push your code
git push -u origin master
```

**4. GitHub Actions will automatically:**
- Run tests on every push
- Build Docker images
- Lint your code

**5. View your project:**
```bash
# Open in browser
gh repo view --web

# Or manually:
open https://github.com/YOUR_USERNAME/InfraMind
```

**✅ This is perfect for: Sharing code, collaboration, building a portfolio**

---

## ✅ **OPTION 3: Deploy to Production (Real Server)**

**What this means**: Run InfraMind on a server so it's accessible 24/7 by your team.

**Pros**:
- Accessible from anywhere
- Runs 24/7
- Can handle multiple users
- Production-ready

**Cons**:
- Costs money (cloud server)
- Requires more setup
- Need to manage infrastructure

### Where to Deploy:

**Choice 1: Simple Server (DigitalOcean, AWS, GCP)**
**Choice 2: Kubernetes (EKS, GKE, AKS)**
**Choice 3: Free Tier (Render, Railway, Fly.io)**

Let me show you the **easiest option** - **Railway** (free tier):

---

### 🚂 **Deploy to Railway (Free - Easiest)**

**1. Sign up for Railway:**
```bash
open https://railway.app
# Sign up with GitHub
```

**2. Install Railway CLI:**
```bash
# macOS
brew install railway

# Or use npm
npm install -g @railway/cli

# Login
railway login
```

**3. Push to GitHub first (see Option 2 above):**
```bash
git push origin master
```

**4. Deploy from GitHub:**
```bash
# Initialize Railway project
railway init

# Link to your GitHub repo
railway link

# Add services one by one
railway up postgres
railway up redis
railway up api

# Set environment variables
railway variables set API_KEY=$(openssl rand -hex 32)
railway variables set DATABASE_URL=postgresql://...
railway variables set REDIS_URL=redis://...

# Deploy
railway up
```

**5. Access your app:**
```bash
# Get the URL
railway domain

# Open in browser
railway open
```

**Free Tier Limits:**
- $5 free credit/month
- Good for testing
- 500MB RAM per service
- Perfect for learning

---

### ☸️ **Deploy to Kubernetes (Advanced)**

**Prerequisites:**
- Kubernetes cluster (EKS, GKE, AKS, or local with minikube)
- kubectl installed
- helm installed

**1. Have a Kubernetes cluster ready:**
```bash
# Check access
kubectl cluster-info

# Or create a local cluster for testing
minikube start
```

**2. Create namespace:**
```bash
kubectl create namespace infra
```

**3. Create secrets:**
```bash
# Create secret for database password
kubectl create secret generic inframind-secrets \
  --from-literal=api-key=$(openssl rand -hex 32) \
  --from-literal=postgres-password=$(openssl rand -hex 16) \
  --from-literal=redis-password=$(openssl rand -hex 16) \
  -n infra
```

**4. Deploy using Helm:**
```bash
# From your InfraMind directory
cd /Users/idang/Projects/InfraRead

# Install with Helm
helm upgrade --install inframind deploy/helm/inframind \
  --namespace infra \
  --create-namespace \
  --set api.replicas=2 \
  --set api.image.tag=latest \
  --wait

# Check status
kubectl get pods -n infra
kubectl get svc -n infra
```

**5. Access your deployment:**
```bash
# Port forward to access locally
kubectl port-forward svc/inframind-api 8080:8080 -n infra

# Or create an ingress/load balancer (see k8s/ingress.yaml)
kubectl apply -f k8s/ingress.yaml

# Get external IP
kubectl get ingress -n infra
```

**6. View logs:**
```bash
kubectl logs -f deployment/inframind-api -n infra
```

---

### 🌩️ **Deploy to AWS/GCP/Azure (Enterprise)**

**For AWS:**
```bash
# 1. Create EKS cluster
eksctl create cluster --name inframind --region us-west-2

# 2. Deploy
kubectl apply -f k8s/

# 3. Set up LoadBalancer
kubectl apply -f k8s/service-lb.yaml
```

**For GCP:**
```bash
# 1. Create GKE cluster
gcloud container clusters create inframind \
  --zone us-central1-a \
  --num-nodes 3

# 2. Deploy
kubectl apply -f k8s/

# 3. Get external IP
kubectl get svc
```

---

## 🤔 **Which Option Should You Choose?**

### **Choose Option 1 (Local)** if:
- ✅ You're just testing/learning
- ✅ You don't need 24/7 availability
- ✅ It's just for you
- ✅ You want FREE
- ✅ **← START HERE**

### **Choose Option 2 (GitHub)** if:
- ✅ You want to share code
- ✅ You want others to contribute
- ✅ You want version control
- ✅ You're building a portfolio
- ✅ **← DO THIS SECOND**

### **Choose Option 3 (Production)** if:
- ✅ You have a team using it
- ✅ You need 24/7 availability
- ✅ You're ready to pay for hosting
- ✅ You need scale (100+ users)
- ✅ **← DO THIS AFTER TESTING LOCALLY**

---

## 📝 **My Recommended Path for You:**

### **Week 1: Local Testing**
```bash
# Keep using it locally
make up
# Test with your real CI/CD builds
# Collect data
# View dashboards
```

### **Week 2: Push to GitHub**
```bash
# Commit your code
git add .
git commit -m "Initial release v0.1.0"

# Create GitHub repo
gh repo create InfraMind --public --source=. --remote=origin
git push -u origin master

# Share with others!
```

### **Week 3-4: Deploy to Production**
```bash
# Choose based on your needs:
# - Railway (free, easiest)
# - Kubernetes (scalable, powerful)
# - Your own server (most control)
```

---

## 🚨 **Before You Commit - IMPORTANT!**

**Run this checklist:**

```bash
# 1. Make sure .env is NOT being committed
cat .gitignore | grep "^\.env$"
# Should show: .env

# 2. Check for secrets
git status
# Make sure no .env files are listed

# 3. Verify no secrets in code
grep -r "password\|secret\|api_key" --include="*.py" --include="*.yaml" . | grep -v "placeholder"
# Should be minimal results

# 4. Test that everything works
make down
make up
curl http://localhost:8081/healthz
# Should return: {"status":"ok",...}

# 5. NOW you can commit!
git add .
git commit -m "Your message"
```

---

## 🎯 **Quick Start Commands**

### **To commit and push to GitHub:**
```bash
# From InfraRead directory
cd /Users/idang/Projects/InfraRead

# Check status
git status

# Add files
git add .

# Commit
git commit -m "feat: add production monitoring and release v0.1.0"

# Create GitHub repo and push
gh repo create InfraMind --public --source=. --remote=origin
git push -u origin master

# View on GitHub
gh repo view --web
```

### **To deploy locally:**
```bash
# You're already doing this!
make up

# View services
docker-compose ps

# View logs
docker-compose logs -f api
```

### **To stop everything:**
```bash
# Stop but keep data
docker-compose stop

# Stop and remove everything (including data)
docker-compose down -v
```

---

## 🆘 **Need Help?**

### **If something breaks:**
```bash
# Check logs
docker-compose logs api

# Restart everything fresh
make down
make up

# Check if ports are in use
lsof -i :8081
```

### **Common Issues:**

**Problem: Port already in use**
```bash
# Solution: Change port in .env
echo "API_PORT=8082" >> .env
make down && make up
```

**Problem: Database connection error**
```bash
# Solution: Recreate database
docker-compose down -v
docker-compose up -d
```

**Problem: Can't access Grafana**
```bash
# Solution: Check if it's running
docker-compose ps grafana
# Try: http://localhost:3001
# Login: admin/admin
```

---

## 📞 **Questions?**

**Not sure which option to choose?**
→ Start with **Option 1 (Local)** - it's already working!

**Want to share your project?**
→ Do **Option 2 (GitHub)** next

**Need help deploying?**
→ Read **PRODUCTION_DEPLOYMENT.md** or **DEPLOYMENT_CHECKLIST.md**

**Want to see it in action?**
→ Open http://localhost:3001 (Grafana) and explore the dashboards!

---

## ✅ **TL;DR - Just Tell Me What to Do**

**For most people, do this:**

```bash
# 1. Keep it running locally
cd /Users/idang/Projects/InfraRead
make up

# 2. Use it and test it for a week
curl -X POST http://localhost:8081/optimize \
  -H "Content-Type: application/json" \
  -d '{"pipeline": "test", "context": {}}'

# 3. When ready, push to GitHub
git add .
git commit -m "feat: InfraMind v0.1.0 - ML-powered CI/CD optimization"
gh repo create InfraMind --public --source=. --remote=origin
git push -u origin master

# 4. Later, deploy to production (Railway/Kubernetes/AWS)
# Follow the steps in Option 3 above
```

**That's it! 🎉**

---

**Current Status**: ✅ Everything is working locally
**Next Step**: Test it out, then push to GitHub
**After That**: Deploy to production when ready

**You got this! 🚀**
