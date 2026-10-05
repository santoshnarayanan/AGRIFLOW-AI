import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Crop, CropCreate, CropUpdate } from '@/types'
import { apiClient } from './client'

const CROPS_KEY = ['crops'] as const

async function fetchCrops(fieldId?: number): Promise<Crop[]> {
  const params = fieldId ? { field_id: fieldId } : {}
  const { data } = await apiClient.get<Crop[]>('/crops/', { params })
  return data
}

async function fetchCrop(id: number): Promise<Crop> {
  const { data } = await apiClient.get<Crop>(`/crops/${id}`)
  return data
}

async function createCrop(payload: CropCreate): Promise<Crop> {
  const { data } = await apiClient.post<Crop>('/crops/', payload)
  return data
}

async function updateCrop(id: number, payload: CropUpdate): Promise<Crop> {
  const { data } = await apiClient.put<Crop>(`/crops/${id}`, payload)
  return data
}

async function deleteCrop(id: number): Promise<void> {
  await apiClient.delete(`/crops/${id}`)
}

export function useCrops(fieldId?: number) {
  return useQuery({
    queryKey: fieldId ? [...CROPS_KEY, 'field', fieldId] : CROPS_KEY,
    queryFn: () => fetchCrops(fieldId),
  })
}

export function useCrop(id: number) {
  return useQuery({ queryKey: [...CROPS_KEY, id], queryFn: () => fetchCrop(id) })
}

export function useCreateCrop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createCrop,
    onSuccess: () => qc.invalidateQueries({ queryKey: CROPS_KEY }),
  })
}

export function useUpdateCrop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: CropUpdate }) =>
      updateCrop(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: CROPS_KEY }),
  })
}

export function useDeleteCrop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteCrop,
    onSuccess: () => qc.invalidateQueries({ queryKey: CROPS_KEY }),
  })
}
