import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Crop, CropCreate, CropUpdate, OffsetPaginatedResponse } from '@/types'
import { apiClient } from './client'
import { fetchFarms } from '@/api/farms'

const CROPS_KEY = ['crops'] as const

async function fetchCropsByField(fieldId: string): Promise<Crop[]> {
  const { data } = await apiClient.get<OffsetPaginatedResponse<Crop>>(
    `/fields/${fieldId}/crops`,
    { params: { limit: 500, offset: 0 } },
  )
  return data.items
}

async function fetchAllCrops(): Promise<Crop[]> {
  const farms = await fetchFarms()
  const fieldBatches = await Promise.all(
    farms.map(async (farm) => {
      const { data } = await apiClient.get<OffsetPaginatedResponse<{ id: string }>>(
        `/farms/${farm.id}/fields`,
        { params: { limit: 500, offset: 0 } },
      )
      return data.items
    }),
  )
  const fieldIds = fieldBatches.flat().map((f) => f.id)
  if (fieldIds.length === 0) return []
  const cropBatches = await Promise.all(fieldIds.map((id) => fetchCropsByField(id)))
  return cropBatches.flat()
}

async function fetchCrop(id: string): Promise<Crop> {
  const { data } = await apiClient.get<Crop>(`/crops/${id}`)
  return data
}

async function createCrop(fieldId: string, payload: CropCreate): Promise<Crop> {
  const { data } = await apiClient.post<Crop>(`/fields/${fieldId}/crops`, payload)
  return data
}

async function updateCrop(id: string, payload: CropUpdate): Promise<Crop> {
  const { data } = await apiClient.patch<Crop>(`/crops/${id}`, payload)
  return data
}

async function deleteCrop(id: string): Promise<void> {
  await apiClient.delete(`/crops/${id}`)
}

export function useCrops(fieldId?: string) {
  return useQuery({
    queryKey: fieldId ? [...CROPS_KEY, 'field', fieldId] : [...CROPS_KEY, 'all'],
    queryFn: () => (fieldId ? fetchCropsByField(fieldId) : fetchAllCrops()),
  })
}

export function useCrop(id: string) {
  return useQuery({
    queryKey: [...CROPS_KEY, id],
    queryFn: () => fetchCrop(id),
    enabled: !!id,
  })
}

export function useCreateCrop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ fieldId, payload }: { fieldId: string; payload: CropCreate }) =>
      createCrop(fieldId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: CROPS_KEY }),
  })
}

export function useUpdateCrop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CropUpdate }) =>
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
