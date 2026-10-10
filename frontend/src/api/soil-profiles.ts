import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { SoilProfile, SoilProfileCreate, SoilProfileUpdate } from '@/types'
import { apiClient } from './client'

const SOIL_KEY = ['soil-profiles'] as const

async function fetchSoilProfiles(fieldId?: string): Promise<SoilProfile[]> {
  const params = fieldId ? { field_id: fieldId } : {}
  const { data } = await apiClient.get<SoilProfile[]>('/soil-profiles/', { params })
  return data
}

async function createSoilProfile(payload: SoilProfileCreate): Promise<SoilProfile> {
  const { data } = await apiClient.post<SoilProfile>('/soil-profiles/', payload)
  return data
}

async function updateSoilProfile(id: number, payload: SoilProfileUpdate): Promise<SoilProfile> {
  const { data } = await apiClient.put<SoilProfile>(`/soil-profiles/${id}`, payload)
  return data
}

async function deleteSoilProfile(id: number): Promise<void> {
  await apiClient.delete(`/soil-profiles/${id}`)
}

export function useSoilProfiles(fieldId?: string) {
  return useQuery({
    queryKey: fieldId ? [...SOIL_KEY, 'field', fieldId] : SOIL_KEY,
    queryFn: () => fetchSoilProfiles(fieldId),
  })
}

export function useCreateSoilProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createSoilProfile,
    onSuccess: () => qc.invalidateQueries({ queryKey: SOIL_KEY }),
  })
}

export function useUpdateSoilProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: SoilProfileUpdate }) =>
      updateSoilProfile(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: SOIL_KEY }),
  })
}

export function useDeleteSoilProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteSoilProfile,
    onSuccess: () => qc.invalidateQueries({ queryKey: SOIL_KEY }),
  })
}
