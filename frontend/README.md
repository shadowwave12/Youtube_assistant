# Frontend

The React + JavaScript + Vite application provides the browser interface for the assistant.

## Planned boundaries

- `src/components/`: Reusable UI components.
- `src/pages/`: User-facing screens.
- `src/api/`: JavaScript API client for the FastAPI backend.
- `src/components/`: Reusable UI components for processing and chat.
- `src/assets/`: Static browser assets.

The app calls the real FastAPI processing and chat endpoints. It does not mock successful responses.

## Local development

```powershell
npm install
npm run dev
```
