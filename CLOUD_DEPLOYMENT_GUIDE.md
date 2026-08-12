# Multi-Cloud Deployment Guide

This guide details how to deploy the **Explainable AI Natural Language Query & Analytics Platform** across major cloud platforms (**AWS**, **GCP**, **Azure**) and managed cloud databases (**Neon**, **Supabase**, **AWS RDS**).

---

## 1. AWS (Amazon Web Services)

### Backend: AWS App Runner or AWS ECS (Elastic Container Service)
1. Build and push Docker image to **AWS ECR (Elastic Container Registry)**:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
   docker build -t datavista-backend -f backend/Dockerfile.backend ./backend
   docker tag datavista-backend:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/datavista-backend:latest
   docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/datavista-backend:latest
   ```
2. Deploy to **AWS App Runner**:
   - Go to **AWS App Runner Console** → **Create Service**.
   - Select **Container Registry** → **ECR**.
   - Choose image: `datavista-backend:latest`.
   - Set Port: `8092`.
   - Add Environment Variables (`SECRET_KEY`, `DATABASE_URL`, `ALLOWED_ORIGINS`).
   - Click **Create & Deploy**.

### Frontend: AWS Amplify or AWS S3 + CloudFront
1. Build React frontend:
   ```bash
   cd frontend
   npm run build
   ```
2. Deploy via **AWS Amplify**:
   - Connect GitHub repository.
   - Set build settings to `frontend`.
   - Add `VITE_API_URL` pointing to AWS App Runner URL.

---

## 2. GCP (Google Cloud Platform)

### Backend: Google Cloud Run
1. Build and submit container using **Google Cloud Build**:
   ```bash
   gcloud builds submit --tag gcr.io/<YOUR_PROJECT_ID>/datavista-backend ./backend -f backend/Dockerfile.backend
   ```
2. Deploy to **Cloud Run**:
   ```bash
   gcloud run deploy datavista-backend \
     --image gcr.io/<YOUR_PROJECT_ID>/datavista-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8092 \
     --set-env-vars SECRET_KEY="<YOUR_SECRET_KEY>",ALLOWED_ORIGINS="*"
   ```

### Frontend: Firebase Hosting / Cloud Storage
1. Deploy build output `frontend/dist` using **Firebase Hosting**:
   ```bash
   npm install -g firebase-tools
   firebase login
   firebase init hosting
   firebase deploy
   ```

---

## 3. Azure (Microsoft Azure)

### Backend: Azure App Service (Linux Web App)
1. Build and push to **Azure Container Registry (ACR)**:
   ```bash
   az acr build --registry <YOUR_ACR_NAME> --image datavista-backend:v1 ./backend -f backend/Dockerfile.backend
   ```
2. Create App Service:
   ```bash
   az webapp create --resource-group <RESOURCE_GROUP> --plan <APP_SERVICE_PLAN> --name datavista-backend-app --deployment-container-image-name <YOUR_ACR_NAME>.azurecr.io/datavista-backend:v1
   ```

---

## 4. Managed Cloud Databases (PostgreSQL)

You can connect your FastAPI backend to any managed PostgreSQL cloud service by setting `DATABASE_URL` in your environment variables:

| Provider | Connection String Example (`DATABASE_URL`) |
| :--- | :--- |
| **Neon Tech** | `postgresql+asyncpg://user:pass@ep-cool-name.neon.tech/datavista?sslmode=require` |
| **Supabase** | `postgresql+asyncpg://postgres:pass@db.ref.supabase.co:5432/postgres` |
| **AWS RDS PostgreSQL** | `postgresql+asyncpg://admin:pass@datavista.cluster.us-east-1.rds.amazonaws.com:5432/datavista` |
| **GCP Cloud SQL** | `postgresql+asyncpg://postgres:pass@10.x.x.x:5432/datavista` |

---

## 5. Docker & Cloud VPS Deployment (Hetzner / DigitalOcean / AWS EC2)

You can also run the full stack on any Cloud Virtual Private Server (VPS) using Docker Compose:

```bash
# Clone repo on your cloud instance
git clone <YOUR_REPO_URL>
cd hari

# Launch entire production stack
docker-compose up -d --build
```
- Backend runs on `http://<SERVER_IP>:8092`
- Frontend runs on `http://<SERVER_IP>:8093`
