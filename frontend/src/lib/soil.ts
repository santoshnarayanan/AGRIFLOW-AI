/**
 * Soil texture helpers.
 *
 * Field.soil_type is stored as a free-text label. We standardise on the 12
 * USDA soil texture classes (the same labels the demo dataset uses, e.g.
 * "Loam", "Clay Loam"), plus Peat and Chalk which the soil-profile domain
 * also recognises.
 */

export const USDA_TEXTURE_CLASSES = [
  'Sand',
  'Loamy Sand',
  'Sandy Loam',
  'Loam',
  'Silt Loam',
  'Silt',
  'Sandy Clay Loam',
  'Clay Loam',
  'Silty Clay Loam',
  'Sandy Clay',
  'Silty Clay',
  'Clay',
] as const

/** Every soil type offered in the Field form dropdown. */
export const ALL_SOIL_TYPES: readonly string[] = [...USDA_TEXTURE_CLASSES, 'Peat', 'Chalk']

/**
 * Classify a sand/silt/clay mix into a USDA texture class using the
 * standard USDA soil texture triangle boundaries. Inputs are percentages
 * and are normalised to sum to 100.
 */
export function usdaTextureClass(sandPct: number, siltPct: number, clayPct: number): string {
  const total = sandPct + siltPct + clayPct
  if (total <= 0) return 'Loam'
  const sand = (sandPct / total) * 100
  const silt = (siltPct / total) * 100
  const clay = (clayPct / total) * 100

  if (silt + 1.5 * clay < 15) return 'Sand'
  if (silt + 2 * clay < 30) return 'Loamy Sand'
  if ((clay >= 7 && clay < 20 && sand > 52) || (clay < 7 && silt < 50)) return 'Sandy Loam'
  if (clay >= 7 && clay < 27 && silt >= 28 && silt < 50 && sand <= 52) return 'Loam'
  if ((silt >= 50 && clay >= 12 && clay < 27) || (silt >= 50 && silt < 80 && clay < 12)) return 'Silt Loam'
  if (silt >= 80 && clay < 12) return 'Silt'
  if (clay >= 20 && clay < 35 && silt < 28 && sand > 45) return 'Sandy Clay Loam'
  if (clay >= 27 && clay < 40 && sand > 20 && sand <= 45) return 'Clay Loam'
  if (clay >= 27 && clay < 40 && sand <= 20) return 'Silty Clay Loam'
  if (clay >= 35 && sand > 45) return 'Sandy Clay'
  if (clay >= 40 && silt >= 40) return 'Silty Clay'
  return 'Clay'
}
