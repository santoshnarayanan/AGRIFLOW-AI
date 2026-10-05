import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  IrrigationEvent, IrrigationEventCreate, IrrigationEventUpdate,
} from '@/types'
import { apiClient } from './client'

const IRRIGATION_KEY = ['irrigation'] as const

interface IrrigationParams {
  fieldId?: number
  cropId?: number
  from?: string
  to?: string
  limit?: number
}

async function fetchIrrigationEvents(params: IrrigationParams = {}): Promise<IrrigationEvent[]> {
  const { fieldId, cropId, from, to, limit = 200 } = params
  const { data } = await apiClient.get<IrrigationEvent[]>('/irrigation/', {
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

async function createIrrigationEvent(payload: IrrigationEventCreate): Promise<IrrigationEvent> {
  const { data } = await apiClient.post<IrrigationEvent>('/irrigation/', payload)
  return data
}

async function updateIrrigationEvent(
  id: number, payload: IrrigationEventUpdate,
): Promise<IrrigationEvent> {
  const { data } = await apiClient.put<IrrigationEvent>(`/irrigation/${id}`, payload)
  return data
}

async function deleteIrrigationEvent(id: number): Promise<void> {
  await apiClient.delete(`/irrigation/${id}`)
}

export function useIrrigationEvents(params: IrrigationParams = {}) {
  return useQuery({
    queryKey: [...IRRIGATION_KEY, params],
    queryFn: () => fetchIrrigationEvents(params),
  })
}

export function useCreateIrrigationEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createIrrigationEvent,
    onSuccess: () => qc.invalidateQueries({ queryKey: IRRIGATION_KEY }),
  })
}

export function useUpdateIrrigationEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: IrrigationEventUpdate }) =>
      updateIrrigationEvent(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: IRRIGATION_KEY }),
  })
}

export function useDeleteIrrigationEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteIrrigationEvent,
    onSuccess: () => qc.invalidateQueries({ queryKey: IRRIGATION_KEY }),
  })
}
