import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Field, FieldCreate, FieldUpdate, OffsetPaginatedResponse } from '@/types'
import { apiClient } from './client'
import { fetchFarms } from '@/api/farms'

const FIELDS_KEY = ['fields'] as const

async function fetchFieldsByFarm(farmId: string): Promise<Field[]> {
  const { data } = await apiClient.get<OffsetPaginatedResponse<Field>>(
    `/farms/${farmId}/fields`,
    { params: { limit: 500, offset: 0 } },
  )
  return data.items
}

async function fetchAllFields(): Promise<Field[]> {
  const farms = await fetchFarms()
  if (farms.length === 0) return []
  const batches = await Promise.all(farms.map((f) => fetchFieldsByFarm(f.id)))
  return batches.flat()
}

async function fetchField(id: string): Promise<Field> {
  const { data } = await apiClient.get<Field>(`/fields/${id}`)
  return data
}

async function createField(farmId: string, payload: FieldCreate): Promise<Field> {
  const { data } = await apiClient.post<Field>(`/farms/${farmId}/fields`, payload)
  return data
}

async function updateField(id: string, payload: FieldUpdate): Promise<Field> {
  const { data } = await apiClient.patch<Field>(`/fields/${id}`, payload)
  return data
}

async function deleteField(id: string): Promise<void> {
  await apiClient.delete(`/fields/${id}`)
}

export function useFields(farmId?: string) {
  return useQuery({
    queryKey: farmId ? [...FIELDS_KEY, 'farm', farmId] : [...FIELDS_KEY, 'all'],
    queryFn: () => (farmId ? fetchFieldsByFarm(farmId) : fetchAllFields()),
  })
}

export function useField(id: string) {
  return useQuery({
    queryKey: [...FIELDS_KEY, id],
    queryFn: () => fetchField(id),
    enabled: !!id,
  })
}

export function useCreateField() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ farmId, payload }: { farmId: string; payload: FieldCreate }) =>
      createField(farmId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: FIELDS_KEY }),
  })
}

export function useUpdateField() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: FieldUpdate }) =>
      updateField(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: FIELDS_KEY }),
  })
}

export function useDeleteField() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteField,
    onSuccess: () => qc.invalidateQueries({ queryKey: FIELDS_KEY }),
  })
}
