# 🚂 Quick Railway Deployment

## Deploy in 5 Steps

1. **Go to [railway.app](https://railway.app)** → New Project → GitHub Repo

2. **Add PostgreSQL:**
   - Click "+ New" → "Database" → "Add PostgreSQL"
   - Railway auto-creates `DATABASE_URL`

3. **Deploy Backend:**
   - Click "+ New" → "GitHub Repo"
   - Set **Root Directory:** `backend`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables:**
   ```
   ENVIRONMENT=production
   SECRET_KEY=<generate-random-32-char-key>
   CORS_ORIGINS=https://your-frontend.vercel.app,https://yourdomain.com
   ```

5. **Deploy!** → Get URL from Settings → Networking

## Test

- Health: `https://your-backend.up.railway.app/health`
- Docs: `https://your-backend.up.railway.app/docs`

## Full Guide

See `RAILWAY_BACKEND_DEPLOYMENT.md` for complete instructions.
