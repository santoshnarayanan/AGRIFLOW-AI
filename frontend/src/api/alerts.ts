import { useQuery } from '@tanstack/react-query'
import type { Alert } from '@/types'
import { apiClient } from './client'

const ALERTS_KEY = ['alerts'] as const

async function fetchAlerts(limit = 50): Promise<Alert[]> {
  const { data } = await apiClient.get<Alert[]>('/alerts/', { params: { limit } })
  return data
}

export function useAlerts(limit = 50) {
  return useQuery({ queryKey: [...ALERTS_KEY, limit], queryFn: () => fetchAlerts(limit) })
}

export function useRecentAlerts() {
  return useAlerts(5)
}
