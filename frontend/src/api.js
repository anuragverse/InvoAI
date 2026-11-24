import axios from "axios";

// Backend address. Set VITE_API_URL when deploying (no trailing slash).
export const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

// Free hosting can take up to a minute to wake the server on the first request
export const api = axios.create({ baseURL: API_URL, timeout: 90000 });

export const MAX_UPLOAD_MB = 10;

// Turn any failed request into a message a person can understand
export function errorMessage(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string" && detail) return detail;

  // FastAPI validation errors arrive as a list
  if (Array.isArray(detail) && detail.length) {
    return "Please check your input and try again.";
  }

  if (error?.code === "ECONNABORTED") {
    return "The server took too long to respond. Please try again.";
  }

  if (!error?.response) {
    return "Cannot reach the server. Check your connection, or try again in a minute if the server was asleep.";
  }

  return fallback;
}
