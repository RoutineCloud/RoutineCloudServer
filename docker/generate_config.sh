#!/bin/sh

# Default values if not provided
VITE_OIDC_ISSUER=${VITE_OIDC_ISSUER}
VITE_OIDC_CLIENT_ID=${VITE_OIDC_CLIENT_ID}
VITE_API_BASE_URL=${VITE_API_BASE_URL:-"http://localhost:3000"}

# Generate config.js
cat <<EOF > /usr/share/nginx/html/config.js
window.config = {
  VITE_OIDC_ISSUER: "${VITE_OIDC_ISSUER}",
  VITE_OIDC_CLIENT_ID: "${VITE_OIDC_CLIENT_ID}",
  VITE_API_BASE_URL: "${VITE_API_BASE_URL}"
};
EOF
