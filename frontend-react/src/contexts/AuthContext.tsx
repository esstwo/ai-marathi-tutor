import { createContext, useContext, useState, useEffect, useCallback } from "react";
import type { Child } from "@/types";
import * as api from "@/services/api";

interface AuthState {
  accessToken: string | null;
  userId: string | null;
  children: Child[];
  activeChild: Child | null;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<{ children: Child[] }>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  addChild: (name: string, age: number, avatar: string) => Promise<Child>;
  selectChild: (child: Child) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children: reactChildren }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(
    () => localStorage.getItem("access_token")
  );
  const [userId, setUserId] = useState<string | null>(
    () => localStorage.getItem("user_id")
  );
  const [childrenList, setChildrenList] = useState<Child[]>(() => {
    const stored = localStorage.getItem("children");
    return stored ? JSON.parse(stored) : [];
  });
  const [activeChild, setActiveChild] = useState<Child | null>(() => {
    const stored = localStorage.getItem("active_child");
    return stored ? JSON.parse(stored) : null;
  });

  const isAuthenticated = !!accessToken;

  const persist = useCallback(
    (token: string, uid: string, kids: Child[], active: Child | null) => {
      localStorage.setItem("access_token", token);
      localStorage.setItem("user_id", uid);
      localStorage.setItem("children", JSON.stringify(kids));
      if (active) localStorage.setItem("active_child", JSON.stringify(active));
      setAccessToken(token);
      setUserId(uid);
      setChildrenList(kids);
      setActiveChild(active);
    },
    []
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.login(email, password);
      const kids = res.children || [];
      const active = kids.length > 0 ? kids[0] : null;
      persist(res.access_token, res.user_id, kids, active);
      return { children: kids };
    },
    [persist]
  );

  const signup = useCallback(
    async (name: string, email: string, password: string) => {
      const res = await api.signup(name, email, password);
      persist(res.access_token, res.user_id, [], null);
    },
    [persist]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("children");
    localStorage.removeItem("active_child");
    setAccessToken(null);
    setUserId(null);
    setChildrenList([]);
    setActiveChild(null);
  }, []);

  const addChild = useCallback(
    async (name: string, age: number, avatar: string) => {
      const child = await api.createChild(name, age, avatar);
      const updated = [...childrenList, child];
      setChildrenList(updated);
      setActiveChild(child);
      localStorage.setItem("children", JSON.stringify(updated));
      localStorage.setItem("active_child", JSON.stringify(child));
      return child;
    },
    [childrenList]
  );

  const selectChild = useCallback((child: Child) => {
    setActiveChild(child);
    localStorage.setItem("active_child", JSON.stringify(child));
  }, []);

  return (
    <AuthContext.Provider
      value={{
        accessToken,
        userId,
        children: childrenList,
        activeChild,
        isAuthenticated,
        login,
        signup,
        logout,
        addChild,
        selectChild,
      }}
    >
      {reactChildren}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
