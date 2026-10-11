import { create } from 'zustand'
import type { PlatformUser } from '@/types'

const TOKEN_KEY = 'agriflow_access_token'

export function getStoredAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

interface AuthState {
  accessToken: string | null
  user: PlatformUser | null
  setSession: (token: string, user: PlatformUser) => void
  clearSession: () => void
  hydrateToken: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: getStoredAccessToken(),
  user: null,
  setSession: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token)
    set({ accessToken: token, user })
  },
  clearSession: () => {
    localStorage.removeItem(TOKEN_KEY)
    set({ accessToken: null, user: null })
  },
  hydrateToken: () => set({ accessToken: getStoredAccessToken() }),
}))
