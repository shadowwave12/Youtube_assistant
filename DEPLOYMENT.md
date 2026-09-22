# Deployment Checklist

This checklist prepares the existing application for GitHub, Render, and Vercel. It does not deploy anything automatically.

## Before deployment

- [ ] Code pushed to GitHub
- [ ] `.env` is not committed
- [ ] API keys are stored only in Render environment variables
- [ ] Backend dependencies are listed in `backend/requirements.txt`
- [ ] `backend/runtime.txt` matches the local Python version
- [ ] Production Torch resolves to a `+cpu` build
- [ ] No `nvidia-*`, CUDA, or Triton packages are installed
- [ ] Frontend build succeeds locally
- [ ] Backend tests pass locally

## Render backend

- [ ] Create a Render Web Service from the GitHub repository
- [ ] Set root directory to `backend`
- [ ] Set build command to `pip install -r requirements.txt`
- [ ] Set start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Set `LLM_PROVIDER`
- [ ] Set `LLM_MODEL`
- [ ] Set `LLM_API_KEY`
- [ ] Set `FRONTEND_URL` to the Vercel URL
- [ ] Confirm `https://your-backend.onrender.com/health` works
- [ ] Confirm the health response does not contain an API key

## Vercel frontend

- [ ] Create a Vercel project from the GitHub repository
- [ ] Set root directory to `frontend`
- [ ] Set framework to Vite
- [ ] Set build command to `npm run build`
- [ ] Set output directory to `dist`
- [ ] Set `VITE_API_URL` to the Render backend URL
- [ ] Redeploy after changing `VITE_API_URL`

## End-to-end test

- [ ] Open the Vercel URL
- [ ] Process a YouTube video
- [ ] Confirm transcript processing completes
- [ ] Confirm embeddings and FAISS indexing complete
- [ ] Ask a question
- [ ] Confirm the answer is displayed
- [ ] Confirm `/api/videos/process` succeeds in the browser Network tab
- [ ] Confirm `/api/chat` succeeds in the browser Network tab
- [ ] Confirm no LLM key appears in frontend source or browser requests

## Deployment risks for this architecture

- The embedding model downloads or loads during the first backend service initialization. A cold start can therefore take longer.
- FAISS indexes are held in memory. A Render restart or sleeping instance removes processed videos, so users must process the video again.
- The embedding model is loaded lazily once per backend process through the cached application service. Do not use multiple workers on a 512 MiB instance.
- YouTube transcript availability depends on the video and the external transcript service.
- Gemini and Groq rate limits, model availability, and API-key permissions remain external dependencies.
- Render free-tier sleep and cold starts can make the first request slow.
