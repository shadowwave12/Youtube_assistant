# Frontend Component Plan

## Request flow

1. `VideoProcessor` collects a YouTube URL and calls `processVideo` from the API client.
2. `App` stores the returned `video_id`, processing status, and chunk count.
3. `ChatPanel` becomes available after processing succeeds.
4. `ChatPanel` calls `sendChat` with the active video ID and question.
5. `App` appends the answer and source excerpts to the message list.
6. API failures are converted into user-facing messages by the client and rendered by `StatusBanner`.

## Components

- `App`: owns workflow state and composes the page.
- `VideoProcessor`: URL input, submit action, loading state, and validation feedback.
- `ChatPanel`: message history, question input, submit state, and source excerpts.
- `StatusBanner`: processing, ready, and error feedback with an accessible live region.
- `api/client.js`: the only module that performs HTTP requests.
- API response shapes are documented in the client through clear object naming; runtime validation remains owned by FastAPI.

The frontend does not mock successful responses. It always calls the FastAPI backend and displays an explicit connection error when the backend is unavailable.
