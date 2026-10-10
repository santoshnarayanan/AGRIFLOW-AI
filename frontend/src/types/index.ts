// ─── Shared ───────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}

/** Backend list endpoints use limit/offset (see app.schemas.common.PaginatedResponse). */
export interface OffsetPaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

// ─── Farm ─────────────────────────────────────────────────────────────────────

export interface Farm {
  id: string
  farm_code: string
  farm_name: string
  owner_name: string
  country: string
  state: string
  city: string
  latitude: string | number
  longitude: string | number
  total_area_hectares: string | number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface FarmCreate {
  farm_code: string
  farm_name: string
  owner_name: string
  country: string
  state: string
  city: string
  latitude: number
  longitude: number
  total_area_hectares: number
  is_active?: boolean
}

export interface FarmUpdate {
  farm_name?: string
  owner_name?: string
  country?: string
  state?: string
  city?: string
  latitude?: number
  longitude?: number
  total_area_hectares?: number
  is_active?: boolean
}

// ─── Field ────────────────────────────────────────────────────────────────────

export interface Field {
  id: string
  farm_id: string
  name: string
  area_hectares: string | number | null
  soil_type: string | null
  latitude: string | number | null
  longitude: string | number | null
  elevation_m: string | number | null
  created_at: string
  updated_at: string
}

export interface FieldCreate {
  name: string
  area_hectares?: number
  soil_type?: string
  latitude?: number
  longitude?: number
  elevation_m?: number
}

export interface FieldUpdate {
  name?: string
  area_hectares?: number
  soil_type?: string
  latitude?: number
  longitude?: number
  elevation_m?: number
}

// ─── Satellite Analysis ───────────────────────────────────────────────────────

export type SatelliteSource =
  | 'sentinel_2' | 'landsat_8' | 'landsat_9' | 'planet' | 'modis' | 'spot'

export interface SatelliteAnalysis {
  id: number
  field_id: string
  acquisition_date: string
  satellite_source: SatelliteSource | null
  cloud_cover_percentage: number | null
  ndvi: number | null
  ndwi: number | null
  ndre: number | null
  evi: number | null
  image_url: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface SatelliteAnalysisCreate {
  field_id: string
  acquisition_date: string
  satellite_source?: SatelliteSource
  cloud_cover_percentage?: number
  ndvi?: number
  ndwi?: number
  ndre?: number
  evi?: number
  image_url?: string
  notes?: string
}

export interface SatelliteAnalysisUpdate {
  satellite_source?: SatelliteSource
  cloud_cover_percentage?: number
  ndvi?: number
  ndwi?: number
  ndre?: number
  evi?: number
  image_url?: string
  notes?: string
}

// ─── Disease Observation ──────────────────────────────────────────────────────

export type DiseaseSeverity = 'low' | 'moderate' | 'high' | 'critical'

export interface DiseaseObservation {
  id: number
  field_id: string
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
  field_id: string
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
  field_id: string
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
  field_id: string
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
  field_id: string
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
  field_id: string
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
  field_id: string
  sensor_id: string | null
  sensor_type: SensorType
  value: number
  unit: string
  quality_flag: string | null
  recorded_at: string   // immutable once written — ADR enforced
  created_at: string
}

export interface SensorReadingCreate {
  field_id: string
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
  field_id: string
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
  field_id: string
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
  field_id: string
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
  field_id: string
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
  id: string
  field_id: string
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

// ─── Alert (Phase 13 — matches FastAPI schemas) ──────────────────────────────

export type AlertType =
  | 'SOIL_MOISTURE_LOW'
  | 'SOIL_MOISTURE_HIGH'
  | 'DISEASE_RISK_HIGH'
  | 'DISEASE_OUTBREAK'
  | 'FROST_RISK'
  | 'HEAT_STRESS'
  | 'DROUGHT_STRESS'
  | 'SENSOR_ANOMALY'
  | 'IRRIGATION_OVERDUE'
  | 'HARVEST_WINDOW_OPEN'

export type AlertSeverity = 'INFO' | 'WARNING' | 'HIGH' | 'CRITICAL'

export interface Alert {
  id: string
  field_id: string
  crop_id: string | null
  recommendation_id: string | null
  alert_type: AlertType
  severity: AlertSeverity
  title: string
  message: string
  triggered_at: string
  expires_at: string | null
  is_acknowledged: boolean
  acknowledged_at: string | null
  source_metric: string | null
  source_value: number | null
  threshold_value: number | null
  created_at: string
  updated_at: string
}

export interface AlertCreate {
  crop_id?: string | null
  recommendation_id?: string | null
  alert_type: AlertType
  severity: AlertSeverity
  title: string
  message: string
  triggered_at: string
  expires_at?: string | null
  source_metric?: string | null
  source_value?: number | null
  threshold_value?: number | null
}

export interface AlertUpdate {
  severity?: AlertSeverity
  title?: string
  message?: string
  is_acknowledged?: boolean
  expires_at?: string | null
}

// ─── Recommendation (Phase 13 — matches FastAPI schemas) ─────────────────────

export type RecommendationType =
  | 'IRRIGATION'
  | 'DISEASE_TREATMENT'
  | 'FERTILIZATION'
  | 'HARVEST_TIMING'
  | 'SOIL_AMENDMENT'
  | 'GENERAL'

export type RecommendationStatus =
  | 'PENDING'
  | 'ACTIVE'
  | 'ACKNOWLEDGED'
  | 'SUPERSEDED'
  | 'EXPIRED'
  | 'DISMISSED'

export type RecommendationPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface Recommendation {
  id: string
  field_id: string
  crop_id: string | null
  recommendation_type: RecommendationType
  status: RecommendationStatus
  priority: RecommendationPriority
  title: string
  description: string | null
  recommended_action: string
  recommended_value: number | null
  recommended_unit: string | null
  confidence_score: number | null
  evidence_summary: string | null
  engine_version: string | null
  valid_from: string
  valid_until: string | null
  acknowledged_at: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface RecommendationCreate {
  crop_id?: string | null
  recommendation_type: RecommendationType
  priority?: RecommendationPriority
  title: string
  description?: string | null
  recommended_action: string
  recommended_value?: number | null
  recommended_unit?: string | null
  confidence_score?: number | null
  evidence_summary?: string | null
  engine_version?: string | null
  valid_from: string
  valid_until?: string | null
  notes?: string | null
}

export interface RecommendationUpdate {
  status?: RecommendationStatus
  priority?: RecommendationPriority
  title?: string
  description?: string | null
  recommended_action?: string
  recommended_value?: number | null
  recommended_unit?: string | null
  confidence_score?: number | null
  evidence_summary?: string | null
  valid_until?: string | null
  notes?: string | null
}
