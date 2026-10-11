import { useQuery } from '@tanstack/react-query'
import type { PlatformDashboardReadModel } from '@/types'
import { apiClient } from './client'

const READ_MODELS_KEY = ['read-models'] as const

async function fetchPlatformDashboard(): Promise<PlatformDashboardReadModel> {
  const { data } = await apiClient.get<PlatformDashboardReadModel>('/read-models/dashboard')
  return data
}

export function usePlatformDashboard() {
  return useQuery({
    queryKey: [...READ_MODELS_KEY, 'platform-dashboard'],
    queryFn: fetchPlatformDashboard,
    staleTime: 60_000,
  })
}
