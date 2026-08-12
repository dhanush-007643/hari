# Complete Step-by-Step Guide: Deploying on Render & Vercel

This guide provides the exact, beginner-friendly process to deploy your project:
- **Backend (FastAPI)** → **Render**
- **Frontend (React / Vite)** → **Vercel**

---

## 📌 Prerequisites: Push Code to GitHub

Make sure your project code is pushed to GitHub before starting:

```bash
# Open terminal in your project root folder (hari)
git init
git add .
git commit -m "Initial commit for deployment"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git
git push -u origin main
```

---

## 🚀 Step 1: Deploy Backend on Render

1. Log into your **[Render Dashboard](https://dashboard.render.com/)**.
2. Click the **New +** button at top right and select **Web Service**.
3. Connect your **GitHub account** and select your repository (`<YOUR_REPO_NAME>`).
4. Configure the Web Service settings as follows:
   - **Name:** `datavista-backend`
   - **Language / Environment:** `Python 3`
   - **Branch:** `main`
   - **Root Directory:** *(Leave blank)*
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Scroll down to **Environment Variables** and add these 4 keys:
   | Key | Value |
   | :--- | :--- |
   | `PYTHON_VERSION` | `3.11.0` |
   | `DEBUG` | `false` |
   | `SECRET_KEY` | `datavista-production-secret-key-2025` |
   | `ALLOWED_ORIGINS` | `*` |
6. Click **Create Web Service**.
7. Wait 2-3 minutes for Render to build. Once complete, copy your **Render Backend URL** at the top left:
   > Example: `https://datavista-backend.onrender.com`

---

## ⚡ Step 2: Deploy Frontend on Vercel

1. Log into your **[Vercel Dashboard](https://vercel.com/dashboard)**.
2. Click **Add New...** → **Project**.
3. Import your GitHub repository (`<YOUR_REPO_NAME>`).
4. Configure Project Settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click **Edit** and select `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Expand the **Environment Variables** section and add:
   - **Name / Key:** `VITE_API_URL`
   - **Value:** `https://datavista-backend.onrender.com` *(Paste your exact Render URL from Step 1)*
6. Click **Deploy**.
7. Vercel will build your frontend in ~1 minute and provide your live application link!

---

## 🧪 Step 3: Test & Verify

1. Click your live Vercel app link (e.g. `https://datavista-frontend.vercel.app`).
2. Log in using default credentials:
   - **Email:** `admin@datavista.com`
   - **Password:** `Admin@123`
3. Test natural language queries, ML predictions, and report downloads to verify frontend-backend communication.
