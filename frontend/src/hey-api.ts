// src/hey-api.ts
import type {CreateClientConfig} from "./api/client.gen"
import {getEnv} from "@/env";

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseURL: getEnv('VITE_API_BASE_URL') || config.baseURL,
  withCredentials: true,
  throwOnError: true,
});
