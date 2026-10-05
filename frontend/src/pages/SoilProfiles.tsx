import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2, FlaskConical, Filter, Droplets } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter, DialogDescription,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useFarms } from '@/api/farms'
import { useFields } from '@/api/fields'
import {
  useSoilProfiles, useCreateSoilProfile,
  useUpdateSoilProfile, useDeleteSoilProfile,
} from '@/api/soil-profiles'
import { formatDate, cn } from '@/lib/utils'
import type { SoilProfile, SoilTexture, SoilProfileCreate, SoilProfileUpdate } from '@/types'

// ─── Constants ────────────────────────────────────────────────────────────────

const SOIL_TEXTURES: { value: SoilTexture; label: string }[] = [
  { value: 'sandy', label: 'Sandy' },
  { value: 'sandy_loam', label: 'Sandy Loam' },
  { value: 'loam', label: 'Loam' },
  { value: 'silt_loam', label: 'Silt Loam' },
  { value: 'silt', label: 'Silt' },
  { value: 'clay_loam', label: 'Clay Loam' },
  { value: 'clay', label: 'Clay' },
  { value: 'peat', label: 'Peat' },
]

// ─── pH helpers ───────────────────────────────────────────────────────────────

function phClass(ph: number | null): string {
  if (ph === null) return 'bg-muted text-muted-foreground'
  if (ph < 5.5) return 'bg-red-100 text-red-800'
  if (ph < 6.0) return 'bg-orange-100 text-orange-800'
  if (ph <= 7.0) return 'bg-green-100 text-green-800'
  if (ph <= 7.5) return 'bg-teal-100 text-teal-800'
  if (ph <= 8.5) return 'bg-blue-100 text-blue-800'
  return 'bg-indigo-100 text-indigo-800'
}

function phLabel(ph: number | null): string {
  if (ph === null) return '—'
  if (ph < 5.5) return 'Very Acidic'
  if (ph < 6.0) return 'Acidic'
  if (ph <= 7.0) return 'Optimal'
  if (ph <= 7.5) return 'Neutral'
  if (ph <= 8.5) return 'Alkaline'
  return 'Very Alkaline'
}

// pH gradient bar: maps 0–14 to a left% position on a colour strip
function PhBar({ ph }: { ph: number | null }) {
  if (ph === null) return <span className="text-muted-foreground text-sm">—</span>
  const pct = Math.min(100, Math.max(0, (ph / 14) * 100))
  return (
    <div className="flex items-center gap-2">
      <div className="relative h-3 w-24 overflow-hidden rounded-full"
        style={{ background: 'linear-gradient(to right, #ef4444, #f97316, #eab308, #22c55e, #22c55e, #14b8a6, #3b82f6, #6366f1)' }}
      >
        <div
          className="absolute top-0 h-full w-1 rounded-full bg-white shadow ring-1 ring-black/20"
          style={{ left: `calc(${pct}% - 2px)` }}
        />
      </div>
      <span className={cn('rounded-full px-2 py-0.5 text-xs font-semibold', phClass(ph))}>
        {ph.toFixed(1)}
      </span>
    </div>
  )
}

// NPK mini bar — percentage of an assumed max (500 mg/kg)
function NpkBar({ value, color }: { value: number | null; color: string }) {
  if (value === null) return <span className="text-muted-foreground text-sm">—</span>
  const pct = Math.min(100, (value / 500) * 100)
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-2 w-16 rounded-full bg-muted">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-muted-foreground">{value}</span>
    </div>
  )
}

// ─── Form schema ─────────────────────────────────────────────────────────────

const optNum = z
  .string()
  .refine((v) => v === '' || (!isNaN(Number(v)) && Number(v) >= 0), {
    message: 'Must be a non-negative number',
  })

const soilSchema = z.object({
  field_id: z.string().min(1, 'Please select a field'),
  ph_level: z.string().refine((v) => v === '' || (Number(v) >= 0 && Number(v) <= 14), {
    message: 'pH must be between 0 and 14',
  }),
  nitrogen_content: optNum,
  phosphorus_content: optNum,
  potassium_content: optNum,
  organic_matter: z.string().refine((v) => v === '' || (Number(v) >= 0 && Number(v) <= 100), {
    message: 'Organic matter must be 0–100%',
  }),
  moisture_content: z.string().refine((v) => v === '' || (Number(v) >= 0 && Number(v) <= 100), {
    message: 'Moisture must be 0–100%',
  }),
  texture: z.string(),
  notes: z.string().max(1000),
  recorded_at: z.string(),
})

interface SoilFormValues {
  field_id: string
  ph_level: string
  nitrogen_content: string
  phosphorus_content: string
  potassium_content: string
  organic_matter: string
  moisture_content: string
  texture: string
  notes: string
  recorded_at: string
}

const EMPTY_FORM: SoilFormValues = {
  field_id: '', ph_level: '', nitrogen_content: '', phosphorus_content: '',
  potassium_content: '', organic_matter: '', moisture_content: '',
  texture: '', notes: '', recorded_at: '',
}

function numOrUndef(s: string): number | undefined {
  return s === '' ? undefined : Number(s)
}

// ─── Soil Form ────────────────────────────────────────────────────────────────

interface SoilFormProps {
  defaultValues?: Partial<SoilFormValues>
  onSubmit: (values: SoilFormValues) => void
  isPending: boolean
  onCancel: () => void
  mode: 'create' | 'edit'
  lockedFieldId?: number
  preselectedFarmId?: number
}

function SoilForm({
  defaultValues, onSubmit, isPending, onCancel, mode, lockedFieldId, preselectedFarmId,
}: SoilFormProps) {
  const { data: farms } = useFarms()
  const [formFarmId, setFormFarmId] = useState<number | undefined>(preselectedFarmId)
  const { data: fields } = useFields(formFarmId)

  const { register, handleSubmit, control, formState: { errors } } = useForm<SoilFormValues>({
    resolver: zodResolver(soilSchema),
    defaultValues: { ...EMPTY_FORM, ...defaultValues },
  })

  const lockedField = fields?.find((f) => f.id === lockedFieldId)

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Field selector */}
      {lockedFieldId ? (
        <div className="space-y-2">
          <Label>Field</Label>
          <div className="flex h-10 items-center rounded-md border bg-muted px-3 text-sm text-muted-foreground">
            {lockedField?.name ?? `Field #${lockedFieldId}`}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label>Farm</Label>
            <Select value={formFarmId ? String(formFarmId) : ''} onValueChange={(v) => setFormFarmId(Number(v))}>
              <SelectTrigger><SelectValue placeholder="Select farm…" /></SelectTrigger>
              <SelectContent>
                {farms?.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Field *</Label>
            <Controller name="field_id" control={control} render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange} disabled={!formFarmId}>
                <SelectTrigger>
                  <SelectValue placeholder={formFarmId ? 'Select field…' : 'Pick farm first'} />
                </SelectTrigger>
                <SelectContent>
                  {fields?.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
                </SelectContent>
              </Select>
            )} />
            {errors.field_id && <p className="text-xs text-destructive">{errors.field_id.message}</p>}
          </div>
        </div>
      )}

      {/* Recorded date + Texture */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="recorded_at">Sample Date</Label>
          <Input id="recorded_at" type="date" {...register('recorded_at')} />
        </div>
        <div className="space-y-2">
          <Label>Soil Texture</Label>
          <Controller name="texture" control={control} render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger><SelectValue placeholder="Select texture…" /></SelectTrigger>
              <SelectContent>
                {SOIL_TEXTURES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )} />
        </div>
      </div>

      {/* pH + Organic matter + Moisture */}
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-2">
          <Label htmlFor="ph_level">pH Level (0–14)</Label>
          <Input id="ph_level" type="number" step="0.1" min="0" max="14" placeholder="e.g. 6.5" {...register('ph_level')} />
          {errors.ph_level && <p className="text-xs text-destructive">{errors.ph_level.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="organic_matter">Organic Matter (%)</Label>
          <Input id="organic_matter" type="number" step="0.1" min="0" max="100" placeholder="e.g. 3.2" {...register('organic_matter')} />
          {errors.organic_matter && <p className="text-xs text-destructive">{errors.organic_matter.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="moisture_content">Moisture (%)</Label>
          <Input id="moisture_content" type="number" step="0.1" min="0" max="100" placeholder="e.g. 22.0" {...register('moisture_content')} />
          {errors.moisture_content && <p className="text-xs text-destructive">{errors.moisture_content.message}</p>}
        </div>
      </div>

      {/* NPK */}
      <div>
        <p className="mb-2 text-sm font-medium text-muted-foreground">NPK Content (mg/kg)</p>
        <div className="grid grid-cols-3 gap-3">
          <div className="space-y-2">
            <Label htmlFor="nitrogen_content">Nitrogen (N)</Label>
            <Input id="nitrogen_content" type="number" step="0.1" min="0" placeholder="e.g. 120" {...register('nitrogen_content')} />
            {errors.nitrogen_content && <p className="text-xs text-destructive">{errors.nitrogen_content.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="phosphorus_content">Phosphorus (P)</Label>
            <Input id="phosphorus_content" type="number" step="0.1" min="0" placeholder="e.g. 45" {...register('phosphorus_content')} />
            {errors.phosphorus_content && <p className="text-xs text-destructive">{errors.phosphorus_content.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="potassium_content">Potassium (K)</Label>
            <Input id="potassium_content" type="number" step="0.1" min="0" placeholder="e.g. 200" {...register('potassium_content')} />
            {errors.potassium_content && <p className="text-xs text-destructive">{errors.potassium_content.message}</p>}
          </div>
        </div>
      </div>

      {/* Notes */}
      <div className="space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Textarea id="notes" placeholder="Observations, lab report reference, field conditions…" rows={3} {...register('notes')} />
      </div>

      <DialogFooter className="pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>Cancel</Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Saving…' : mode === 'create' ? 'Add Soil Profile' : 'Save Changes'}
        </Button>
      </DialogFooter>
    </form>
  )
}

// ─── Delete confirm ───────────────────────────────────────────────────────────

function DeleteSoilDialog({ profile, open, onClose }: {
  profile: SoilProfile | null; open: boolean; onClose: () => void
}) {
  const { mutate: del, isPending } = useDeleteSoilProfile()
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Soil Profile</DialogTitle>
          <DialogDescription>
            Delete this soil profile record
            {profile?.recorded_at ? ` (sampled ${formatDate(profile.recorded_at)})` : ''}?
            This permanently removes the nutrient and pH data. This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>Cancel</Button>
          <Button variant="destructive" disabled={isPending}
            onClick={() => profile && del(profile.id, { onSuccess: onClose })}>
            {isPending ? 'Deleting…' : 'Delete Profile'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function SoilProfiles() {
  const { data: farms, isLoading: farmsLoading } = useFarms()
  const [selectedFarmId, setSelectedFarmId] = useState<number | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<number | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [editProfile, setEditProfile] = useState<SoilProfile | null>(null)
  const [deleteProfile, setDeleteProfile] = useState<SoilProfile | null>(null)

  const { data: fields } = useFields(selectedFarmId)
  const { data: profiles, isLoading, isError } = useSoilProfiles(selectedFieldId)
  const { mutate: createProfile, isPending: creating } = useCreateSoilProfile()
  const { mutate: updateProfile, isPending: updating } = useUpdateSoilProfile()

  function handleFarmChange(v: string) {
    setSelectedFarmId(v === 'all' ? undefined : Number(v))
    setSelectedFieldId(undefined)
  }

  function handleCreate(values: SoilFormValues) {
    const payload: SoilProfileCreate = {
      field_id: Number(values.field_id),
      ph_level: numOrUndef(values.ph_level),
      nitrogen_content: numOrUndef(values.nitrogen_content),
      phosphorus_content: numOrUndef(values.phosphorus_content),
      potassium_content: numOrUndef(values.potassium_content),
      organic_matter: numOrUndef(values.organic_matter),
      moisture_content: numOrUndef(values.moisture_content),
      texture: values.texture ? (values.texture as SoilTexture) : undefined,
      notes: values.notes || undefined,
      recorded_at: values.recorded_at || undefined,
    }
    createProfile(payload, { onSuccess: () => setCreateOpen(false) })
  }

  function handleEdit(values: SoilFormValues) {
    if (!editProfile) return
    const payload: SoilProfileUpdate = {
      ph_level: numOrUndef(values.ph_level),
      nitrogen_content: numOrUndef(values.nitrogen_content),
      phosphorus_content: numOrUndef(values.phosphorus_content),
      potassium_content: numOrUndef(values.potassium_content),
      organic_matter: numOrUndef(values.organic_matter),
      moisture_content: numOrUndef(values.moisture_content),
      texture: values.texture ? (values.texture as SoilTexture) : undefined,
      notes: values.notes || undefined,
      recorded_at: values.recorded_at || undefined,
    }
    updateProfile({ id: editProfile.id, payload }, { onSuccess: () => setEditProfile(null) })
  }

  // Aggregate stats from visible profiles
  const validPh = profiles?.filter((p) => p.ph_level !== null) ?? []
  const avgPh = validPh.length
    ? validPh.reduce((s, p) => s + p.ph_level!, 0) / validPh.length
    : null
  const latestSample = profiles
    ?.filter((p) => p.recorded_at)
    .sort((a, b) => b.recorded_at!.localeCompare(a.recorded_at!))[0]

  const selectedFarm = farms?.find((f) => f.id === selectedFarmId)
  const selectedField = fields?.find((f) => f.id === selectedFieldId)

  function profileToFormValues(p: SoilProfile): Partial<SoilFormValues> {
    return {
      field_id: String(p.field_id),
      ph_level: p.ph_level != null ? String(p.ph_level) : '',
      nitrogen_content: p.nitrogen_content != null ? String(p.nitrogen_content) : '',
      phosphorus_content: p.phosphorus_content != null ? String(p.phosphorus_content) : '',
      potassium_content: p.potassium_content != null ? String(p.potassium_content) : '',
      organic_matter: p.organic_matter != null ? String(p.organic_matter) : '',
      moisture_content: p.moisture_content != null ? String(p.moisture_content) : '',
      texture: p.texture ?? '',
      notes: p.notes ?? '',
      recorded_at: p.recorded_at ? p.recorded_at.split('T')[0] : '',
    }
  }

  return (
    <div className="space-y-6">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-muted-foreground">Farm:</span>
        </div>
        {farmsLoading ? <Skeleton className="h-10 w-44" /> : (
          <Select value={selectedFarmId ? String(selectedFarmId) : 'all'} onValueChange={handleFarmChange}>
            <SelectTrigger className="w-44"><SelectValue placeholder="All farms" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All farms</SelectItem>
              {farms?.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
            </SelectContent>
          </Select>
        )}
        {selectedFarmId && (
          <>
            <span className="text-muted-foreground">›</span>
            <span className="text-sm font-medium text-muted-foreground">Field:</span>
            <Select value={selectedFieldId ? String(selectedFieldId) : 'all'}
              onValueChange={(v) => setSelectedFieldId(v === 'all' ? undefined : Number(v))}>
              <SelectTrigger className="w-44"><SelectValue placeholder="All fields" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All fields</SelectItem>
                {fields?.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </>
        )}
        <div className="flex-1" />
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Soil Profile
        </Button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold">{profiles?.length ?? '—'}</p>
            <p className="text-xs text-muted-foreground mt-0.5">Soil Samples</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-muted-foreground">Avg pH</p>
              {avgPh !== null && (
                <span className={cn('rounded-full px-2 py-0.5 text-[10px] font-semibold', phClass(avgPh))}>
                  {phLabel(avgPh)}
                </span>
              )}
            </div>
            <p className="text-2xl font-bold">{avgPh !== null ? avgPh.toFixed(1) : '—'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold">
              {profiles
                ? profiles.filter((p) => p.organic_matter !== null).length > 0
                  ? (profiles.reduce((s, p) => s + (p.organic_matter ?? 0), 0) /
                    profiles.filter((p) => p.organic_matter !== null).length).toFixed(1) + '%'
                  : '—'
                : '—'}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">Avg Organic Matter</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-lg font-bold">
              {latestSample?.recorded_at ? formatDate(latestSample.recorded_at) : '—'}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">Latest Sample</p>
          </CardContent>
        </Card>
      </div>

      {/* Profiles table */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            {selectedField
              ? `Soil Profiles — ${selectedField.name}`
              : selectedFarm
              ? `Soil Profiles — ${selectedFarm.name}`
              : 'All Soil Profiles'}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : isError ? (
            <div className="py-12 text-center text-sm text-destructive">
              Failed to load profiles. Is the backend running?
            </div>
          ) : profiles?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <FlaskConical className="mb-3 h-10 w-10 opacity-20" />
              <p className="font-medium">No soil samples yet</p>
              <p className="text-sm">
                {selectedField
                  ? `Record the first soil sample for ${selectedField.name}.`
                  : 'Select a field or click "Add Soil Profile" to record a sample.'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>pH Level</TableHead>
                  <TableHead>N (mg/kg)</TableHead>
                  <TableHead>P (mg/kg)</TableHead>
                  <TableHead>K (mg/kg)</TableHead>
                  <TableHead>Organic Matter</TableHead>
                  <TableHead>Moisture</TableHead>
                  <TableHead>Texture</TableHead>
                  <TableHead>Sampled</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {profiles?.map((p) => {
                  const field = fields?.find((f) => f.id === p.field_id)
                  const farm = farms?.find((f) => f.id === field?.farm_id)
                  return (
                    <TableRow key={p.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium text-sm">
                            {field?.name ?? `Field #${p.field_id}`}
                          </p>
                          <p className="text-xs text-muted-foreground">{farm?.name ?? ''}</p>
                        </div>
                      </TableCell>
                      <TableCell><PhBar ph={p.ph_level} /></TableCell>
                      <TableCell><NpkBar value={p.nitrogen_content} color="bg-green-500" /></TableCell>
                      <TableCell><NpkBar value={p.phosphorus_content} color="bg-amber-500" /></TableCell>
                      <TableCell><NpkBar value={p.potassium_content} color="bg-blue-500" /></TableCell>
                      <TableCell>
                        {p.organic_matter != null ? (
                          <div className="flex items-center gap-1.5">
                            <div className="h-2 w-14 rounded-full bg-muted">
                              <div className="h-2 rounded-full bg-emerald-500"
                                style={{ width: `${Math.min(100, p.organic_matter)}%` }} />
                            </div>
                            <span className="text-xs text-muted-foreground">{p.organic_matter}%</span>
                          </div>
                        ) : <span className="text-muted-foreground text-sm">—</span>}
                      </TableCell>
                      <TableCell>
                        {p.moisture_content != null ? (
                          <div className="flex items-center gap-1.5">
                            <Droplets className="h-3.5 w-3.5 text-blue-400" />
                            <span className="text-sm">{p.moisture_content}%</span>
                          </div>
                        ) : <span className="text-muted-foreground text-sm">—</span>}
                      </TableCell>
                      <TableCell>
                        {p.texture ? (
                          <Badge variant="outline" className="capitalize text-xs">
                            {p.texture.replace(/_/g, ' ')}
                          </Badge>
                        ) : <span className="text-muted-foreground text-sm">—</span>}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {p.recorded_at ? formatDate(p.recorded_at) : '—'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="ghost" size="icon" className="h-8 w-8"
                            onClick={() => setEditProfile(p)}>
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button variant="ghost" size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => setDeleteProfile(p)}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Record Soil Profile</DialogTitle>
            <DialogDescription>
              Enter soil analysis data from a lab report or field measurement.
            </DialogDescription>
          </DialogHeader>
          <SoilForm mode="create" lockedFieldId={selectedFieldId} preselectedFarmId={selectedFarmId}
            defaultValues={selectedFieldId ? { field_id: String(selectedFieldId) } : undefined}
            onSubmit={handleCreate} isPending={creating} onCancel={() => setCreateOpen(false)} />
        </DialogContent>
      </Dialog>

      {/* Edit */}
      <Dialog open={!!editProfile} onOpenChange={(v) => !v && setEditProfile(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Soil Profile</DialogTitle>
            <DialogDescription>Update the soil analysis data for this record.</DialogDescription>
          </DialogHeader>
          {editProfile && (
            <SoilForm mode="edit" lockedFieldId={editProfile.field_id}
              defaultValues={profileToFormValues(editProfile)}
              onSubmit={handleEdit} isPending={updating}
              onCancel={() => setEditProfile(null)} />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete */}
      <DeleteSoilDialog profile={deleteProfile} open={!!deleteProfile}
        onClose={() => setDeleteProfile(null)} />
    </div>
  )
}
