import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  Recommendation,
  RecommendationCreate,
  RecommendationUpdate,
} from '@/types'
import { apiClient } from './client'

const RECOMMENDATIONS_KEY = ['recommendations'] as const

async function fetchFieldRecommendations(
  fieldId: string,
  limit = 500,
): Promise<Recommendation[]> {
  const { data } = await apiClient.get<Recommendation[]>(
    `/fields/${fieldId}/recommendations`,
    { params: { limit, offset: 0 } },
  )
  return data
}

async function createRecommendation(
  fieldId: string,
  payload: RecommendationCreate,
): Promise<Recommendation> {
  const { data } = await apiClient.post<Recommendation>(
    `/fields/${fieldId}/recommendations`,
    payload,
  )
  return data
}

async function updateRecommendation(
  id: string,
  payload: RecommendationUpdate,
): Promise<Recommendation> {
  const { data } = await apiClient.patch<Recommendation>(
    `/recommendations/${id}`,
    payload,
  )
  return data
}

async function deleteRecommendation(id: string): Promise<void> {
  await apiClient.delete(`/recommendations/${id}`)
}

export function useFieldRecommendations(fieldId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: [...RECOMMENDATIONS_KEY, 'field', fieldId],
    queryFn: () => fetchFieldRecommendations(fieldId!),
    enabled: enabled && !!fieldId,
  })
}

/** Load recommendations for many fields (e.g. all fields in a farm). */
export function useRecommendationsForFieldIds(fieldIds: string[]) {
  const queries = useQueries({
    queries: fieldIds.map((fieldId) => ({
      queryKey: [...RECOMMENDATIONS_KEY, 'field', fieldId],
      queryFn: () => fetchFieldRecommendations(fieldId),
      enabled: fieldIds.length > 0,
    })),
  })

  const isLoading = queries.some((q) => q.isLoading)
  const isError = queries.some((q) => q.isError)
  const data = queries.flatMap((q) => q.data ?? [])
  const sorted = [...data].sort(
    (a, b) => new Date(b.valid_from).getTime() - new Date(a.valid_from).getTime(),
  )

  return { data: sorted, isLoading, isError }
}

export function useCreateRecommendation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      fieldId,
      payload,
    }: {
      fieldId: string
      payload: RecommendationCreate
    }) => createRecommendation(fieldId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: RECOMMENDATIONS_KEY }),
  })
}

export function useUpdateRecommendation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string
      payload: RecommendationUpdate
    }) => updateRecommendation(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: RECOMMENDATIONS_KEY }),
  })
}

export function useDeleteRecommendation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteRecommendation,
    onSuccess: () => qc.invalidateQueries({ queryKey: RECOMMENDATIONS_KEY }),
  })
}
