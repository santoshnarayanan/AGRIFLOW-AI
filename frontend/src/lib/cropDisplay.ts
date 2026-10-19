import type { Crop } from '@/types'

/** API wire shape when React Query cache predates ``mapCropFromApi``. */
export type CropLike = Crop & {
  crop_name?: string
  crop_variety?: string | null
}

export function cropDisplayName(crop: CropLike): string {
  const name = crop.name?.trim() || crop.crop_name?.trim()
  return name || 'Unknown crop'
}

export function cropDisplayVariety(crop: CropLike): string | null {
  const variety = crop.variety?.trim() || crop.crop_variety?.trim()
  return variety || null
}
