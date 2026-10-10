import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Farm, FarmCreate, FarmUpdate } from '@/types'
import { apiClient } from './client'

const FARMS_KEY = ['farms'] as const

export async function fetchFarms(): Promise<Farm[]> {
  const { data } = await apiClient.get<Farm[]>('/farms', { params: { limit: 500, offset: 0 } })
  return data
}

async function fetchFarm(id: string): Promise<Farm> {
  const { data } = await apiClient.get<Farm>(`/farms/${id}`)
  return data
}

async function createFarm(payload: FarmCreate): Promise<Farm> {
  const { data } = await apiClient.post<Farm>('/farms', payload)
  return data
}

async function updateFarm(id: string, payload: FarmUpdate): Promise<Farm> {
  const { data } = await apiClient.patch<Farm>(`/farms/${id}`, payload)
  return data
}

async function deleteFarm(id: string): Promise<void> {
  await apiClient.delete(`/farms/${id}`)
}

export function useFarms() {
  return useQuery({ queryKey: FARMS_KEY, queryFn: fetchFarms })
}

export function useFarm(id: string) {
  return useQuery({
    queryKey: [...FARMS_KEY, id],
    queryFn: () => fetchFarm(id),
    enabled: !!id,
  })
}

export function useCreateFarm() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createFarm,
    onSuccess: () => qc.invalidateQueries({ queryKey: FARMS_KEY }),
  })
}

export function useUpdateFarm() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: FarmUpdate }) =>
      updateFarm(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: FARMS_KEY }),
  })
}

export function useDeleteFarm() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteFarm,
    onSuccess: () => qc.invalidateQueries({ queryKey: FARMS_KEY }),
  })
}
