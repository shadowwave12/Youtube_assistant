const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export class ApiClientError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

async function apiRequest(path, options) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
  } catch {
    throw new ApiClientError(
      "The assistant backend is unavailable. Start FastAPI and try again.",
      0,
    );
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    const errorDetail =
      typeof detail === "string"
        ? detail
        : detail?.error?.message ??
          detail?.message ??
          payload?.error?.message ??
          payload?.message ??
          "The request could not be completed.";
    throw new ApiClientError(
      errorDetail,
      response.status,
    );
  }

  return response.json();
}

export function processVideo(payload) {
  return apiRequest("/api/videos/process", {
    method: "POST",
    body: JSON.stringify({
      source: payload.source,
      languages: payload.languages ?? ["en"],
    }),
  });
}

export function sendChat(payload) {
  return apiRequest("/api/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
