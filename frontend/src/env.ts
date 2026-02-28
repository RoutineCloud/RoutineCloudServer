// Utility to handle environment variables from both run-time (window.config) and build-time (import.meta.env)
export const getEnv = (name: string): string => {
  // @ts-ignore
  return window.config?.[name] || import.meta.env[name];
};
