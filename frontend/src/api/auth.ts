import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { LoginRequest, PlatformUser, TokenResponse } from '@/types'
import { apiClient } from './client'
import { useAuthStore } from '@/stores/authStore'

const AUTH_KEY = ['auth'] as const

async function loginRequest(body: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', body)
  return data
}

async function fetchMe(): Promise<PlatformUser> {
  const { data } = await apiClient.get<PlatformUser>('/auth/me')
  return data
}

export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const tokenResponse = await loginRequest(body)
      useAuthStore.setState({ accessToken: tokenResponse.access_token })
      localStorage.setItem('agriflow_access_token', tokenResponse.access_token)
      const user = await fetchMe()
      return { tokenResponse, user }
    },
    onSuccess: ({ tokenResponse, user }) => {
      setSession(tokenResponse.access_token, user)
      queryClient.setQueryData([...AUTH_KEY, 'me'], user)
    },
  })
}

export function useCurrentUser(enabled = true) {
  const token = useAuthStore((s) => s.accessToken)

  return useQuery({
    queryKey: [...AUTH_KEY, 'me'],
    queryFn: fetchMe,
    enabled: enabled && Boolean(token),
    retry: false,
  })
}

export function useLogout() {
  const clearSession = useAuthStore((s) => s.clearSession)
  const queryClient = useQueryClient()

  return () => {
    clearSession()
    queryClient.removeQueries({ queryKey: AUTH_KEY })
  }
}
