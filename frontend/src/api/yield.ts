import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { YieldRecord, YieldRecordCreate, YieldRecordUpdate } from '@/types'
import { apiClient } from './client'

const YIELD_KEY = ['yield'] as const

interface YieldParams {
  fieldId?: number
  cropId?: number
  from?: string
  to?: string
  limit?: number
}

async function fetchYieldRecords(params: YieldParams = {}): Promise<YieldRecord[]> {
  const { fieldId, cropId, from, to, limit = 200 } = params
  const { data } = await apiClient.get<YieldRecord[]>('/yield/', {
    params: {
      ...(fieldId && { field_id: fieldId }),
      ...(cropId && { crop_id: cropId }),
      ...(from && { from }),
      ...(to && { to }),
      limit,
    },
  })
  return data
}

async function createYieldRecord(payload: YieldRecordCreate): Promise<YieldRecord> {
  const { data } = await apiClient.post<YieldRecord>('/yield/', payload)
  return data
}

async function updateYieldRecord(id: number, payload: YieldRecordUpdate): Promise<YieldRecord> {
  const { data } = await apiClient.put<YieldRecord>(`/yield/${id}`, payload)
  return data
}

async function deleteYieldRecord(id: number): Promise<void> {
  await apiClient.delete(`/yield/${id}`)
}

export function useYieldRecords(params: YieldParams = {}) {
  return useQuery({
    queryKey: [...YIELD_KEY, params],
    queryFn: () => fetchYieldRecords(params),
  })
}

export function useCreateYieldRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createYieldRecord,
    onSuccess: () => qc.invalidateQueries({ queryKey: YIELD_KEY }),
  })
}

export function useUpdateYieldRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: YieldRecordUpdate }) =>
      updateYieldRecord(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: YIELD_KEY }),
  })
}

export function useDeleteYieldRecord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteYieldRecord,
    onSuccess: () => qc.invalidateQueries({ queryKey: YIELD_KEY }),
  })
}
