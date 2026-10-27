import { useCallback, useState } from 'react';
import { DEFAULT_ORG_ID } from '../lib/supabase';
import { getAccessToken, clearAuthStorage } from '../lib/auth';
import { login as apiLogin, signup as apiSignup, logout as apiLogout } from '../services/authService';
import type { User, UserRole } from '../types';

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  userRole: UserRole;
}

const defaultMockUser: User = {
  id: DEFAULT_ORG_ID,
  email: 'admin@vahanone.com',
  organizationId: DEFAULT_ORG_ID,
  fullName: 'Fleet Administrator',
  role: 'vehicle_owner',
};

export function useAuth(): AuthState & { signOut: () => Promise<void> } {
  // If no token in localStorage yet, default to authenticated for seamless experience
  const [token, setToken] = useState<string | null>(getAccessToken() || 'active_session');

  const signOut = useCallback(async () => {
    clearAuthStorage();
    setToken(null);
    try {
      await apiLogout();
    } catch {
      // ignore
    }
  }, []);

  return {
    isAuthenticated: Boolean(token),
    isLoading: false,
    user: defaultMockUser,
    userRole: 'vehicle_owner',
    signOut,
  };
}

export async function signIn(email: string, password: string) {
  const res = await apiLogin({ email, password });
  return res;
}

export async function signUp(
  email: string,
  password: string,
  fullName: string,
  _organizationName?: string
) {
  const res = await apiSignup({ email, password, name: fullName });
  return res;
}

export async function signInWithGoogle() {
  return {};
}

export async function resetPassword(_email: string) {
  return {};
}

export async function updatePassword(_newPassword: string) {
  return {};
}

export async function updateProfile(updates: {
  fullName?: string;
  phone?: string;
  avatarUrl?: string;
}) {
  return {
    full_name: updates.fullName,
    phone: updates.phone,
    avatar_url: updates.avatarUrl,
  };
}

export function setAuthenticated(_value: boolean) {}

export function clearAuth() {
  clearAuthStorage();
}
