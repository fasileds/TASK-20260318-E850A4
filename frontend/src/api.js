import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 15000,
});

export function setUsernameHeader(username) {
  if (username) {
    api.defaults.headers.common["X-Username"] = username;
  } else {
    delete api.defaults.headers.common["X-Username"];
  }
}
