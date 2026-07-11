import { apiClient, setTokens, clearTokens, WORKSPACE_KEY } from "./client";

export interface User {
  id: string;
  email: string;
  name: string;
  workspace_id: string;
}

export interface Workspace {
  id: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  workspace_id: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  name: string;
  workspace_name: string;
}

export const login = async (payload: LoginPayload): Promise<AuthResponse> => {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", payload);
  setTokens(data.access_token, data.refresh_token);
  localStorage.setItem(WORKSPACE_KEY, JSON.stringify({ id: data.workspace_id, name: "" }));
  return data;
};

export const register = async (
  payload: RegisterPayload
): Promise<AuthResponse> => {
  const { data } = await apiClient.post<AuthResponse>(
    "/auth/register",
    payload
  );
  setTokens(data.access_token, data.refresh_token);
  localStorage.setItem(WORKSPACE_KEY, JSON.stringify({ id: data.workspace_id, name: "" }));
  return data;
};

export const refresh = async (refreshToken: string): Promise<AuthResponse> => {
  const { data } = await apiClient.post<AuthResponse>("/auth/refresh", {
    refresh_token: refreshToken,
  });
  setTokens(data.access_token, data.refresh_token);
  localStorage.setItem(WORKSPACE_KEY, JSON.stringify({ id: data.workspace_id, name: "" }));
  return data;
};

export const logout = (): void => {
  clearTokens();
};
