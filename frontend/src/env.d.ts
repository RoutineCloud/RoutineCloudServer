/// <reference types="vite/client" />

// Shims for Vue single-file components
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface Window {
  config?: {
    VITE_OIDC_ISSUER?: string;
    VITE_OIDC_CLIENT_ID?: string;
    VITE_API_BASE_URL?: string;
  };
}
