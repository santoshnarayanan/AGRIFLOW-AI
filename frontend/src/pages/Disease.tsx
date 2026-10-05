import { useEffect, useMemo, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, Legend,
} from 'recharts'
import type { TooltipProps } from 'recharts'
import { Bug, AlertTriangle, Microscope, CalendarDays, Plus, Pencil, Trash2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useFarms } from '@/api/farms'
import { useFields } from '@/api/fields'
import { useCrops } from '@/api/crops'
import {
  useDiseaseObservations, useCreateDiseaseObservation,
  useUpdateDiseaseObservation, useDeleteDiseaseObservation,
} from '@/api/disease'
import { formatDate, formatDateTime } from '@/lib/utils'
import type { DiseaseSeverity, DiseaseObservation } from '@/types'

// ─── Disease meta ─────────────────────────────────────────────────────────────

const ALL_SEVERITIES: DiseaseSeverity[] = ['low', 'moderate', 'high', 'critical']

const SEV_LABEL: Record<DiseaseSeverity, string> = {
  low: 'Low', moderate: 'Moderate', high: 'High', critical: 'Critical',
}

const SEV_COLOR: Record<DiseaseSeverity, string> = {
  low: '#22c55e', moderate: '#f59e0b', high: '#f97316', critical: '#ef4444',
}

const SEV_BADGE: Record<DiseaseSeverity, string> = {
  low: 'text-green-700 bg-green-100',
  moderate: 'text-amber-700 bg-amber-100',
  high: 'text-orange-700 bg-orange-100',
  critical: 'text-red-700 bg-red-100',
}

// Higher = worse (used for "worst severity" stat)
const SEV_RANK: Record<DiseaseSeverity, number> = { low: 0, moderate: 1, high: 2, critical: 3 }

// Common disease suggestions for datalist
const DISEASE_SUGGESTIONS = [
  'Powdery Mildew', 'Downy Mildew', 'Early Blight', 'Late Blight', 'Anthracnose',
  'Fusarium Wilt', 'Bacterial Leaf Blight', 'Rust', 'Leaf Spot', 'Root Rot',
  'Crown Gall', 'Mosaic Virus', 'Leaf Curl Virus', 'Aphid Infestation',
  'Whitefly Infestation', 'Spider Mite', 'Stem Borer', 'Damping Off',
]

// ─── Helpers ──────────────────────────────────────────────────────────────────

function toDatetimeLocal(iso: string) {
  const d = new Date(iso)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}

// ─── Chart tooltip ────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border bg-card p-3 shadow-lg text-sm">
      <p className="mb-2 text-xs font-medium text-muted-foreground">{label}</p>
      {payload.map(p => p.value ? (
        <p key={p.dataKey} className="font-medium" style={{ color: p.color }}>
          {p.name}: {p.value}
        </p>
      ) : null)}
    </div>
  )
}

// ─── Disease frequency table ──────────────────────────────────────────────────

function DiseaseFrequency({ observations }: { observations: DiseaseObservation[] }) {
  const rows = useMemo(() => {
    const freq: Record<string, {
      count: number; maxSeverity: DiseaseSeverity; totalArea: number; areaCount: number
    }> = {}
    observations.forEach(o => {
      if (!freq[o.disease_name]) {
        freq[o.disease_name] = { count: 0, maxSeverity: 'low', totalArea: 0, areaCount: 0 }
      }
      freq[o.disease_name].count++
      if (SEV_RANK[o.severity] > SEV_RANK[freq[o.disease_name].maxSeverity]) {
        freq[o.disease_name].maxSeverity = o.severity
      }
      if (o.affected_area_percentage != null) {
        freq[o.disease_name].totalArea += o.affected_area_percentage
        freq[o.disease_name].areaCount++
      }
    })
    return Object.entries(freq)
      .sort(([, a], [, b]) => b.count - a.count || SEV_RANK[b.maxSeverity] - SEV_RANK[a.maxSeverity])
      .slice(0, 8)
      .map(([name, d]) => ({
        name,
        count: d.count,
        maxSeverity: d.maxSeverity,
        avgArea: d.areaCount > 0 ? d.totalArea / d.areaCount : null,
      }))
  }, [observations])

  if (!rows.length) {
    return <p className="text-sm text-muted-foreground">No observations in selected range</p>
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b text-xs text-muted-foreground">
          <th className="pb-2 text-left">Disease</th>
          <th className="pb-2 text-right">Obs.</th>
          <th className="pb-2 text-center">Max Severity</th>
          <th className="pb-2 text-right">Avg Area %</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(r => (
          <tr key={r.name} className="border-b last:border-0 hover:bg-muted/30">
            <td className="py-2 font-medium">{r.name}</td>
            <td className="py-2 text-right font-mono">{r.count}</td>
            <td className="py-2 text-center">
              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${SEV_BADGE[r.maxSeverity]}`}>
                {SEV_LABEL[r.maxSeverity]}
              </span>
            </td>
            <td className="py-2 text-right font-mono">
              {r.avgArea != null ? `${r.avgArea.toFixed(1)}%` : '—'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// ─── Form schema ──────────────────────────────────────────────────────────────

const obsSchema = z.object({
  farm_id: z.string().min(1, 'Select a farm'),
  field_id: z.string().min(1, 'Select a field'),
  crop_id: z.string(),
  disease_name: z.string().min(1, 'Disease name is required'),
  severity: z.string().min(1, 'Severity is required'),
  observed_at: z.string().min(1, 'Observed at is required'),
  affected_area_percentage: z.string().refine(
    v => v === '' || (!isNaN(Number(v)) && Number(v) >= 0 && Number(v) <= 100),
    { message: 'Enter 0–100' },
  ),
  symptoms: z.string(),
  treatment_applied: z.string(),
  treatment_date: z.string(),
  notes: z.string(),
})

interface ObsFormValues {
  farm_id: string; field_id: string; crop_id: string
  disease_name: string; severity: string; observed_at: string
  affected_area_percentage: string; symptoms: string
  treatment_applied: string; treatment_date: string; notes: string
}

const defaultValues: ObsFormValues = {
  farm_id: '', field_id: '', crop_id: '',
  disease_name: '', severity: 'moderate',
  observed_at: toDatetimeLocal(new Date().toISOString()),
  affected_area_percentage: '', symptoms: '',
  treatment_applied: '', treatment_date: '', notes: '',
}

function obsToFormValues(
  o: DiseaseObservation,
  allFields: { id: number; farm_id: number }[],
): ObsFormValues {
  const field = allFields.find(f => f.id === o.field_id)
  return {
    farm_id: field ? String(field.farm_id) : '',
    field_id: String(o.field_id),
    crop_id: o.crop_id ? String(o.crop_id) : '',
    disease_name: o.disease_name,
    severity: o.severity,
    observed_at: toDatetimeLocal(o.observed_at),
    affected_area_percentage: o.affected_area_percentage != null
      ? String(o.affected_area_percentage) : '',
    symptoms: o.symptoms ?? '',
    treatment_applied: o.treatment_applied ?? '',
    treatment_date: o.treatment_date ? o.treatment_date.slice(0, 10) : '',
    notes: o.notes ?? '',
  }
}

// ─── Create / Edit dialog ─────────────────────────────────────────────────────

interface ObsDialogProps {
  open: boolean
  onOpenChange: (v: boolean) => void
  editing: DiseaseObservation | null
  allFields: { id: number; name: string; farm_id: number }[]
}

function ObsDialog({ open, onOpenChange, editing, allFields }: ObsDialogProps) {
  const { data: farms = [] } = useFarms()
  const createObs = useCreateDiseaseObservation()
  const updateObs = useUpdateDiseaseObservation()

  const form = useForm<ObsFormValues>({
    resolver: zodResolver(obsSchema),
    defaultValues,
  })
  const { register, handleSubmit, control, watch, setValue, reset, formState: { errors } } = form

  const watchedFarm = watch('farm_id')
  const watchedField = watch('field_id')

  const { data: fields = [] } = useFields(watchedFarm ? Number(watchedFarm) : undefined)
  const { data: crops = [] } = useCrops(watchedField ? Number(watchedField) : undefined)

  useEffect(() => {
    if (editing) reset(obsToFormValues(editing, allFields))
    else reset(defaultValues)
  }, [editing, allFields, reset])

  useEffect(() => { if (!editing) setValue('field_id', '') }, [watchedFarm, editing, setValue])
  useEffect(() => { if (!editing) setValue('crop_id', '') }, [watchedField, editing, setValue])

  const onSubmit = (values: ObsFormValues) => {
    const payload = {
      crop_id: values.crop_id ? Number(values.crop_id) : undefined,
      disease_name: values.disease_name.trim(),
      severity: values.severity as DiseaseSeverity,
      observed_at: new Date(values.observed_at).toISOString(),
      affected_area_percentage: values.affected_area_percentage
        ? Number(values.affected_area_percentage) : undefined,
      symptoms: values.symptoms || undefined,
      treatment_applied: values.treatment_applied || undefined,
      treatment_date: values.treatment_date || undefined,
      notes: values.notes || undefined,
    }

    if (editing) {
      updateObs.mutate(
        { id: editing.id, payload },
        { onSuccess: () => { onOpenChange(false); reset(defaultValues) } },
      )
    } else {
      createObs.mutate(
        { ...payload, field_id: Number(values.field_id) },
        { onSuccess: () => { onOpenChange(false); reset(defaultValues) } },
      )
    }
  }

  const isPending = createObs.isPending || updateObs.isPending

  return (
    <Dialog open={open} onOpenChange={v => { onOpenChange(v); if (!v) reset(defaultValues) }}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {editing ? 'Edit Disease Observation' : 'Log Disease Observation'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* datalist for disease name suggestions */}
          <datalist id="disease-suggestions">
            {DISEASE_SUGGESTIONS.map(d => <option key={d} value={d} />)}
          </datalist>

          <div className="grid grid-cols-2 gap-3">
            {/* Farm — locked in edit */}
            <div className="space-y-1.5">
              <Label>Farm</Label>
              {editing ? (
                <Input
                  value={farms.find(f => f.id === allFields.find(fi => fi.id === editing.field_id)?.farm_id)?.name ?? '—'}
                  readOnly className="bg-muted text-muted-foreground"
                />
              ) : (
                <Controller name="farm_id" control={control} render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger><SelectValue placeholder="Select farm" /></SelectTrigger>
                    <SelectContent>
                      {farms.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                )} />
              )}
              {errors.farm_id && <p className="text-xs text-destructive">{errors.farm_id.message}</p>}
            </div>

            {/* Field — locked in edit */}
            <div className="space-y-1.5">
              <Label>Field</Label>
              {editing ? (
                <Input
                  value={allFields.find(f => f.id === editing.field_id)?.name ?? '—'}
                  readOnly className="bg-muted text-muted-foreground"
                />
              ) : (
                <Controller name="field_id" control={control} render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange} disabled={!watchedFarm}>
                    <SelectTrigger>
                      <SelectValue placeholder={watchedFarm ? 'Select field' : 'Select farm first'} />
                    </SelectTrigger>
                    <SelectContent>
                      {fields.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                )} />
              )}
              {errors.field_id && <p className="text-xs text-destructive">{errors.field_id.message}</p>}
            </div>

            {/* Crop */}
            <div className="space-y-1.5">
              <Label>Crop <span className="text-muted-foreground">(optional)</span></Label>
              <Controller name="crop_id" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange} disabled={!watchedField && !editing}>
                  <SelectTrigger><SelectValue placeholder="— No crop —" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">— No crop —</SelectItem>
                    {crops.map(c => (
                      <SelectItem key={c.id} value={String(c.id)}>
                        {c.name}{c.variety ? ` (${c.variety})` : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )} />
            </div>

            {/* Observed At */}
            <div className="space-y-1.5">
              <Label>Observed At</Label>
              <Input type="datetime-local" {...register('observed_at')} />
              {errors.observed_at && <p className="text-xs text-destructive">{errors.observed_at.message}</p>}
            </div>

            {/* Disease name */}
            <div className="col-span-2 space-y-1.5">
              <Label>Disease / Pest Name</Label>
              <Input
                list="disease-suggestions"
                placeholder="e.g. Powdery Mildew, Aphid Infestation…"
                {...register('disease_name')}
              />
              {errors.disease_name && <p className="text-xs text-destructive">{errors.disease_name.message}</p>}
            </div>

            {/* Severity */}
            <div className="space-y-1.5">
              <Label>Severity</Label>
              <Controller name="severity" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {ALL_SEVERITIES.map(s => (
                      <SelectItem key={s} value={s}>
                        <div className="flex items-center gap-2">
                          <span className="inline-block size-2 rounded-full" style={{ background: SEV_COLOR[s] }} />
                          {SEV_LABEL[s]}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )} />
              {errors.severity && <p className="text-xs text-destructive">{errors.severity.message}</p>}
            </div>

            {/* Affected area */}
            <div className="space-y-1.5">
              <Label>Affected Area % <span className="text-muted-foreground">(optional)</span></Label>
              <Input type="number" min="0" max="100" step="0.1" placeholder="e.g. 25" {...register('affected_area_percentage')} />
              {errors.affected_area_percentage && <p className="text-xs text-destructive">{errors.affected_area_percentage.message}</p>}
            </div>
          </div>

          {/* Symptoms */}
          <div className="space-y-1.5">
            <Label>Symptoms <span className="text-muted-foreground">(optional)</span></Label>
            <Textarea placeholder="Describe visible symptoms, affected plant parts…" rows={2} {...register('symptoms')} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Treatment applied */}
            <div className="space-y-1.5">
              <Label>Treatment Applied <span className="text-muted-foreground">(optional)</span></Label>
              <Input placeholder="e.g. Fungicide spray" {...register('treatment_applied')} />
            </div>

            {/* Treatment date */}
            <div className="space-y-1.5">
              <Label>Treatment Date <span className="text-muted-foreground">(optional)</span></Label>
              <Input type="date" {...register('treatment_date')} />
            </div>
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <Label>Notes <span className="text-muted-foreground">(optional)</span></Label>
            <Textarea placeholder="Any additional observations…" rows={2} {...register('notes')} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => { onOpenChange(false); reset(defaultValues) }}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? (editing ? 'Saving…' : 'Logging…') : editing ? 'Save Changes' : 'Log Observation'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Delete dialog ────────────────────────────────────────────────────────────

interface DeleteDialogProps {
  obs: DiseaseObservation | null
  onOpenChange: (v: boolean) => void
}

function DeleteDialog({ obs, onOpenChange }: DeleteDialogProps) {
  const deleteObs = useDeleteDiseaseObservation()
  if (!obs) return null
  return (
    <Dialog open={!!obs} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Observation</DialogTitle>
          <DialogDescription asChild>
            <div className="space-y-2 text-sm text-muted-foreground">
              <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-red-800">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <span>This observation is stored in a <strong>TimescaleDB hypertable</strong> and cannot be recovered after deletion.</span>
              </div>
              <p>
                Delete <strong>{obs.disease_name}</strong> observation recorded on{' '}
                {formatDate(obs.observed_at)} (severity: {SEV_LABEL[obs.severity]})?
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            variant="destructive"
            disabled={deleteObs.isPending}
            onClick={() => deleteObs.mutate(obs.id, { onSuccess: () => onOpenChange(false) })}
          >
            {deleteObs.isPending ? 'Deleting…' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function Disease() {
  const [selectedFarmId, setSelectedFarmId] = useState<number | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<number | undefined>()
  const [severityFilter, setSeverityFilter] = useState<DiseaseSeverity | 'all'>('all')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<DiseaseObservation | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<DiseaseObservation | null>(null)

  const now = new Date()
  const sixMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 6, now.getDate())
  const [fromDate, setFromDate] = useState(sixMonthsAgo.toISOString().slice(0, 10))
  const [toDate, setToDate] = useState(now.toISOString().slice(0, 10))

  const { data: farms = [] } = useFarms()
  const { data: fields = [] } = useFields(selectedFarmId)
  const { data: allFieldsFlat = [] } = useFields()

  const { data: observations = [], isLoading } = useDiseaseObservations({
    fieldId: selectedFieldId,
    severity: severityFilter !== 'all' ? severityFilter : undefined,
    from: fromDate ? `${fromDate}T00:00:00Z` : undefined,
    to: toDate ? `${toDate}T23:59:59Z` : undefined,
  })

  // Stats
  const stats = useMemo(() => {
    const worstSev = observations.length
      ? observations.reduce((w, o) =>
          SEV_RANK[o.severity] > SEV_RANK[w.severity] ? o : w,
        ).severity
      : null
    const areas = observations.filter(o => o.affected_area_percentage != null)
    const avgArea = areas.length
      ? areas.reduce((s, o) => s + o.affected_area_percentage!, 0) / areas.length
      : null
    const treated = observations.filter(o => o.treatment_applied != null).length
    const latest = [...observations].sort((a, b) => b.observed_at.localeCompare(a.observed_at))[0]?.observed_at ?? null
    return { count: observations.length, worstSev, avgArea, treated, latest }
  }, [observations])

  // Monthly stacked chart data
  const chartData = useMemo(() => {
    const byMonth: Record<string, Record<DiseaseSeverity, number>> = {}
    observations.forEach(o => {
      const month = o.observed_at.slice(0, 7)
      if (!byMonth[month]) byMonth[month] = { low: 0, moderate: 0, high: 0, critical: 0 }
      byMonth[month][o.severity]++
    })
    return Object.entries(byMonth)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, counts]) => ({
        month: new Date(month + '-15').toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
        ...counts,
      }))
  }, [observations])

  function openCreate() { setEditing(null); setDialogOpen(true) }
  function openEdit(o: DiseaseObservation) { setEditing(o); setDialogOpen(true) }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Disease Observations</h1>
          <p className="text-sm text-muted-foreground">
            Plant disease and pest detection log · Severity tracking and treatment records
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 size-4" /> Log Observation
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Select
          value={selectedFarmId ? String(selectedFarmId) : 'all'}
          onValueChange={v => {
            setSelectedFarmId(v !== 'all' ? Number(v) : undefined)
            setSelectedFieldId(undefined)
          }}
        >
          <SelectTrigger className="w-44"><SelectValue placeholder="All farms" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All farms</SelectItem>
            {farms.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select
          value={selectedFieldId ? String(selectedFieldId) : 'all'}
          onValueChange={v => setSelectedFieldId(v !== 'all' ? Number(v) : undefined)}
          disabled={!selectedFarmId}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder={selectedFarmId ? 'All fields' : 'Select farm'} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All fields</SelectItem>
            {fields.map(f => <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select
          value={severityFilter}
          onValueChange={v => setSeverityFilter(v as DiseaseSeverity | 'all')}
        >
          <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All severities</SelectItem>
            {ALL_SEVERITIES.map(s => (
              <SelectItem key={s} value={s}>
                <div className="flex items-center gap-2">
                  <span className="inline-block size-2 rounded-full" style={{ background: SEV_COLOR[s] }} />
                  {SEV_LABEL[s]}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex items-center gap-2">
          <Input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} className="w-36" />
          <span className="text-muted-foreground text-sm">to</span>
          <Input type="date" value={toDate} onChange={e => setToDate(e.target.value)} className="w-36" />
        </div>
      </div>

      {/* Stat cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-lg" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Bug className="size-4" /> Observations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{stats.count}</p>
              <p className="mt-1 text-xs text-muted-foreground">In selected range</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <AlertTriangle className="size-4" /> Worst Severity
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stats.worstSev ? (
                <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${SEV_BADGE[stats.worstSev]}`}>
                  {SEV_LABEL[stats.worstSev]}
                </span>
              ) : (
                <p className="text-3xl font-bold">—</p>
              )}
              <p className="mt-2 text-xs text-muted-foreground">Highest in range</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Microscope className="size-4" /> Avg Affected Area
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">
                {stats.avgArea != null ? `${stats.avgArea.toFixed(1)}%` : '—'}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {stats.treated} of {stats.count} treated
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <CalendarDays className="size-4" /> Latest Observation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-bold leading-tight">
                {stats.latest ? formatDate(stats.latest) : '—'}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">Most recent record</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Chart + Disease frequency */}
      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-base">Monthly Observations by Severity</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-56 w-full" />
            ) : chartData.length === 0 ? (
              <div className="flex h-56 items-center justify-center text-muted-foreground text-sm">
                No observations in the selected range
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} width={30} />
                  <RechartsTooltip content={<ChartTooltip />} />
                  <Legend />
                  <Bar dataKey="critical" name="Critical" stackId="a" fill={SEV_COLOR.critical} />
                  <Bar dataKey="high" name="High" stackId="a" fill={SEV_COLOR.high} />
                  <Bar dataKey="moderate" name="Moderate" stackId="a" fill={SEV_COLOR.moderate} />
                  <Bar dataKey="low" name="Low" stackId="a" fill={SEV_COLOR.low} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Top Diseases</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
              </div>
            ) : (
              <DiseaseFrequency observations={observations} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Observations table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Observation Log
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({observations.length} {observations.length === 1 ? 'record' : 'records'})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : observations.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground text-sm">
              No disease observations found — log the first one above
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Observed At</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Disease / Pest</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Severity</th>
                    <th className="px-4 py-2 text-right text-xs text-muted-foreground">Area %</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Treatment</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Treat. Date</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {[...observations]
                    .sort((a, b) => b.observed_at.localeCompare(a.observed_at))
                    .map(o => (
                      <tr key={o.id} className="border-b last:border-0 hover:bg-muted/30">
                        <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                          {formatDateTime(o.observed_at)}
                        </td>
                        <td className="px-4 py-2 font-medium">{o.disease_name}</td>
                        <td className="px-4 py-2">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${SEV_BADGE[o.severity]}`}>
                            {SEV_LABEL[o.severity]}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right font-mono">
                          {o.affected_area_percentage != null
                            ? `${o.affected_area_percentage.toFixed(1)}%`
                            : '—'}
                        </td>
                        <td className="max-w-36 px-4 py-2 text-xs text-muted-foreground">
                          <span className="line-clamp-1">
                            {o.treatment_applied ?? '—'}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-xs text-muted-foreground">
                          {o.treatment_date ? formatDate(o.treatment_date) : '—'}
                        </td>
                        <td className="px-4 py-2">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              size="icon" variant="ghost"
                              className="size-7 text-muted-foreground hover:text-foreground"
                              onClick={() => openEdit(o)}
                            >
                              <Pencil className="size-3.5" />
                            </Button>
                            <Button
                              size="icon" variant="ghost"
                              className="size-7 text-muted-foreground hover:text-destructive"
                              onClick={() => setDeleteTarget(o)}
                            >
                              <Trash2 className="size-3.5" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <ObsDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        editing={editing}
        allFields={allFieldsFlat}
      />
      <DeleteDialog obs={deleteTarget} onOpenChange={v => { if (!v) setDeleteTarget(null) }} />
    </div>
  )
}
