# Frontend Guide

The React + JavaScript + Vite application provides the browser interface for the assistant. It does not call YouTube or the LLM directly.

## Important files

- `src/App.jsx`: owns URL, video, chat, loading, and error state.
- `src/api/client.js`: sends JSON requests to FastAPI and turns errors into readable messages.
- `src/components/VideoProcessor.jsx`: collects a YouTube URL and starts processing.
- `src/components/ChatPanel.jsx`: collects questions and renders Markdown answers.

## Browser-to-backend flow

`VideoProcessor` calls `processVideo`, which sends `POST /api/videos/process`. After the backend returns a video ID, `ChatPanel` calls `sendChat`, which sends `POST /api/chat`. The returned `answer` is rendered with `react-markdown`.

## Local development

```powershell
npm install
npm run dev
```

Build the production bundle with:

```powershell
npm run build
```
