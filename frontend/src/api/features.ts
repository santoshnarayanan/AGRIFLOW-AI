import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type {
  FeatureCatalogResponse,
  FieldFeatureSnapshot,
  FieldFeatureSnapshotListResponse,
} from '@/types'
import { apiClient } from './client'

const FEATURES_KEY = ['features'] as const

async function fetchFeatureCatalog(): Promise<FeatureCatalogResponse> {
  const { data } = await apiClient.get<FeatureCatalogResponse>('/features/catalog')
  return data
}

async function fetchFieldSnapshots(fieldId: string): Promise<FieldFeatureSnapshotListResponse> {
  const { data } = await apiClient.get<FieldFeatureSnapshotListResponse>(
    `/features/fields/${fieldId}/snapshots`,
    { params: { limit: 20, offset: 0 } },
  )
  return data
}

async function materializeFieldFeatures(fieldId: string): Promise<FieldFeatureSnapshot> {
  const { data } = await apiClient.post<FieldFeatureSnapshot>(
    `/features/fields/${fieldId}/materialize`,
    {},
  )
  return data
}

export function useFeatureCatalog() {
  return useQuery({
    queryKey: [...FEATURES_KEY, 'catalog'],
    queryFn: fetchFeatureCatalog,
  })
}

export function useFieldFeatureSnapshots(fieldId: string | null) {
  return useQuery({
    queryKey: [...FEATURES_KEY, 'snapshots', fieldId],
    queryFn: () => fetchFieldSnapshots(fieldId!),
    enabled: Boolean(fieldId),
  })
}

export function useMaterializeFieldFeatures() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (fieldId: string) => materializeFieldFeatures(fieldId),
    onSuccess: (_snapshot, fieldId) => {
      queryClient.invalidateQueries({ queryKey: [...FEATURES_KEY, 'snapshots', fieldId] })
    },
  })
}
