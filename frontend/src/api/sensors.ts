import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { SensorReading, SensorReadingCreate, SensorType } from '@/types'
import { apiClient } from './client'

const SENSORS_KEY = ['sensors'] as const

interface SensorParams {
  fieldId?: number
  sensorType?: SensorType
  from?: string
  to?: string
  limit?: number
}

async function fetchSensorReadings(params: SensorParams = {}): Promise<SensorReading[]> {
  const { fieldId, sensorType, from, to, limit = 300 } = params
  const { data } = await apiClient.get<SensorReading[]>('/sensors/', {
    params: {
      ...(fieldId && { field_id: fieldId }),
      ...(sensorType && { sensor_type: sensorType }),
      ...(from && { from }),
      ...(to && { to }),
      limit,
    },
  })
  return data
}

async function createSensorReading(payload: SensorReadingCreate): Promise<SensorReading> {
  const { data } = await apiClient.post<SensorReading>('/sensors/', payload)
  return data
}

async function deleteSensorReading(id: number): Promise<void> {
  await apiClient.delete(`/sensors/${id}`)
}

export function useSensorReadings(params: SensorParams = {}) {
  return useQuery({
    queryKey: [...SENSORS_KEY, params],
    queryFn: () => fetchSensorReadings(params),
  })
}

export function useCreateSensorReading() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createSensorReading,
    onSuccess: () => qc.invalidateQueries({ queryKey: SENSORS_KEY }),
  })
}

export function useDeleteSensorReading() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteSensorReading,
    onSuccess: () => qc.invalidateQueries({ queryKey: SENSORS_KEY }),
  })
}
