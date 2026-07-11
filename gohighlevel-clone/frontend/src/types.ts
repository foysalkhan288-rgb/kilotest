export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role?: string;
}

export interface Workspace {
  id: string;
  name: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}
