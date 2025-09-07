import axios from "axios"
import {useUserStore} from "@/stores/user.ts";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  timeout: 10000,
})

http.interceptors.request.use(cfg => {
  const token = localStorage.getItem("auth_token")
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})


// Global 401 handler -> logout
http.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
    }
    return Promise.reject(err)
  }
)