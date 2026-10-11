import { useQuery } from '@tanstack/react-query'
import type {
  EventCatalogResponse,
  OutboxEntryListResponse,
  OutboxEntryStatus,
  OutboxStats,
} from '@/types'
import { apiClient } from './client'

const EVENTS_KEY = ['events'] as const

async function fetchEventCatalog(): Promise<EventCatalogResponse> {
  const { data } = await apiClient.get<EventCatalogResponse>('/events/catalog')
  return data
}

async function fetchOutboxStats(): Promise<OutboxStats> {
  const { data } = await apiClient.get<OutboxStats>('/events/outbox/stats')
  return data
}

async function fetchOutboxEntries(
  status: OutboxEntryStatus,
  limit = 50,
): Promise<OutboxEntryListResponse> {
  const { data } = await apiClient.get<OutboxEntryListResponse>('/events/outbox/entries', {
    params: { status, limit },
  })
  return data
}

export function useEventCatalog() {
  return useQuery({
    queryKey: [...EVENTS_KEY, 'catalog'],
    queryFn: fetchEventCatalog,
  })
}

export function useOutboxStats() {
  return useQuery({
    queryKey: [...EVENTS_KEY, 'outbox', 'stats'],
    queryFn: fetchOutboxStats,
    refetchInterval: 15_000,
  })
}

export function useOutboxEntries(status: OutboxEntryStatus) {
  return useQuery({
    queryKey: [...EVENTS_KEY, 'outbox', 'entries', status],
    queryFn: () => fetchOutboxEntries(status),
    refetchInterval: 15_000,
  })
}
