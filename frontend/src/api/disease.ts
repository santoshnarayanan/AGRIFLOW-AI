import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  DiseaseObservation, DiseaseObservationCreate, DiseaseObservationUpdate, DiseaseSeverity,
} from '@/types'
import { apiClient } from './client'

const DISEASE_KEY = ['disease'] as const

interface DiseaseParams {
  fieldId?: number
  cropId?: number
  severity?: DiseaseSeverity
  from?: string
  to?: string
  limit?: number
}

async function fetchDiseaseObservations(params: DiseaseParams = {}): Promise<DiseaseObservation[]> {
  const { fieldId, cropId, severity, from, to, limit = 200 } = params
  const { data } = await apiClient.get<DiseaseObservation[]>('/disease/', {
    params: {
      ...(fieldId && { field_id: fieldId }),
      ...(cropId && { crop_id: cropId }),
      ...(severity && { severity }),
      ...(from && { from }),
      ...(to && { to }),
      limit,
    },
  })
  return data
}

async function createDiseaseObservation(payload: DiseaseObservationCreate): Promise<DiseaseObservation> {
  const { data } = await apiClient.post<DiseaseObservation>('/disease/', payload)
  return data
}

async function updateDiseaseObservation(
  id: number, payload: DiseaseObservationUpdate,
): Promise<DiseaseObservation> {
  const { data } = await apiClient.put<DiseaseObservation>(`/disease/${id}`, payload)
  return data
}

async function deleteDiseaseObservation(id: number): Promise<void> {
  await apiClient.delete(`/disease/${id}`)
}

export function useDiseaseObservations(params: DiseaseParams = {}) {
  return useQuery({
    queryKey: [...DISEASE_KEY, params],
    queryFn: () => fetchDiseaseObservations(params),
  })
}

export function useCreateDiseaseObservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createDiseaseObservation,
    onSuccess: () => qc.invalidateQueries({ queryKey: DISEASE_KEY }),
  })
}

export function useUpdateDiseaseObservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: DiseaseObservationUpdate }) =>
      updateDiseaseObservation(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: DISEASE_KEY }),
  })
}

export function useDeleteDiseaseObservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteDiseaseObservation,
    onSuccess: () => qc.invalidateQueries({ queryKey: DISEASE_KEY }),
  })
}
