import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Field } from '@/types'
import { apiClient } from './client'

const FIELDS_KEY = ['fields'] as const

export interface FieldCreate {
  farm_id: number
  name: string
  area?: number
  location?: string
}

export interface FieldUpdate {
  name?: string
  area?: number
  location?: string
}

async function fetchFields(farmId?: number): Promise<Field[]> {
  const params = farmId ? { farm_id: farmId } : {}
  const { data } = await apiClient.get<Field[]>('/fields/', { params })
  return data
}

async function fetchField(id: number): Promise<Field> {
  const { data } = await apiClient.get<Field>(`/fields/${id}`)
  return data
}

async function createField(payload: FieldCreate): Promise<Field> {
  const { data } = await apiClient.post<Field>('/fields/', payload)
  return data
}

async function updateField(id: number, payload: FieldUpdate): Promise<Field> {
  const { data } = await apiClient.put<Field>(`/fields/${id}`, payload)
  return data
}

async function deleteField(id: number): Promise<void> {
  await apiClient.delete(`/fields/${id}`)
}

export function useFields(farmId?: number) {
  return useQuery({
    queryKey: farmId ? [...FIELDS_KEY, 'farm', farmId] : FIELDS_KEY,
    queryFn: () => fetchFields(farmId),
  })
}

export function useField(id: number) {
  return useQuery({ queryKey: [...FIELDS_KEY, id], queryFn: () => fetchField(id) })
}

export function useCreateField() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createField,
    onSuccess: () => qc.invalidateQueries({ queryKey: FIELDS_KEY }),
  })
}

export function useUpdateField() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: FieldUpdate }) =>
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
