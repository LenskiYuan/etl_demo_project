import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "etl-demo",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "etl-frontend",
});

let initPromise = null;

export async function initializeAuth() {
  if (keycloak.authenticated) {
    return keycloak;
  }

  if (initPromise) {
    return initPromise;
  }

  initPromise = keycloak
    .init({
      onLoad: "login-required",
      checkLoginIframe: false,
      pkceMethod: "S256",
    })
    .then((authenticated) => {
      if (!authenticated) {
        throw new Error("Authentication failed");
      }

      return keycloak;
    })
    .catch((error) => {
      initPromise = null;
      throw error;
    });

  return initPromise;
}

export function getKeycloak() {
  return keycloak;
}
