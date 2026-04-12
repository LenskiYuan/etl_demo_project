import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "etl-demo",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "etl-frontend",
});

export async function initializeAuth() {
  const authenticated = await keycloak.init({
    onLoad: "login-required",
    checkLoginIframe: false,
    pkceMethod: "S256",
  });

  if (!authenticated) {
    throw new Error("Authentication failed");
  }

  return keycloak;
}

export function getKeycloak() {
  return keycloak;
}
