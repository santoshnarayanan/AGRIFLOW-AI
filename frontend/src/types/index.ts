// ─── Shared ───────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}

// ─── Farm ─────────────────────────────────────────────────────────────────────

export interface Farm {
  id: number
  name: string
  location: string | null
  area: number | null
  created_at: string
  updated_at: string
}

export interface FarmCreate {
  name: string
  location?: string
  area?: number
}

export interface FarmUpdate {
  name?: string
  location?: string
  area?: number
}

// ─── Field ────────────────────────────────────────────────────────────────────

export interface Field {
  id: number
  farm_id: number
  name: string
  area: number | null
  location: string | null
  created_at: string
  updated_at: string
}

// ─── Alert ────────────────────────────────────────────────────────────────────

export type AlertType =
  | 'soil_moisture_low' | 'soil_moisture_high'
  | 'temperature_extreme' | 'frost_risk' | 'drought_risk'
  | 'disease_risk_high' | 'pest_detected'
  | 'irrigation_required' | 'yield_anomaly' | 'sensor_malfunction'

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low'

export interface Alert {
  id: number
  field_id: number
  crop_id: number | null
  alert_type: AlertType
  severity: AlertSeverity
  message: string
  triggered_at: string
  is_resolved: boolean
  created_at: string
}

// ─── Recommendation ───────────────────────────────────────────────────────────

export type RecommendationType =
  | 'irrigation' | 'fertilization' | 'pest_control'
  | 'harvest_timing' | 'planting_schedule' | 'soil_amendment'

export type RecommendationStatus =
  | 'pending' | 'acknowledged' | 'implemented'
  | 'rejected' | 'expired' | 'superseded'

export type RecommendationPriority = 'critical' | 'high' | 'medium'

export interface Recommendation {
  id: number
  field_id: number
  crop_id: number | null
  recommendation_type: RecommendationType
  status: RecommendationStatus
  priority: RecommendationPriority
  confidence_score: number
  engine_version: string | null
  message: string
  created_at: string
}
