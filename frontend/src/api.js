const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, token, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

export function fetchMe(token) {
  return request("/api/me", token);
}

export function fetchOverview(token) {
  return request("/api/overview", token);
}

export function fetchJobs(token) {
  return request("/api/jobs", token);
}

export function triggerJob(token, payload) {
  return request("/api/jobs/run", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchViews(token) {
  return request("/api/views", token);
}

export function saveView(token, payload) {
  return request("/api/views", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
