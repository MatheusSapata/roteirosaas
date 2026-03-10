import axios from "axios";

const defaultApi = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const apiRoot = defaultApi.replace(/\/api\/v1\/?$/, "");
const caktoBaseUrl = `${apiRoot}/api/cakto`;

export const CHECKOUT_SESSION_STORAGE_KEY = "caktoCheckoutToken";

const client = axios.create({
  baseURL: caktoBaseUrl
});

export const fetchOnboardingSession = (params: Record<string, string>) => {
  return client.get("/onboarding/session", { params });
};

export const submitOnboardingPassword = (params: Record<string, string>, payload: { password: string }) => {
  return client.post("/onboarding/session/password", payload, { params });
};

export const submitManualOnboardingPassword = (payload: { email: string; password: string }) => {
  return client.post("/onboarding/manual-password", payload);
};

export const validateManualOnboardingEmail = (payload: { email: string }) => {
  return client.post("/onboarding/manual-password/validate", payload);
};

export const createCaktoCheckoutSession = (plan: string, cycle?: string) => {
  return client.post("/checkout-session", { plan, cycle });
};

export const getCheckoutSessionStatus = (token: string) => {
  return client.get(`/checkout-session/${token}`);
};
