import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Alert, AlertCreate, AlertUpdate } from '@/types'
import { apiClient } from './client'

const ALERTS_KEY = ['alerts'] as const

async function fetchFieldAlerts(
  fieldId: string,
  activeOnly = false,
  limit = 500,
): Promise<Alert[]> {
  const path = activeOnly
    ? `/fields/${fieldId}/alerts/active`
    : `/fields/${fieldId}/alerts`
  const { data } = await apiClient.get<Alert[]>(path, { params: { limit, offset: 0 } })
  return data
}

async function createAlert(fieldId: string, payload: AlertCreate): Promise<Alert> {
  const { data } = await apiClient.post<Alert>(`/fields/${fieldId}/alerts`, payload)
  return data
}

async function updateAlert(id: string, payload: AlertUpdate): Promise<Alert> {
  const { data } = await apiClient.patch<Alert>(`/alerts/${id}`, payload)
  return data
}

async function deleteAlert(id: string): Promise<void> {
  await apiClient.delete(`/alerts/${id}`)
}

export function useFieldAlerts(
  fieldId: string | undefined,
  options?: { activeOnly?: boolean },
) {
  const activeOnly = options?.activeOnly ?? false
  return useQuery({
    queryKey: [...ALERTS_KEY, 'field', fieldId, activeOnly ? 'active' : 'all'],
    queryFn: () => fetchFieldAlerts(fieldId!, activeOnly),
    enabled: !!fieldId,
  })
}

/** Load alerts for many fields (dashboard and farm-wide views). */
export function useAlertsForFieldIds(fieldIds: string[], activeOnly = false) {
  const queries = useQueries({
    queries: fieldIds.map((fieldId) => ({
      queryKey: [...ALERTS_KEY, 'field', fieldId, activeOnly ? 'active' : 'all'],
      queryFn: () => fetchFieldAlerts(fieldId, activeOnly),
      enabled: fieldIds.length > 0,
    })),
  })

  const isLoading = queries.some((q) => q.isLoading)
  const isError = queries.some((q) => q.isError)
  const data = queries.flatMap((q) => q.data ?? [])
  const sorted = [...data].sort(
    (a, b) => new Date(b.triggered_at).getTime() - new Date(a.triggered_at).getTime(),
  )

  return { data: sorted, isLoading, isError }
}

/** @deprecated Use useAlertsForFieldIds with field IDs from useFields */
export function useAlerts(limit = 50) {
  return useQuery({
    queryKey: [...ALERTS_KEY, 'legacy', limit],
    queryFn: async () => [] as Alert[],
    enabled: false,
  })
}

export function useRecentAlerts() {
  return useAlerts(5)
}

export function useCreateAlert() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ fieldId, payload }: { fieldId: string; payload: AlertCreate }) =>
      createAlert(fieldId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ALERTS_KEY }),
  })
}

export function useUpdateAlert() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: AlertUpdate }) =>
      updateAlert(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ALERTS_KEY }),
  })
}

export function useDeleteAlert() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteAlert,
    onSuccess: () => qc.invalidateQueries({ queryKey: ALERTS_KEY }),
  })
}
