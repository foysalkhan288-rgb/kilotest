import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react";
import { AuthResponse, User, Workspace, login, logout as apiLogout, register } from "../api/auth";
import { getAccessToken, WORKSPACE_KEY } from "../api/client";

interface AuthContextValue {
  user: User | null;
  workspace: Workspace | null;
  isAuthenticated: boolean;
  login: (payload: { email: string; password: string }) => Promise<void>;
  register: (payload: {
    email: string;
    password: string;
    name: string;
    workspace_name: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const readWorkspace = (): Workspace | null => {
  const raw = localStorage.getItem(WORKSPACE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Workspace;
  } catch {
    return null;
  }
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(readWorkspace());

  useEffect(() => {
    const token = getAccessToken();
    if (token && !user) {
      setWorkspace(readWorkspace());
    }
  }, [user]);

  const handleAuth = useCallback((data: AuthResponse) => {
    setUser(null);
    setWorkspace({ id: data.workspace_id, name: "" });
  }, []);

  const loginFn = useCallback(
    async (payload: { email: string; password: string }) => {
      const data = await login(payload);
      handleAuth(data);
    },
    [handleAuth]
  );

  const registerFn = useCallback(
    async (payload: {
      email: string;
      password: string;
      name: string;
      workspace_name: string;
    }) => {
      const data = await register(payload);
      handleAuth(data);
    },
    [handleAuth]
  );

  const logoutFn = useCallback(() => {
    apiLogout();
    setUser(null);
    setWorkspace(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        workspace,
        isAuthenticated: Boolean(getAccessToken()),
        login: loginFn,
        register: registerFn,
        logout: logoutFn,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
