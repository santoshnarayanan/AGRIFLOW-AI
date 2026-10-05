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

// ─── Disease Observation ──────────────────────────────────────────────────────

export type DiseaseSeverity = 'low' | 'moderate' | 'high' | 'critical'

export interface DiseaseObservation {
  id: number
  field_id: number
  crop_id: number | null
  disease_name: string
  severity: DiseaseSeverity
  affected_area_percentage: number | null
  symptoms: string | null
  observed_at: string
  treatment_applied: string | null
  treatment_date: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface DiseaseObservationCreate {
  field_id: number
  crop_id?: number
  disease_name: string
  severity: DiseaseSeverity
  affected_area_percentage?: number
  symptoms?: string
  observed_at: string
  treatment_applied?: string
  treatment_date?: string
  notes?: string
}

export interface DiseaseObservationUpdate {
  crop_id?: number | null
  disease_name?: string
  severity?: DiseaseSeverity
  affected_area_percentage?: number
  symptoms?: string
  treatment_applied?: string
  treatment_date?: string
  notes?: string
}

// ─── Yield Record ─────────────────────────────────────────────────────────────

export type YieldGrade = 'premium' | 'grade_a' | 'grade_b' | 'grade_c' | 'commercial' | 'reject'

export interface YieldRecord {
  id: number
  field_id: number
  crop_id: number | null
  harvest_date: string
  quantity: number
  unit: string
  quality_grade: YieldGrade | null
  moisture_content: number | null
  area_harvested: number | null
  yield_per_hectare: number | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface YieldRecordCreate {
  field_id: number
  crop_id?: number
  harvest_date: string
  quantity: number
  unit: string
  quality_grade?: YieldGrade
  moisture_content?: number
  area_harvested?: number
  yield_per_hectare?: number
  notes?: string
}

export interface YieldRecordUpdate {
  crop_id?: number | null
  quantity?: number
  unit?: string
  quality_grade?: YieldGrade | null
  moisture_content?: number
  area_harvested?: number
  yield_per_hectare?: number
  notes?: string
}

// ─── Irrigation Event ─────────────────────────────────────────────────────────

export type IrrigationMethod =
  | 'drip' | 'sprinkler' | 'flood' | 'furrow' | 'center_pivot' | 'subsurface'

export interface IrrigationEvent {
  id: number
  field_id: number
  crop_id: number | null
  start_time: string
  end_time: string | null
  duration_minutes: number | null
  water_amount: number | null
  irrigation_method: IrrigationMethod
  notes: string | null
  created_at: string
  updated_at: string
}

export interface IrrigationEventCreate {
  field_id: number
  crop_id?: number
  start_time: string
  end_time?: string
  duration_minutes?: number
  water_amount?: number
  irrigation_method: IrrigationMethod
  notes?: string
}

export interface IrrigationEventUpdate {
  crop_id?: number | null
  end_time?: string
  duration_minutes?: number
  water_amount?: number
  irrigation_method?: IrrigationMethod
  notes?: string
}

// ─── Sensor Reading ───────────────────────────────────────────────────────────

export type SensorType =
  | 'soil_moisture' | 'soil_temperature'
  | 'air_temperature' | 'air_humidity'
  | 'light_intensity' | 'co2_level'
  | 'electrical_conductivity' | 'leaf_wetness'

export interface SensorReading {
  id: number
  field_id: number
  sensor_id: string | null
  sensor_type: SensorType
  value: number
  unit: string
  quality_flag: string | null
  recorded_at: string   // immutable once written — ADR enforced
  created_at: string
}

export interface SensorReadingCreate {
  field_id: number
  sensor_id?: string
  sensor_type: SensorType
  value: number
  unit: string
  quality_flag?: string
  recorded_at: string
}

// ─── Weather Observation ──────────────────────────────────────────────────────

export interface WeatherObservation {
  id: number
  field_id: number
  temperature: number | null
  humidity: number | null
  rainfall: number | null
  wind_speed: number | null
  wind_direction: number | null
  solar_radiation: number | null
  atmospheric_pressure: number | null
  recorded_at: string
  created_at: string
}

export interface WeatherObservationCreate {
  field_id: number
  temperature?: number
  humidity?: number
  rainfall?: number
  wind_speed?: number
  wind_direction?: number
  solar_radiation?: number
  atmospheric_pressure?: number
  recorded_at: string
}

// ─── Soil Profile ─────────────────────────────────────────────────────────────

export type SoilTexture =
  | 'sandy' | 'sandy_loam' | 'loam' | 'silt_loam'
  | 'silt' | 'clay_loam' | 'clay' | 'peat'

export interface SoilProfile {
  id: number
  field_id: number
  ph_level: number | null
  nitrogen_content: number | null
  phosphorus_content: number | null
  potassium_content: number | null
  organic_matter: number | null
  moisture_content: number | null
  texture: SoilTexture | null
  notes: string | null
  recorded_at: string | null
  created_at: string
  updated_at: string
}

export interface SoilProfileCreate {
  field_id: number
  ph_level?: number
  nitrogen_content?: number
  phosphorus_content?: number
  potassium_content?: number
  organic_matter?: number
  moisture_content?: number
  texture?: SoilTexture
  notes?: string
  recorded_at?: string
}

export interface SoilProfileUpdate {
  ph_level?: number
  nitrogen_content?: number
  phosphorus_content?: number
  potassium_content?: number
  organic_matter?: number
  moisture_content?: number
  texture?: SoilTexture
  notes?: string
  recorded_at?: string
}

// ─── Crop ─────────────────────────────────────────────────────────────────────

export type GrowthStage =
  | 'seedling' | 'vegetative' | 'flowering'
  | 'fruiting' | 'ripening' | 'harvested'

export type CropStatus = 'planned' | 'active' | 'harvested' | 'failed'

export interface Crop {
  id: number
  field_id: number
  name: string
  variety: string | null
  growth_stage: GrowthStage
  planting_date: string | null
  expected_harvest_date: string | null
  actual_harvest_date: string | null
  status: CropStatus
  created_at: string
  updated_at: string
}

export interface CropCreate {
  field_id: number
  name: string
  variety?: string
  growth_stage?: GrowthStage
  planting_date?: string
  expected_harvest_date?: string
  status?: CropStatus
}

export interface CropUpdate {
  name?: string
  variety?: string
  growth_stage?: GrowthStage
  planting_date?: string
  expected_harvest_date?: string
  actual_harvest_date?: string
  status?: CropStatus
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
