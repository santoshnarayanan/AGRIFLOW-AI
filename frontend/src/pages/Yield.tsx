import { useEffect, useMemo, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, Legend, Cell,
} from 'recharts'
import type { TooltipProps } from 'recharts'
import { Wheat, TrendingUp, Layers, BarChart3, Plus, Pencil, Trash2, AlertTriangle } from 'lucide-react'
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
import { useYieldRecords, useCreateYieldRecord, useUpdateYieldRecord, useDeleteYieldRecord } from '@/api/yield'
import { formatDate, formatDateTime } from '@/lib/utils'
import type { YieldGrade, YieldRecord } from '@/types'

// ─── Yield meta ───────────────────────────────────────────────────────────────

const ALL_GRADES: YieldGrade[] = ['premium', 'grade_a', 'grade_b', 'grade_c', 'commercial', 'reject']

const GRADE_LABEL: Record<YieldGrade, string> = {
  premium: 'Premium',
  grade_a: 'Grade A',
  grade_b: 'Grade B',
  grade_c: 'Grade C',
  commercial: 'Commercial',
  reject: 'Reject',
}

const GRADE_COLOR: Record<YieldGrade, string> = {
  premium: '#8b5cf6',
  grade_a: '#22c55e',
  grade_b: '#84cc16',
  grade_c: '#f59e0b',
  commercial: '#3b82f6',
  reject: '#ef4444',
}

const GRADE_BADGE: Record<YieldGrade, string> = {
  premium: 'text-violet-700 bg-violet-100',
  grade_a: 'text-green-700 bg-green-100',
  grade_b: 'text-lime-700 bg-lime-100',
  grade_c: 'text-amber-700 bg-amber-100',
  commercial: 'text-blue-700 bg-blue-100',
  reject: 'text-red-700 bg-red-100',
}

const UNITS = ['kg', 'tons', 'bushels', 'quintals', 'lbs']

// Grade priority for "best grade" stat (lower index = better)
const GRADE_RANK: Record<YieldGrade, number> = {
  premium: 0, grade_a: 1, grade_b: 2, grade_c: 3, commercial: 4, reject: 5,
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatQty(value: number, unit: string) {
  return `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${unit}`
}

// ─── Chart tooltip ────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border bg-card p-3 shadow-lg text-sm">
      <p className="mb-1 text-xs text-muted-foreground">{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} className="font-medium" style={{ color: p.color }}>
          {p.name}: {Number(p.value).toFixed(2)}
        </p>
      ))}
    </div>
  )
}

// ─── Grade breakdown table ────────────────────────────────────────────────────

function GradeBreakdown({ records }: { records: YieldRecord[] }) {
  const rows = ALL_GRADES.map(g => {
    const gradeRecords = records.filter(r => r.quality_grade === g)
    if (!gradeRecords.length) return null
    const total = gradeRecords.reduce((s, r) => s + r.quantity, 0)
    const unit = gradeRecords[0].unit
    const avgMoisture = gradeRecords.filter(r => r.moisture_content != null).length > 0
      ? gradeRecords.reduce((s, r) => s + (r.moisture_content ?? 0), 0) /
        gradeRecords.filter(r => r.moisture_content != null).length
      : null
    return { grade: g, count: gradeRecords.length, total, unit, avgMoisture }
  }).filter(Boolean)

  const ungraded = records.filter(r => r.quality_grade === null)

  if (!rows.length && !ungraded.length) {
    return <p className="text-sm text-muted-foreground">No records in selected range</p>
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b text-xs text-muted-foreground">
          <th className="pb-2 text-left">Quality Grade</th>
          <th className="pb-2 text-right">Harvests</th>
          <th className="pb-2 text-right">Total Quantity</th>
          <th className="pb-2 text-right">Avg Moisture %</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(r => r && (
          <tr key={r.grade} className="border-b last:border-0 hover:bg-muted/30">
            <td className="py-2">
              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${GRADE_BADGE[r.grade]}`}>
                {GRADE_LABEL[r.grade]}
              </span>
            </td>
            <td className="py-2 text-right font-mono">{r.count}</td>
            <td className="py-2 text-right font-mono font-semibold">
              {formatQty(r.total, r.unit)}
            </td>
            <td className="py-2 text-right font-mono">
              {r.avgMoisture != null ? `${r.avgMoisture.toFixed(1)}%` : '—'}
            </td>
          </tr>
        ))}
        {ungraded.length > 0 && (
          <tr className="border-b last:border-0 hover:bg-muted/30">
            <td className="py-2 text-muted-foreground text-xs">Ungraded</td>
            <td className="py-2 text-right font-mono">{ungraded.length}</td>
            <td className="py-2 text-right font-mono">
              {formatQty(ungraded.reduce((s, r) => s + r.quantity, 0), ungraded[0]?.unit ?? '')}
            </td>
            <td className="py-2 text-right text-muted-foreground">—</td>
          </tr>
        )}
      </tbody>
    </table>
  )
}

// ─── Form schema ──────────────────────────────────────────────────────────────

const recordSchema = z.object({
  farm_id: z.string().min(1, 'Select a farm'),
  field_id: z.string().min(1, 'Select a field'),
  crop_id: z.string(),
  harvest_date: z.string().min(1, 'Harvest date is required'),
  quantity: z.string().refine(v => v !== '' && !isNaN(Number(v)) && Number(v) > 0, { message: 'Enter a positive number' }),
  unit: z.string().min(1, 'Unit is required'),
  quality_grade: z.string(),
  moisture_content: z.string().refine(v => v === '' || !isNaN(Number(v)), { message: 'Must be a number' }),
  area_harvested: z.string().refine(v => v === '' || !isNaN(Number(v)), { message: 'Must be a number' }),
  yield_per_hectare: z.string().refine(v => v === '' || !isNaN(Number(v)), { message: 'Must be a number' }),
  notes: z.string(),
})

interface RecordFormValues {
  farm_id: string; field_id: string; crop_id: string
  harvest_date: string; quantity: string; unit: string
  quality_grade: string; moisture_content: string
  area_harvested: string; yield_per_hectare: string; notes: string
}

const defaultValues: RecordFormValues = {
  farm_id: '', field_id: '', crop_id: '',
  harvest_date: new Date().toISOString().slice(0, 10),
  quantity: '', unit: 'kg', quality_grade: '', moisture_content: '',
  area_harvested: '', yield_per_hectare: '', notes: '',
}

function recordToFormValues(
  r: YieldRecord,
  allFields: { id: number; farm_id: number }[],
): RecordFormValues {
  const field = allFields.find(f => f.id === r.field_id)
  return {
    farm_id: field ? String(field.farm_id) : '',
    field_id: String(r.field_id),
    crop_id: r.crop_id ? String(r.crop_id) : '',
    harvest_date: r.harvest_date.slice(0, 10),
    quantity: String(r.quantity),
    unit: r.unit,
    quality_grade: r.quality_grade ?? '',
    moisture_content: r.moisture_content != null ? String(r.moisture_content) : '',
    area_harvested: r.area_harvested != null ? String(r.area_harvested) : '',
    yield_per_hectare: r.yield_per_hectare != null ? String(r.yield_per_hectare) : '',
    notes: r.notes ?? '',
  }
}

// ─── Create / Edit dialog ─────────────────────────────────────────────────────

interface RecordDialogProps {
  open: boolean
  onOpenChange: (v: boolean) => void
  editing: YieldRecord | null
  allFields: { id: number; name: string; farm_id: number }[]
}

function RecordDialog({ open, onOpenChange, editing, allFields }: RecordDialogProps) {
  const { data: farms = [] } = useFarms()
  const createRecord = useCreateYieldRecord()
  const updateRecord = useUpdateYieldRecord()

  const form = useForm<RecordFormValues>({
    resolver: zodResolver(recordSchema),
    defaultValues,
  })
  const { register, handleSubmit, control, watch, setValue, reset, formState: { errors } } = form

  const watchedFarm = watch('farm_id')
  const watchedField = watch('field_id')
  const watchedQty = watch('quantity')
  const watchedArea = watch('area_harvested')

  const { data: fields = [] } = useFields(watchedFarm ? Number(watchedFarm) : undefined)
  const { data: crops = [] } = useCrops(watchedField ? Number(watchedField) : undefined)

  useEffect(() => {
    if (editing) reset(recordToFormValues(editing, allFields))
    else reset(defaultValues)
  }, [editing, allFields, reset])

  useEffect(() => {
    if (!editing) setValue('field_id', '')
  }, [watchedFarm, editing, setValue])

  useEffect(() => {
    if (!editing) setValue('crop_id', '')
  }, [watchedField, editing, setValue])

  // Auto-calc yield_per_hectare when quantity + area_harvested are filled
  useEffect(() => {
    const qty = Number(watchedQty)
    const area = Number(watchedArea)
    if (qty > 0 && area > 0) {
      setValue('yield_per_hectare', (qty / area).toFixed(2))
    }
  }, [watchedQty, watchedArea, setValue])

  const onSubmit = (values: RecordFormValues) => {
    const payload = {
      crop_id: values.crop_id ? Number(values.crop_id) : undefined,
      harvest_date: values.harvest_date,
      quantity: Number(values.quantity),
      unit: values.unit,
      quality_grade: (values.quality_grade as YieldGrade) || undefined,
      moisture_content: values.moisture_content ? Number(values.moisture_content) : undefined,
      area_harvested: values.area_harvested ? Number(values.area_harvested) : undefined,
      yield_per_hectare: values.yield_per_hectare ? Number(values.yield_per_hectare) : undefined,
      notes: values.notes || undefined,
    }

    if (editing) {
      updateRecord.mutate(
        { id: editing.id, payload },
        { onSuccess: () => { onOpenChange(false); reset(defaultValues) } },
      )
    } else {
      createRecord.mutate(
        { ...payload, field_id: Number(values.field_id) },
        { onSuccess: () => { onOpenChange(false); reset(defaultValues) } },
      )
    }
  }

  const isPending = createRecord.isPending || updateRecord.isPending

  return (
    <Dialog open={open} onOpenChange={v => { onOpenChange(v); if (!v) reset(defaultValues) }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit Yield Record' : 'Record Harvest Yield'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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

            {/* Harvest Date */}
            <div className="space-y-1.5">
              <Label>Harvest Date</Label>
              <Input type="date" {...register('harvest_date')} />
              {errors.harvest_date && <p className="text-xs text-destructive">{errors.harvest_date.message}</p>}
            </div>

            {/* Quantity */}
            <div className="space-y-1.5">
              <Label>Quantity</Label>
              <Input type="number" min="0" step="0.01" placeholder="e.g. 1500" {...register('quantity')} />
              {errors.quantity && <p className="text-xs text-destructive">{errors.quantity.message}</p>}
            </div>

            {/* Unit */}
            <div className="space-y-1.5">
              <Label>Unit</Label>
              <Controller name="unit" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {UNITS.map(u => <SelectItem key={u} value={u}>{u}</SelectItem>)}
                  </SelectContent>
                </Select>
              )} />
            </div>

            {/* Quality Grade */}
            <div className="space-y-1.5">
              <Label>Quality Grade <span className="text-muted-foreground">(optional)</span></Label>
              <Controller name="quality_grade" control={control} render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger><SelectValue placeholder="— Ungraded —" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">— Ungraded —</SelectItem>
                    {ALL_GRADES.map(g => <SelectItem key={g} value={g}>{GRADE_LABEL[g]}</SelectItem>)}
                  </SelectContent>
                </Select>
              )} />
            </div>

            {/* Moisture Content */}
            <div className="space-y-1.5">
              <Label>Moisture Content % <span className="text-muted-foreground">(optional)</span></Label>
              <Input type="number" min="0" max="100" step="0.1" placeholder="e.g. 14.5" {...register('moisture_content')} />
              {errors.moisture_content && <p className="text-xs text-destructive">{errors.moisture_content.message}</p>}
            </div>

            {/* Area Harvested */}
            <div className="space-y-1.5">
              <Label>Area Harvested (ha) <span className="text-muted-foreground">(optional)</span></Label>
              <Input type="number" min="0" step="0.01" placeholder="e.g. 5.0" {...register('area_harvested')} />
              {errors.area_harvested && <p className="text-xs text-destructive">{errors.area_harvested.message}</p>}
            </div>

            {/* Yield per Hectare — auto-calculated */}
            <div className="space-y-1.5">
              <Label>Yield / Hectare <span className="text-muted-foreground">(auto-calculated)</span></Label>
              <Input type="number" step="0.01" placeholder="Auto" {...register('yield_per_hectare')} />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Notes <span className="text-muted-foreground">(optional)</span></Label>
            <Textarea placeholder="Field conditions, equipment notes…" rows={2} {...register('notes')} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => { onOpenChange(false); reset(defaultValues) }}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? (editing ? 'Saving…' : 'Recording…') : editing ? 'Save Changes' : 'Record Yield'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Delete dialog ────────────────────────────────────────────────────────────

interface DeleteDialogProps {
  record: YieldRecord | null
  onOpenChange: (v: boolean) => void
}

function DeleteDialog({ record, onOpenChange }: DeleteDialogProps) {
  const deleteRecord = useDeleteYieldRecord()
  if (!record) return null
  return (
    <Dialog open={!!record} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Yield Record</DialogTitle>
          <DialogDescription asChild>
            <div className="space-y-2 text-sm text-muted-foreground">
              <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-red-800">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <span>
                  This record is stored in a <strong>TimescaleDB hypertable</strong> and cannot be recovered after deletion.
                </span>
              </div>
              <p>
                Delete yield of <strong>{formatQty(record.quantity, record.unit)}</strong> harvested on{' '}
                {formatDate(record.harvest_date)}?
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            variant="destructive"
            disabled={deleteRecord.isPending}
            onClick={() => deleteRecord.mutate(record.id, { onSuccess: () => onOpenChange(false) })}
          >
            {deleteRecord.isPending ? 'Deleting…' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function Yield() {
  const [selectedFarmId, setSelectedFarmId] = useState<number | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<number | undefined>()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<YieldRecord | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<YieldRecord | null>(null)

  const now = new Date()
  const yearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
  const [fromDate, setFromDate] = useState(yearAgo.toISOString().slice(0, 10))
  const [toDate, setToDate] = useState(now.toISOString().slice(0, 10))

  const { data: farms = [] } = useFarms()
  const { data: fields = [] } = useFields(selectedFarmId)
  const { data: allFieldsFlat = [] } = useFields()

  const { data: records = [], isLoading } = useYieldRecords({
    fieldId: selectedFieldId,
    from: fromDate ? `${fromDate}T00:00:00Z` : undefined,
    to: toDate ? `${toDate}T23:59:59Z` : undefined,
  })

  // Stats
  const stats = useMemo(() => {
    if (!records.length) return { totalQty: 0, unit: 'kg', avgYph: null, bestGrade: null, count: 0 }
    const totalQty = records.reduce((s, r) => s + r.quantity, 0)
    const unit = records[0].unit
    const yph = records.filter(r => r.yield_per_hectare != null)
    const avgYph = yph.length
      ? yph.reduce((s, r) => s + r.yield_per_hectare!, 0) / yph.length
      : null
    const graded = records.filter(r => r.quality_grade != null)
    const bestGrade = graded.length
      ? graded.reduce((best, r) =>
          GRADE_RANK[r.quality_grade!] < GRADE_RANK[best.quality_grade!] ? r : best,
        ).quality_grade
      : null
    return { totalQty, unit, avgYph, bestGrade, count: records.length }
  }, [records])

  // Monthly chart data
  const chartData = useMemo(() => {
    const byMonth: Record<string, { quantity: number; yph: number[]; count: number; dominantGrade: string }> = {}
    records.forEach(r => {
      const month = r.harvest_date.slice(0, 7) // YYYY-MM
      if (!byMonth[month]) byMonth[month] = { quantity: 0, yph: [], count: 0, dominantGrade: '' }
      byMonth[month].quantity += r.quantity
      byMonth[month].count += 1
      if (r.yield_per_hectare != null) byMonth[month].yph.push(r.yield_per_hectare)
    })

    return Object.entries(byMonth)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, v]) => ({
        month: new Date(month + '-15').toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
        quantity: v.quantity,
        avgYph: v.yph.length ? v.yph.reduce((a, b) => a + b, 0) / v.yph.length : null,
        count: v.count,
      }))
  }, [records])

  function openCreate() { setEditing(null); setDialogOpen(true) }
  function openEdit(r: YieldRecord) { setEditing(r); setDialogOpen(true) }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Yield Records</h1>
          <p className="text-sm text-muted-foreground">
            Harvest yield tracking · Quantity, quality and productivity analysis
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 size-4" /> Record Yield
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
                <Wheat className="size-4" /> Total Harvest
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">
                {stats.totalQty >= 1000
                  ? `${(stats.totalQty / 1000).toFixed(1)}k`
                  : stats.totalQty.toFixed(1)}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">{stats.unit} in selected range</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <TrendingUp className="size-4" /> Avg Yield / ha
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">
                {stats.avgYph != null ? stats.avgYph.toFixed(1) : '—'}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {stats.avgYph != null ? `${stats.unit} per hectare` : 'No area data'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <BarChart3 className="size-4" /> Harvest Events
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{stats.count}</p>
              <p className="mt-1 text-xs text-muted-foreground">Records in range</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Layers className="size-4" /> Best Grade Seen
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stats.bestGrade ? (
                <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${GRADE_BADGE[stats.bestGrade]}`}>
                  {GRADE_LABEL[stats.bestGrade]}
                </span>
              ) : (
                <p className="text-3xl font-bold">—</p>
              )}
              <p className="mt-2 text-xs text-muted-foreground">Highest quality in range</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Monthly chart + Grade breakdown */}
      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-base">Monthly Harvest Volume</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-56 w-full" />
            ) : chartData.length === 0 ? (
              <div className="flex h-56 items-center justify-center text-muted-foreground text-sm">
                No yield records in the selected range
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <ComposedChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="qty" tick={{ fontSize: 11 }} width={52} />
                  <YAxis yAxisId="yph" orientation="right" tick={{ fontSize: 11 }} width={52} />
                  <RechartsTooltip content={<ChartTooltip />} />
                  <Legend />
                  <Bar yAxisId="qty" dataKey="quantity" name={`Quantity (${stats.unit})`} radius={[3, 3, 0, 0]} maxBarSize={40}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill="#22c55e" />
                    ))}
                  </Bar>
                  {chartData.some(d => d.avgYph != null) && (
                    <Line
                      yAxisId="yph"
                      type="monotone"
                      dataKey="avgYph"
                      name={`Yield/ha (${stats.unit})`}
                      stroke="#f97316"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      connectNulls
                    />
                  )}
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Quality Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
              </div>
            ) : (
              <GradeBreakdown records={records} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Records table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Harvest Log
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({records.length} {records.length === 1 ? 'record' : 'records'})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : records.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground text-sm">
              No yield records found — record the first harvest above
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Harvest Date</th>
                    <th className="px-4 py-2 text-right text-xs text-muted-foreground">Quantity</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Grade</th>
                    <th className="px-4 py-2 text-right text-xs text-muted-foreground">Moisture %</th>
                    <th className="px-4 py-2 text-right text-xs text-muted-foreground">Area (ha)</th>
                    <th className="px-4 py-2 text-right text-xs text-muted-foreground">Yield/ha</th>
                    <th className="px-4 py-2 text-left text-xs text-muted-foreground">Notes</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {[...records]
                    .sort((a, b) => b.harvest_date.localeCompare(a.harvest_date))
                    .map(r => (
                      <tr key={r.id} className="border-b last:border-0 hover:bg-muted/30">
                        <td className="px-4 py-2 font-mono text-xs">{formatDate(r.harvest_date)}</td>
                        <td className="px-4 py-2 text-right font-mono font-semibold">
                          {formatQty(r.quantity, r.unit)}
                        </td>
                        <td className="px-4 py-2">
                          {r.quality_grade ? (
                            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${GRADE_BADGE[r.quality_grade]}`}>
                              {GRADE_LABEL[r.quality_grade]}
                            </span>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="px-4 py-2 text-right font-mono">
                          {r.moisture_content != null ? `${r.moisture_content.toFixed(1)}%` : '—'}
                        </td>
                        <td className="px-4 py-2 text-right font-mono">
                          {r.area_harvested != null ? r.area_harvested.toFixed(2) : '—'}
                        </td>
                        <td className="px-4 py-2 text-right font-mono">
                          {r.yield_per_hectare != null ? r.yield_per_hectare.toFixed(1) : '—'}
                        </td>
                        <td className="max-w-40 px-4 py-2 text-xs text-muted-foreground">
                          <span className="line-clamp-1">{r.notes ?? '—'}</span>
                        </td>
                        <td className="px-4 py-2">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              size="icon" variant="ghost"
                              className="size-7 text-muted-foreground hover:text-foreground"
                              onClick={() => openEdit(r)}
                            >
                              <Pencil className="size-3.5" />
                            </Button>
                            <Button
                              size="icon" variant="ghost"
                              className="size-7 text-muted-foreground hover:text-destructive"
                              onClick={() => setDeleteTarget(r)}
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

      <RecordDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        editing={editing}
        allFields={allFieldsFlat}
      />
      <DeleteDialog record={deleteTarget} onOpenChange={v => { if (!v) setDeleteTarget(null) }} />
    </div>
  )
}
