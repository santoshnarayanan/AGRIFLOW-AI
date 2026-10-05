import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  SatelliteAnalysis, SatelliteAnalysisCreate, SatelliteAnalysisUpdate,
} from '@/types'
import { apiClient } from './client'

const SATELLITE_KEY = ['satellite'] as const

interface SatelliteParams {
  fieldId?: number
  from?: string
  to?: string
  limit?: number
}

async function fetchSatelliteAnalyses(params: SatelliteParams = {}): Promise<SatelliteAnalysis[]> {
  const { fieldId, from, to, limit = 200 } = params
  const { data } = await apiClient.get<SatelliteAnalysis[]>('/satellite/', {
    params: {
      ...(fieldId && { field_id: fieldId }),
      ...(from && { from }),
      ...(to && { to }),
      limit,
    },
  })
  return data
}

async function createSatelliteAnalysis(
  payload: SatelliteAnalysisCreate,
): Promise<SatelliteAnalysis> {
  const { data } = await apiClient.post<SatelliteAnalysis>('/satellite/', payload)
  return data
}

async function updateSatelliteAnalysis(
  id: number, payload: SatelliteAnalysisUpdate,
): Promise<SatelliteAnalysis> {
  const { data } = await apiClient.put<SatelliteAnalysis>(`/satellite/${id}`, payload)
  return data
}

async function deleteSatelliteAnalysis(id: number): Promise<void> {
  await apiClient.delete(`/satellite/${id}`)
}

export function useSatelliteAnalyses(params: SatelliteParams = {}) {
  return useQuery({
    queryKey: [...SATELLITE_KEY, params],
    queryFn: () => fetchSatelliteAnalyses(params),
  })
}

export function useCreateSatelliteAnalysis() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createSatelliteAnalysis,
    onSuccess: () => qc.invalidateQueries({ queryKey: SATELLITE_KEY }),
  })
}

export function useUpdateSatelliteAnalysis() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: SatelliteAnalysisUpdate }) =>
      updateSatelliteAnalysis(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: SATELLITE_KEY }),
  })
}

export function useDeleteSatelliteAnalysis() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteSatelliteAnalysis,
    onSuccess: () => qc.invalidateQueries({ queryKey: SATELLITE_KEY }),
  })
}
