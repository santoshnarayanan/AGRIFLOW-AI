# AI Data Readiness Assessment

**Document:** Phase 6 – Step 1  
**Date:** June 2026  
**Author:** AGRIFLOW-AI Architecture Team  
**Status:** Approved for Implementation Planning  

---

## Purpose

This document assesses the readiness of the current AGRIFLOW-AI domain models to support AI and machine learning use cases. It identifies what data is currently available, what AI use cases are already partially supportable, and precisely what attributes are missing before each AI capability can be built.

The assessment covers four target AI capabilities:

1. **Yield Prediction** — Forecast expected harvest tonnage per field per crop cycle
2. **Disease Prediction** — Early detection of disease and pest risk using environmental signals
3. **Irrigation Optimization** — Recommend optimal irrigation schedules based on soil moisture, ET, and crop demand
4. **Weather Intelligence** — Field-level weather pattern analysis, anomaly detection, and forecast integration

> **Scope:** Documentation only. No models, migrations, repositories, services, or APIs are modified by this document.

---

## Domain Hierarchy

```
Farm
 └── Field
      ├── Crop             (one-to-many)
      ├── SoilProfile      (one-to-one)
      └── WeatherRecord    (one-to-many, time-series)
```

All models inherit `AuditableModel`, which provides:
- `id` — UUID v4 primary key
- `created_at` — server-side timestamp
- `updated_at` — server-side timestamp

---

## Section 1 — Current Domain Model Inventory

### 1.1 Farm

**Table:** `farms`

| Attribute | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | No | Primary key |
| `farm_code` | String(50) | No | Human-readable identifier |
| `farm_name` | String(255) | No | Display name |
| `owner_name` | String(255) | No | Farm owner or operator |
| `country` | String(100) | No | Country |
| `state` | String(100) | No | State or province |
| `city` | String(100) | No | Nearest municipality |
| `latitude` | Numeric(9,6) | No | WGS-84 latitude |
| `longitude` | Numeric(10,6) | No | WGS-84 longitude |
| `total_area_hectares` | Numeric(12,4) | No | Total farm area in hectares |
| `is_active` | Boolean | No | Soft-delete flag |
| `created_at` | Timestamp TZ | No | Audit timestamp |
| `updated_at` | Timestamp TZ | No | Audit timestamp |

**Current AI Utility:** Geographic context for weather and climate zone assignment. Insufficient alone for any AI model.

---

### 1.2 Field

**Table:** `fields`

| Attribute | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | No | Primary key |
| `farm_id` | UUID (FK) | No | Parent farm |
| `name` | String(255) | No | Display name |
| `area_hectares` | Numeric(10,2) | Yes | Field area |
| `soil_type` | String(50) | Yes | Free-text soil classification |
| `latitude` | Numeric(10,6) | Yes | WGS-84 latitude |
| `longitude` | Numeric(10,6) | Yes | WGS-84 longitude |
| `created_at` | Timestamp TZ | No | Audit timestamp |
| `updated_at` | Timestamp TZ | No | Audit timestamp |

**Current AI Utility:** Field area enables per-hectare normalisation of yield calculations. Lat/lng enables geo-spatial weather lookups. Soil type (free-text) provides weak signal for soil matching.

---

### 1.3 Crop

**Table:** `crops`

| Attribute | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | No | Primary key |
| `field_id` | UUID (FK) | No | Parent field |
| `crop_name` | String(255) | No | Common crop name |
| `crop_variety` | String(255) | Yes | Cultivar designation |
| `planting_date` | Date | No | Planting calendar date |
| `expected_harvest_date` | Date | Yes | Projected harvest date |
| `actual_harvest_date` | Date | Yes | Actual harvest completion |
| `status` | Enum | No | PLANNED / PLANTED / GROWING / HARVESTED |
| `created_at` | Timestamp TZ | No | Audit timestamp |
| `updated_at` | Timestamp TZ | No | Audit timestamp |

**Current AI Utility:** Planting-to-harvest window enables growing season duration analysis. Status enables basic lifecycle filtering. No quantitative output (yield) is recorded — a critical gap for supervised learning.

---

### 1.4 SoilProfile

**Table:** `soil_profiles`

| Attribute | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | No | Primary key |
| `field_id` | UUID (FK, UNIQUE) | No | Parent field (one-to-one) |
| `soil_type` | Enum | No | SANDY / CLAY / LOAM / SILT / PEAT / CHALK |
| `ph` | Numeric(4,2) | Yes | pH on 0–14 scale |
| `organic_matter` | Numeric(6,3) | Yes | % by weight |
| `nitrogen` | Numeric(8,4) | Yes | mg/kg (ppm) |
| `phosphorus` | Numeric(8,4) | Yes | mg/kg (ppm) |
| `potassium` | Numeric(8,4) | Yes | mg/kg (ppm) |
| `notes` | Text | Yes | Agronomist free-text |
| `created_at` | Timestamp TZ | No | Audit timestamp |
| `updated_at` | Timestamp TZ | No | Audit timestamp |

**Current AI Utility:** NPK and pH provide moderate soil fertility signal for yield and disease models. Organic matter influences water retention and microbial activity. No dynamic soil moisture data — a critical gap for irrigation models.

---

### 1.5 WeatherRecord

**Table:** `weather_records`

| Attribute | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID | No | Primary key |
| `field_id` | UUID (FK) | No | Parent field |
| `recorded_at` | Timestamp TZ | No | Observation timestamp |
| `temperature_c` | Numeric(5,2) | No | Air temperature (°C) |
| `humidity_percent` | Numeric(5,2) | No | Relative humidity (%) |
| `rainfall_mm` | Numeric(8,2) | No | Precipitation (mm) |
| `wind_speed_kmh` | Numeric(6,2) | No | Wind speed (km/h) |
| `data_source` | String(50) | No | MANUAL / sensor / API |
| `created_at` | Timestamp TZ | No | Audit timestamp |
| `updated_at` | Timestamp TZ | No | Audit timestamp |

**Current AI Utility:** Core atmospheric observations enable basic time-series analysis and anomaly detection. No solar radiation, evapotranspiration, dew point, or soil temperature — variables required by the majority of agricultural AI models.

---

## Section 2 — AI Use Case Coverage Assessment

### 2.1 Coverage Scoring

| AI Use Case | Current Coverage | Key Blockers |
|---|---|---|
| Yield Prediction | 18% | No yield history, no GDD, no ET, no seeding data |
| Disease Prediction | 15% | No disease observations, no dew point, no leaf wetness |
| Irrigation Optimization | 25% | No soil moisture, no ET, no field capacity |
| Weather Intelligence | 35% | No solar radiation, no pressure, no forecast table |

---

### 2.2 Yield Prediction

**Minimum viable model:** Supervised regression (Random Forest / XGBoost / LSTM) trained on historical yield against environmental and agronomic inputs.

**Currently available:**
- Crop type and variety (weak feature without GDD mapping)
- Planting and harvest dates (season length calculation)
- NPK, pH, organic matter (static soil inputs)
- Temperature, rainfall time-series (partial climate signal)
- Field area (required for per-hectare normalisation)

**Critical blockers:**
- No target variable (`actual_yield_tons_ha`) — supervised learning is impossible without this
- No solar radiation — primary driver of photosynthesis and biomass accumulation
- No Growing Degree Days (calculated from temperature min/max)
- No seeding rate — required to distinguish yield per plant vs per hectare
- No granular growth stage — crop coefficient (Kc) curves require BBCH-scale stages

---

### 2.3 Disease Prediction

**Minimum viable model:** Classification model (Logistic Regression / Gradient Boosting) predicting disease risk index from weather and soil conditions.

**Currently available:**
- Temperature and humidity (basic Blight/Fusarium risk proxy)
- Rainfall (promotes fungal conditions)
- Crop name and variety (disease susceptibility lookup via static reference)

**Critical blockers:**
- No disease observation log — no target variable for supervised models
- No dew point or leaf wetness hours — primary triggers for fungal disease
- No soil temperature — root disease models require this
- No granular growth stage — disease susceptibility varies dramatically by growth stage
- No pesticide application log — prevents model from learning treatment effects

---

### 2.4 Irrigation Optimization

**Minimum viable model:** Water balance model (FAO-56 methodology) + reinforcement learning or schedule optimisation.

**Currently available:**
- Rainfall (partial water input)
- Temperature and humidity (partial ET approximation)
- Soil type classification (texture class for hydraulic conductivity lookup)
- NPK and pH (indirect influence on root depth)

**Critical blockers:**
- No soil moisture (current or time-series) — the primary state variable for irrigation
- No evapotranspiration (ET₀) — the primary water demand signal
- No field capacity or permanent wilting point — required to compute available water capacity
- No irrigation type or schedule log — model cannot learn from past interventions
- No solar radiation — required by Penman-Monteith ET₀ equation

---

### 2.5 Weather Intelligence

**Minimum viable model:** Statistical anomaly detection (Z-score / Prophet) + API-based forecast integration.

**Currently available:**
- Temperature, humidity, rainfall, wind time-series
- Field-level geo-coordinates for spatial aggregation
- `data_source` flag for distinguishing sensor vs manual data

**Critical blockers:**
- No solar radiation or UV index
- No atmospheric pressure (barometric trend = storm prediction signal)
- No dew point (derived from temperature + humidity, but storage enables faster querying)
- No forecast data table (all records are historical observations)
- No extreme weather event flags
- No farm-level elevation or terrain metadata (orographic effects on local weather)

---

## Section 3 — Priority Classification

### Priority Classification Legend

| Priority | AI Capability | Release Target |
|---|---|---|
| P1 | Yield Prediction MVP | Phase 7 |
| P2 | Disease Prediction MVP | Phase 8 |
| P3 | Irrigation Optimization | Phase 9 |
| P4 | Advanced Analytics / Future | Phase 10+ |

---

### Priority 1 — Required for Yield Prediction MVP

These attributes are the minimum required to train and serve a basic yield prediction model.

#### P1.1 — Crop: `actual_yield_tons_ha`

| Field | Value |
|---|---|
| **Domain** | Crop |
| **Column Name** | `actual_yield_tons_ha` |
| **Recommended Type** | `NUMERIC(10, 4)` |
| **Nullable** | Yes (null until HARVESTED) |
| **Business Justification** | This is the target variable (label) for all supervised yield prediction models. Without historical yield data, no regression model can be trained. It is the single most important missing attribute in the entire platform. |
| **Suggested Source** | Manual entry at harvest time by field operator; optionally importable from farm management systems (FMS) or yield monitors on harvesting equipment |

---

#### P1.2 — Crop: `expected_yield_tons_ha`

| Field | Value |
|---|---|
| **Domain** | Crop |
| **Column Name** | `expected_yield_tons_ha` |
| **Recommended Type** | `NUMERIC(10, 4)` |
| **Nullable** | Yes |
| **Business Justification** | Captures agronomist or system-generated yield targets. Enables variance analysis (predicted vs actual) and serves as a benchmark metric in performance dashboards. |
| **Suggested Source** | Manual entry by agronomist; calculated field from AI prediction service once model is trained |

---

#### P1.3 — Crop: `seeding_rate_kg_ha`

| Field | Value |
|---|---|
| **Domain** | Crop |
| **Column Name** | `seeding_rate_kg_ha` |
| **Recommended Type** | `NUMERIC(8, 3)` |
| **Nullable** | Yes |
| **Business Justification** | Seeding density is a primary agronomic input variable for yield models. The same crop variety planted at different densities produces different yields. Required to separate genetics effects from management effects. |
| **Suggested Source** | Manual entry at planting time by field operator |

---

#### P1.4 — Crop: `growth_stage`

| Field | Value |
|---|---|
| **Domain** | Crop |
| **Column Name** | `growth_stage` |
| **Recommended Type** | `VARCHAR(20)` (BBCH scale code, e.g. "BBCH-59") |
| **Nullable** | Yes |
| **Business Justification** | The BBCH phenological scale provides ~100 granular growth stages. Yield potential and crop coefficient (Kc) curves — required for both yield and irrigation models — are defined per growth stage. The current 4-state status enum is insufficient. |
| **Suggested Source** | Manual entry by agronomist during field scouting; estimated via calculation from GDD accumulation once base temperature references are available |

---

#### P1.5 — WeatherRecord: `solar_radiation_wm2`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Name** | `solar_radiation_wm2` |
| **Recommended Type** | `NUMERIC(8, 3)` |
| **Nullable** | Yes |
| **Business Justification** | Solar radiation (W/m²) is the primary driver of crop photosynthesis, biomass accumulation, and ET₀ calculation. It is a required input for the Penman-Monteith evapotranspiration equation used in yield and irrigation models. Its absence blocks both P1 and P3 use cases. |
| **Suggested Source** | Weather API integration (OpenWeatherMap, AgWeatherNet, NASA POWER); IoT pyranometer sensor |

---

#### P1.6 — WeatherRecord: `temperature_min_c` and `temperature_max_c`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Names** | `temperature_min_c`, `temperature_max_c` |
| **Recommended Type** | `NUMERIC(5, 2)` each |
| **Nullable** | Yes |
| **Business Justification** | Daily minimum and maximum temperature are required to compute Growing Degree Days (GDD = ((T_max + T_min)/2) − T_base). GDD accumulation is the standard agronomic method for predicting crop development rates and harvest timing. The current single `temperature_c` field is ambiguous as to whether it represents current, mean, min, or max. |
| **Suggested Source** | Weather API (daily aggregate); IoT sensor with daily roll-up |

---

#### P1.7 — SoilProfile: `soil_depth_cm`

| Field | Value |
|---|---|
| **Domain** | SoilProfile |
| **Column Name** | `soil_depth_cm` |
| **Recommended Type** | `NUMERIC(6, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Rooting depth is constrained by soil depth. Yield models incorporate root zone volume to estimate nutrient and water uptake capacity. Shallow soils impose hard limits on yield potential regardless of other inputs. |
| **Suggested Source** | Manual entry from soil lab report or field auger survey |

---

#### P1.8 — SoilProfile: `cation_exchange_capacity`

| Field | Value |
|---|---|
| **Domain** | SoilProfile |
| **Column Name** | `cation_exchange_capacity_meq` |
| **Recommended Type** | `NUMERIC(8, 4)` |
| **Nullable** | Yes |
| **Business Justification** | CEC (meq/100g) measures the soil's ability to retain and supply cations (Ca²⁺, Mg²⁺, K⁺). It is a primary determinant of nutrient availability for yield models and explains why soils with identical NPK readings have different actual yield outcomes. |
| **Suggested Source** | Soil laboratory analysis report; manual entry |

---

#### P1.9 — Field: `elevation_m`

| Field | Value |
|---|---|
| **Domain** | Field |
| **Column Name** | `elevation_m` |
| **Recommended Type** | `NUMERIC(8, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Elevation influences temperature (lapse rate: −6.5°C per 1,000m), precipitation patterns, and solar irradiance. Yield models trained across geographically diverse farms require elevation as a confounding variable to avoid bias. |
| **Suggested Source** | Calculated field using lat/lng lookup against SRTM or Google Elevation API during field creation |

---

### Priority 2 — Required for Disease Prediction MVP

These attributes are the minimum required to build a disease risk scoring model.

#### P2.1 — Crop: `disease_risk_score`

| Field | Value |
|---|---|
| **Domain** | Crop |
| **Column Name** | `disease_risk_score` |
| **Recommended Type** | `NUMERIC(5, 4)` (0.0000 to 1.0000) |
| **Nullable** | Yes |
| **Business Justification** | AI-generated disease risk probability for the current crop. This is the primary output written back by the disease prediction inference service. Storing it on the Crop record enables threshold-based alerting, historical risk tracking, and model evaluation. |
| **Suggested Source** | Calculated field — written by the AI inference service, not by operators |

---

#### P2.2 — WeatherRecord: `dew_point_c`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Name** | `dew_point_c` |
| **Recommended Type** | `NUMERIC(5, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Dew point is the primary trigger for fungal diseases (Late Blight, Botrytis, Powdery Mildew). When leaf surface temperature falls below dew point, condensation forms and creates ideal conditions for spore germination. Humidity alone is insufficient — dew point is the correct physical variable. |
| **Suggested Source** | Weather API integration; calculated field from temperature + relative humidity using Magnus formula (can be derived but storage enables faster time-series queries) |

---

#### P2.3 — WeatherRecord: `leaf_wetness_hours`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Name** | `leaf_wetness_hours` |
| **Recommended Type** | `NUMERIC(4, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Leaf wetness duration (hours per observation window) is the single most predictive variable in epidemiological disease models (Wallin, Krause-Kyle equations). Most fungal infections require 4–12 continuous hours of leaf wetness to establish. No other existing variable approximates this. |
| **Suggested Source** | IoT leaf wetness sensor (capacitive or electrical resistance); estimated via Penman-Monteith surface energy balance model |

---

#### P2.4 — WeatherRecord: `soil_temperature_c`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Name** | `soil_temperature_c` |
| **Recommended Type** | `NUMERIC(5, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Soil temperature drives soil-borne pathogen activity (Pythium, Rhizoctonia, Fusarium). Root disease risk models require soil temperature at 10cm depth. It also affects seed germination viability and nutrient solubility, contributing to both disease and yield models. |
| **Suggested Source** | IoT soil temperature probe; Weather API (some providers include soil temperature layers) |

---

#### P2.5 — Crop: `pesticide_application_log` (reference to separate table)

| Field | Value |
|---|---|
| **Domain** | Crop |
| **Column Name** | `last_pesticide_application_date` |
| **Recommended Type** | `DATE` |
| **Nullable** | Yes |
| **Business Justification** | Disease models must account for protection windows from pesticide applications. A crop treated 3 days ago has very different risk profile than an untreated crop. A minimal implementation stores the last application date on the Crop record; a full implementation requires a separate `CropTreatment` table. |
| **Suggested Source** | Manual entry by field operator at time of application |

---

#### P2.6 — SoilProfile: `soil_moisture_percent` (current reading)

| Field | Value |
|---|---|
| **Domain** | SoilProfile |
| **Column Name** | `soil_moisture_percent` |
| **Recommended Type** | `NUMERIC(5, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Current volumetric soil moisture affects root disease pressure and influences canopy microclimate through evapotranspiration feedback. Waterlogged soils (>field capacity) create anaerobic root zone conditions that amplify Phytophthora and other oomycete diseases. |
| **Suggested Source** | IoT capacitive soil moisture sensor; satellite-derived soil moisture (Sentinel-1 SAR backscatter) |

---

### Priority 3 — Required for Irrigation Optimization

These attributes are the minimum required to implement FAO-56 water balance and schedule optimisation.

#### P3.1 — SoilProfile: `field_capacity_percent`

| Field | Value |
|---|---|
| **Domain** | SoilProfile |
| **Column Name** | `field_capacity_percent` |
| **Recommended Type** | `NUMERIC(5, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Field capacity (FC) is the soil moisture content at which drainage ceases (typically −33 kPa matric potential). It defines the upper bound of plant-available water. The irrigation trigger point is calculated as a fraction of FC, making this the foundational parameter for any irrigation scheduling model. |
| **Suggested Source** | Soil laboratory analysis; estimated from soil texture class via pedotransfer functions (Saxton & Rawls, 2006) |

---

#### P3.2 — SoilProfile: `permanent_wilting_point_percent`

| Field | Value |
|---|---|
| **Domain** | SoilProfile |
| **Column Name** | `permanent_wilting_point_percent` |
| **Recommended Type** | `NUMERIC(5, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Permanent wilting point (PWP) is the soil moisture content below which plants cannot extract water (−1500 kPa). Available Water Capacity = FC − PWP. This is the denominator of all water stress calculations. Without PWP, irrigation depletion thresholds cannot be computed. |
| **Suggested Source** | Soil laboratory analysis; estimated from texture class via pedotransfer functions |

---

#### P3.3 — WeatherRecord: `evapotranspiration_mm`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Name** | `evapotranspiration_mm` |
| **Recommended Type** | `NUMERIC(6, 3)` |
| **Nullable** | Yes |
| **Business Justification** | Reference evapotranspiration (ET₀, mm/day) is the primary water demand signal in the FAO-56 water balance model. It quantifies the atmospheric demand for water, driven by solar radiation, temperature, humidity, and wind. Multiplied by the crop coefficient (Kc), it gives crop water consumption. This single variable unlocks the entire irrigation model. |
| **Suggested Source** | Weather API (OpenET, FAO AQUASTAT); calculated field using Penman-Monteith equation once solar_radiation_wm2 is available |

---

#### P3.4 — WeatherRecord: `vapor_pressure_deficit_kpa`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Name** | `vapor_pressure_deficit_kpa` |
| **Recommended Type** | `NUMERIC(6, 4)` |
| **Nullable** | Yes |
| **Business Justification** | Vapor Pressure Deficit (VPD, kPa) is the difference between saturation and actual vapor pressure. It drives stomatal closure and transpiration rate. High VPD causes water stress even when soil moisture is adequate. VPD is required for precise ET₀ calculation and for identifying crop heat stress events. |
| **Suggested Source** | Calculated field from temperature + relative humidity; IoT sensor with psychrometer |

---

#### P3.5 — Field: `irrigation_type`

| Field | Value |
|---|---|
| **Domain** | Field |
| **Column Name** | `irrigation_type` |
| **Recommended Type** | `VARCHAR(50)` (DRIP / FLOOD / SPRINKLER / FURROW / RAINFED) |
| **Nullable** | Yes |
| **Business Justification** | Irrigation type determines application efficiency coefficients used in optimisation models. Drip irrigation (90–95% efficiency) requires vastly different scheduling than flood irrigation (50–60%). Without this attribute, the model cannot correctly back-calculate applied water volumes. |
| **Suggested Source** | Manual entry by farm manager during field setup |

---

#### P3.6 — Field: `irrigation_system_capacity_mm_hr`

| Field | Value |
|---|---|
| **Domain** | Field |
| **Column Name** | `irrigation_capacity_mm_hr` |
| **Recommended Type** | `NUMERIC(6, 3)` |
| **Nullable** | Yes |
| **Business Justification** | Maximum irrigation application rate (mm/hour) is a hard physical constraint for schedule optimisation. The model cannot recommend applying 20mm in 1 hour if the system maximum is 5mm/hour. This parameter bounds the solution space for schedule generation. |
| **Suggested Source** | Manual entry by farm manager or irrigation engineer |

---

#### P3.7 — SoilProfile: `bulk_density_g_cm3`

| Field | Value |
|---|---|
| **Domain** | SoilProfile |
| **Column Name** | `bulk_density_g_cm3` |
| **Recommended Type** | `NUMERIC(5, 3)` |
| **Nullable** | Yes |
| **Business Justification** | Bulk density (g/cm³) converts volumetric water content (%) to mass-based measurements required for water balance calculations. It also indicates soil compaction, which reduces hydraulic conductivity and root penetration — both critical factors in irrigation efficiency models. |
| **Suggested Source** | Soil laboratory analysis; estimated from texture class via pedotransfer functions |

---

### Priority 4 — Future Advanced Analytics

These attributes are not required for MVP AI features but enable higher-fidelity models, satellite integration, and operational intelligence in later phases.

#### P4.1 — WeatherRecord: `atmospheric_pressure_hpa`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Name** | `atmospheric_pressure_hpa` |
| **Recommended Type** | `NUMERIC(7, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Barometric pressure trends (falling = storm incoming) provide 12–24 hour advance warning for extreme weather events. Required for a storm-risk alert model and used in precision Penman-Monteith ET₀ calculations at high elevations. |
| **Suggested Source** | Weather API; IoT barometer sensor |

---

#### P4.2 — WeatherRecord: `cloud_cover_percent`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Name** | `cloud_cover_percent` |
| **Recommended Type** | `NUMERIC(5, 2)` |
| **Nullable** | Yes |
| **Business Justification** | Cloud cover (0–100%) attenuates solar radiation reaching the crop canopy. Required for accurate solar radiation estimation when pyranometers are not available, and for satellite imagery quality flagging (cloud masks). |
| **Suggested Source** | Weather API; satellite cloud mask layer (Sentinel-2 SCL band) |

---

#### P4.3 — WeatherRecord: `uv_index`

| Field | Value |
|---|---|
| **Domain** | WeatherRecord |
| **Column Name** | `uv_index` |
| **Recommended Type** | `NUMERIC(4, 2)` |
| **Nullable** | Yes |
| **Business Justification** | UV index correlates with solar radiation available for photosynthesis (PAR). High UV also degrades certain pesticide residues more rapidly, affecting the protection window modelled in disease prediction. |
| **Suggested Source** | Weather API (OpenUV, OpenWeatherMap UV index endpoint) |

---

#### P4.4 — Field: `slope_percent` and `aspect_degrees`

| Field | Value |
|---|---|
| **Domain** | Field |
| **Column Names** | `slope_percent`, `aspect_degrees` |
| **Recommended Types** | `NUMERIC(5, 2)` each |
| **Nullable** | Yes |
| **Business Justification** | Slope affects surface runoff, erosion risk, and cold air drainage. Aspect (compass bearing of slope face) determines how much solar radiation the field receives, driving significant within-farm yield variation. Both are required for precision spatial yield models covering hilly or mountainous terrain. |
| **Suggested Source** | Calculated field using DEM (Digital Elevation Model) analysis from SRTM or LiDAR; GIS processing pipeline |

---

#### P4.5 — Farm: `climate_zone`

| Field | Value |
|---|---|
| **Domain** | Farm |
| **Column Name** | `climate_zone` |
| **Recommended Type** | `VARCHAR(20)` (Köppen-Geiger codes: Af, Am, BSh, Cfa, Dfb, etc.) |
| **Nullable** | Yes |
| **Business Justification** | Climate zone classification enables cross-farm model transfer learning. A yield model trained on Cfa (humid subtropical) farms transfers well to other Cfa farms but poorly to BSh (semi-arid) farms. Encoding this enables climate-stratified model ensembles. |
| **Suggested Source** | Calculated field using lat/lng lookup against Beck et al. (2018) Köppen-Geiger raster dataset |

---

#### P4.6 — Crop: `ndvi_latest` (Normalized Difference Vegetation Index)

| Field | Value |
|---|---|
| **Domain** | Crop |
| **Column Name** | `ndvi_latest` |
| **Recommended Type** | `NUMERIC(5, 4)` (range −1.0 to 1.0) |
| **Nullable** | Yes |
| **Business Justification** | NDVI is a satellite-derived measure of crop biomass and health ((NIR − Red) / (NIR + Red)). It is the most widely used remote sensing feature in yield prediction models and provides a field-level observation that cannot be replicated by ground sensors. Enables yield maps and within-field variability analysis. |
| **Suggested Source** | Sentinel-2 satellite imagery pipeline (10m resolution, 5-day revisit); Planet Labs API |

---

#### P4.7 — Crop: `fertilizer_total_nitrogen_kg_ha`

| Field | Value |
|---|---|
| **Domain** | Crop |
| **Column Name** | `fertilizer_total_nitrogen_kg_ha` |
| **Recommended Type** | `NUMERIC(8, 3)` |
| **Nullable** | Yes |
| **Business Justification** | Total applied nitrogen (kg/ha over the crop cycle) is one of the strongest yield predictors in cereal and vegetable crops. Without this, the model conflates soil N availability with applied N, creating a confounded soil health signal. Required for nutrient response curve modelling. |
| **Suggested Source** | Manual entry by field operator (aggregated from application events); integration with variable-rate application (VRA) systems |

---

#### P4.8 — SoilProfile: `micronutrients` (Zinc, Manganese, Boron, Iron)

| Field | Value |
|---|---|
| **Domain** | SoilProfile |
| **Column Names** | `zinc_mg_kg`, `manganese_mg_kg`, `boron_mg_kg`, `iron_mg_kg` |
| **Recommended Types** | `NUMERIC(8, 4)` each |
| **Nullable** | Yes |
| **Business Justification** | Micronutrient deficiencies cause yield losses of 10–40% even when macronutrients (NPK) are adequate. Zinc deficiency is the most widespread micronutrient problem globally. Required for high-fidelity yield models and for fertiliser recommendation AI features. |
| **Suggested Source** | Soil laboratory micronutrient panel; manual entry from lab report |

---

## Section 4 — Summary Gap Table

### All Missing Attributes by Domain

| Priority | Domain | Column | Type | Source |
|---|---|---|---|---|
| P1 | Crop | `actual_yield_tons_ha` | NUMERIC(10,4) | Manual / Yield monitor |
| P1 | Crop | `expected_yield_tons_ha` | NUMERIC(10,4) | Manual / AI calculated |
| P1 | Crop | `seeding_rate_kg_ha` | NUMERIC(8,3) | Manual |
| P1 | Crop | `growth_stage` | VARCHAR(20) | Manual / GDD calculated |
| P1 | WeatherRecord | `solar_radiation_wm2` | NUMERIC(8,3) | Weather API / IoT sensor |
| P1 | WeatherRecord | `temperature_min_c` | NUMERIC(5,2) | Weather API / IoT sensor |
| P1 | WeatherRecord | `temperature_max_c` | NUMERIC(5,2) | Weather API / IoT sensor |
| P1 | SoilProfile | `soil_depth_cm` | NUMERIC(6,2) | Manual / Lab report |
| P1 | SoilProfile | `cation_exchange_capacity_meq` | NUMERIC(8,4) | Lab analysis |
| P1 | Field | `elevation_m` | NUMERIC(8,2) | Calculated / Elevation API |
| P2 | Crop | `disease_risk_score` | NUMERIC(5,4) | AI inference service |
| P2 | Crop | `last_pesticide_application_date` | DATE | Manual |
| P2 | WeatherRecord | `dew_point_c` | NUMERIC(5,2) | Weather API / Calculated |
| P2 | WeatherRecord | `leaf_wetness_hours` | NUMERIC(4,2) | IoT sensor / Calculated |
| P2 | WeatherRecord | `soil_temperature_c` | NUMERIC(5,2) | Weather API / IoT probe |
| P2 | SoilProfile | `soil_moisture_percent` | NUMERIC(5,2) | IoT sensor / Satellite |
| P3 | SoilProfile | `field_capacity_percent` | NUMERIC(5,2) | Lab / Pedotransfer fn |
| P3 | SoilProfile | `permanent_wilting_point_percent` | NUMERIC(5,2) | Lab / Pedotransfer fn |
| P3 | SoilProfile | `bulk_density_g_cm3` | NUMERIC(5,3) | Lab / Pedotransfer fn |
| P3 | WeatherRecord | `evapotranspiration_mm` | NUMERIC(6,3) | Weather API / Calculated |
| P3 | WeatherRecord | `vapor_pressure_deficit_kpa` | NUMERIC(6,4) | Calculated / IoT |
| P3 | Field | `irrigation_type` | VARCHAR(50) | Manual |
| P3 | Field | `irrigation_capacity_mm_hr` | NUMERIC(6,3) | Manual |
| P4 | WeatherRecord | `atmospheric_pressure_hpa` | NUMERIC(7,2) | Weather API / IoT |
| P4 | WeatherRecord | `cloud_cover_percent` | NUMERIC(5,2) | Weather API / Satellite |
| P4 | WeatherRecord | `uv_index` | NUMERIC(4,2) | Weather API |
| P4 | Field | `slope_percent` | NUMERIC(5,2) | DEM / GIS pipeline |
| P4 | Field | `aspect_degrees` | NUMERIC(5,2) | DEM / GIS pipeline |
| P4 | Farm | `climate_zone` | VARCHAR(20) | Calculated / Köppen API |
| P4 | Crop | `ndvi_latest` | NUMERIC(5,4) | Sentinel-2 / Planet API |
| P4 | Crop | `fertilizer_total_nitrogen_kg_ha` | NUMERIC(8,3) | Manual / VRA system |
| P4 | SoilProfile | `zinc_mg_kg` | NUMERIC(8,4) | Soil lab panel |
| P4 | SoilProfile | `manganese_mg_kg` | NUMERIC(8,4) | Soil lab panel |
| P4 | SoilProfile | `boron_mg_kg` | NUMERIC(8,4) | Soil lab panel |
| P4 | SoilProfile | `iron_mg_kg` | NUMERIC(8,4) | Soil lab panel |

**Total missing attributes:** 35  
**P1 (Yield MVP):** 10 attributes  
**P2 (Disease MVP):** 6 attributes  
**P3 (Irrigation):** 7 attributes  
**P4 (Advanced):** 12 attributes  

---

## Section 5 — Data Source Strategy

### Recommended Integration Roadmap

| Source Type | Attributes Served | Integration Method |
|---|---|---|
| **Manual Entry (Operator)** | yield, seeding_rate, growth_stage, irrigation_type, pesticide_date, fertilizer | Extended Pydantic schemas + API endpoints |
| **Weather API** (OpenWeatherMap / NASA POWER / AgWeatherNet) | solar_radiation, temp_min/max, dew_point, pressure, cloud_cover, ET₀, VPD | Background ingestion service + WeatherRecord writer |
| **IoT Sensor Network** | soil_moisture, soil_temperature, leaf_wetness, actual weather readings | MQTT broker → ingestion service → WeatherRecord / SoilProfile |
| **Satellite Imagery** (Sentinel-2 / Planet) | NDVI, cloud_cover, soil_moisture (SAR) | Scheduled pipeline → Crop and SoilProfile update service |
| **Calculated Fields** (App Layer) | GDD, ET₀, VPD, dew_point, elevation, climate_zone | Python utility functions → stored on model at write time |
| **Soil Laboratory** | CEC, bulk_density, FC, PWP, micronutrients, soil_depth | Manual entry workflow via extended SoilProfile API |

---

## Section 6 — AI Readiness Radar

### Per Use-Case Readiness After P1–P3 Implementation

| AI Use Case | Current | After P1 | After P2 | After P3 |
|---|---|---|---|---|
| Yield Prediction | 18% | 82% | 88% | 93% |
| Disease Prediction | 15% | 40% | 85% | 90% |
| Irrigation Optimization | 25% | 55% | 60% | 92% |
| Weather Intelligence | 35% | 65% | 75% | 85% |

> Note: 100% readiness is intentionally not declared. Production AI systems continuously improve as new data streams are added. The above percentages represent feature completeness relative to MVP model specifications, not perfect model accuracy.

---

## Section 7 — Architectural Recommendations

### 7.1 New Table Candidates

The following net-new tables (not columns on existing models) are recommended for later phases:

| Proposed Table | Purpose | Priority |
|---|---|---|
| `weather_forecasts` | Store API-fetched 7-day forecast data separate from historical observations | P3 |
| `crop_treatments` | Full treatment event log (pesticide, fungicide, fertiliser, irrigation events) | P2–P3 |
| `field_sensor_devices` | Registry of IoT devices attached to fields with calibration metadata | P3 |
| `yield_benchmarks` | Regional and crop-type yield benchmarks for comparative analytics | P4 |
| `satellite_observations` | NDVI, EVI, LAI time-series from satellite passes per field | P4 |

### 7.2 Existing Schema Notes

- `Field.soil_type` is currently a free-text `VARCHAR(50)`. The `SoilProfile.soil_type` uses a typed enum (`SoilType`). These two should be reconciled in Phase 7 — the Field-level free-text should either be deprecated in favour of the SoilProfile enum or constrained to the same enum values.
- `Farm` has no Pydantic schemas or service layer. This gap should be resolved before AI features that aggregate at the farm level (e.g. farm-wide yield dashboards) are implemented.
- `WeatherRecord.temperature_c` is ambiguous (point-in-time vs mean vs max). Clarification and potentially renaming to `temperature_current_c` is recommended alongside adding `temperature_min_c` / `temperature_max_c`.

### 7.3 Data Quality Requirements

Before AI model training begins, the following data quality thresholds should be met:

| Metric | Minimum Requirement |
|---|---|
| Historical yield records per crop type | ≥ 3 years / ≥ 30 field-seasons |
| Weather record completeness | ≥ 95% non-null for temperature, humidity, rainfall |
| Soil profile coverage | ≥ 80% of active fields must have a SoilProfile |
| Temporal resolution of weather records | ≤ 1 hour (hourly or sub-hourly observations) |
| Duplicate / outlier records | ≤ 2% after data quality pipeline |

---

## Document History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | June 2026 | Architecture Team | Initial assessment — Phase 6 Step 1 |

---

*This document is a planning artifact. No code changes are made by this document. All model extensions described herein require separate design review, schema migration, service layer updates, and API versioning as part of Phase 7 planning.*
