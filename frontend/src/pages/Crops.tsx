import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2, Wheat, Filter, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
import { useCrops, useCreateCrop, useUpdateCrop, useDeleteCrop } from '@/api/crops'
import { formatDate, cn } from '@/lib/utils'
import type { Crop, GrowthStage, CropStatus, CropCreate, CropUpdate } from '@/types'

// ─── Constants ────────────────────────────────────────────────────────────────

const GROWTH_STAGES: { value: GrowthStage; label: string }[] = [
  { value: 'seedling', label: 'Seedling' },
  { value: 'vegetative', label: 'Vegetative' },
  { value: 'flowering', label: 'Flowering' },
  { value: 'fruiting', label: 'Fruiting' },
  { value: 'ripening', label: 'Ripening' },
  { value: 'harvested', label: 'Harvested' },
]

const CROP_STATUSES: { value: CropStatus; label: string }[] = [
  { value: 'planned', label: 'Planned' },
  { value: 'active', label: 'Active' },
  { value: 'harvested', label: 'Harvested' },
  { value: 'failed', label: 'Failed' },
]

// Stage index for the progress stepper (harvested is terminal, not a middle step)
const STAGE_ORDER: GrowthStage[] = [
  'seedling', 'vegetative', 'flowering', 'fruiting', 'ripening', 'harvested',
]

function stageProgress(stage: GrowthStage) {
  return STAGE_ORDER.indexOf(stage)
}

// ─── Badge helpers ────────────────────────────────────────────────────────────

function statusVariant(status: CropStatus) {
  return (
    { planned: 'info', active: 'success', harvested: 'secondary', failed: 'destructive' } as const
  )[status]
}

function statusLabel(status: CropStatus) {
  return { planned: 'Planned', active: 'Active', harvested: 'Harvested', failed: 'Failed' }[status]
}

// ─── Growth stage stepper ─────────────────────────────────────────────────────

function GrowthStagePill({ stage }: { stage: GrowthStage }) {
  const idx = stageProgress(stage)
  const colors: Record<GrowthStage, string> = {
    seedling: 'bg-lime-100 text-lime-800',
    vegetative: 'bg-green-100 text-green-800',
    flowering: 'bg-pink-100 text-pink-800',
    fruiting: 'bg-orange-100 text-orange-800',
    ripening: 'bg-amber-100 text-amber-800',
    harvested: 'bg-slate-100 text-slate-700',
  }
  return (
    <div className="flex items-center gap-1.5">
      <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold', colors[stage])}>
        {GROWTH_STAGES[idx]?.label ?? stage}
      </span>
    </div>
  )
}

// ─── Form schema ─────────────────────────────────────────────────────────────

const cropSchema = z.object({
  field_id: z.string().min(1, 'Please select a field'),
  name: z.string().min(1, 'Crop name is required').max(255),
  variety: z.string().max(255),
  growth_stage: z.string().min(1, 'Please select a growth stage'),
  status: z.string().min(1, 'Please select a status'),
  planting_date: z.string(),
  expected_harvest_date: z.string(),
})

interface CropFormValues {
  field_id: string
  name: string
  variety: string
  growth_stage: string
  status: string
  planting_date: string
  expected_harvest_date: string
}

// ─── Crop Form ────────────────────────────────────────────────────────────────

interface CropFormProps {
  defaultValues?: Partial<CropFormValues>
  onSubmit: (values: CropFormValues) => void
  isPending: boolean
  onCancel: () => void
  mode: 'create' | 'edit'
  lockedFieldId?: number
  preselectedFarmId?: number
}

function CropForm({
  defaultValues,
  onSubmit,
  isPending,
  onCancel,
  mode,
  lockedFieldId,
  preselectedFarmId,
}: CropFormProps) {
  const { data: farms } = useFarms()
  const [formFarmId, setFormFarmId] = useState<number | undefined>(preselectedFarmId)
  const { data: fields } = useFields(formFarmId)

  const { register, handleSubmit, control, formState: { errors } } = useForm<CropFormValues>({
    resolver: zodResolver(cropSchema),
    defaultValues: {
      field_id: lockedFieldId ? String(lockedFieldId) : '',
      name: '',
      variety: '',
      growth_stage: 'seedling',
      status: 'active',
      planting_date: '',
      expected_harvest_date: '',
      ...defaultValues,
    },
  })

  const lockedField = fields?.find((f) => f.id === lockedFieldId)

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Farm → Field cascade (edit locks field; create allows selection) */}
      {lockedFieldId ? (
        <div className="space-y-2">
          <Label>Field</Label>
          <div className="flex h-10 items-center rounded-md border border-input bg-muted px-3 text-sm text-muted-foreground">
            {lockedField?.name ?? `Field #${lockedFieldId}`}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label>Farm</Label>
            <Select
              value={formFarmId ? String(formFarmId) : ''}
              onValueChange={(v) => setFormFarmId(Number(v))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select farm…" />
              </SelectTrigger>
              <SelectContent>
                {farms?.map((f) => (
                  <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Field *</Label>
            <Controller
              name="field_id"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value}
                  onValueChange={field.onChange}
                  disabled={!formFarmId}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={formFarmId ? 'Select field…' : 'Pick farm first'} />
                  </SelectTrigger>
                  <SelectContent>
                    {fields?.map((f) => (
                      <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.field_id && <p className="text-xs text-destructive">{errors.field_id.message}</p>}
          </div>
        </div>
      )}

      {/* Name + Variety */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="name">Crop Name *</Label>
          <Input id="name" placeholder="e.g. Rice" {...register('name')} />
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="variety">Variety</Label>
          <Input id="variety" placeholder="e.g. IR64, BPT-5204" {...register('variety')} />
        </div>
      </div>

      {/* Growth stage + Status */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>Growth Stage *</Label>
          <Controller
            name="growth_stage"
            control={control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select stage…" />
                </SelectTrigger>
                <SelectContent>
                  {GROWTH_STAGES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.growth_stage && <p className="text-xs text-destructive">{errors.growth_stage.message}</p>}
        </div>
        <div className="space-y-2">
          <Label>Status *</Label>
          <Controller
            name="status"
            control={control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select status…" />
                </SelectTrigger>
                <SelectContent>
                  {CROP_STATUSES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
      </div>

      {/* Dates */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="planting_date">Planting Date</Label>
          <Input id="planting_date" type="date" {...register('planting_date')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="expected_harvest_date">Expected Harvest</Label>
          <Input id="expected_harvest_date" type="date" {...register('expected_harvest_date')} />
        </div>
      </div>

      <DialogFooter className="pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Saving…' : mode === 'create' ? 'Add Crop' : 'Save Changes'}
        </Button>
      </DialogFooter>
    </form>
  )
}

// ─── Delete confirm ───────────────────────────────────────────────────────────

function DeleteCropDialog({
  crop,
  open,
  onClose,
}: {
  crop: Crop | null
  open: boolean
  onClose: () => void
}) {
  const { mutate: deleteCrop, isPending } = useDeleteCrop()
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Crop</DialogTitle>
          <DialogDescription>
            Delete <strong>{crop?.name}{crop?.variety ? ` (${crop.variety})` : ''}</strong>?
            Associated yield records, disease observations, irrigation events, and AI
            recommendations linked to this crop will lose their crop reference (set to null).
            This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>Cancel</Button>
          <Button
            variant="destructive"
            disabled={isPending}
            onClick={() => crop && deleteCrop(crop.id, { onSuccess: onClose })}
          >
            {isPending ? 'Deleting…' : 'Delete Crop'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function Crops() {
  const { data: farms, isLoading: farmsLoading } = useFarms()

  const [selectedFarmId, setSelectedFarmId] = useState<number | undefined>()
  const [selectedFieldId, setSelectedFieldId] = useState<number | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [editCrop, setEditCrop] = useState<Crop | null>(null)
  const [deleteCrop, setDeleteCrop] = useState<Crop | null>(null)

  const { data: fields } = useFields(selectedFarmId)
  const { data: crops, isLoading: cropsLoading, isError } = useCrops(selectedFieldId)
  const { mutate: createCrop, isPending: creating } = useCreateCrop()
  const { mutate: updateCrop, isPending: updating } = useUpdateCrop()

  // Reset field selection when farm changes
  function handleFarmChange(farmId: string) {
    setSelectedFarmId(farmId === 'all' ? undefined : Number(farmId))
    setSelectedFieldId(undefined)
  }

  function handleCreate(values: CropFormValues) {
    const payload: CropCreate = {
      field_id: Number(values.field_id),
      name: values.name,
      variety: values.variety || undefined,
      growth_stage: values.growth_stage as GrowthStage,
      status: values.status as CropStatus,
      planting_date: values.planting_date || undefined,
      expected_harvest_date: values.expected_harvest_date || undefined,
    }
    createCrop(payload, { onSuccess: () => setCreateOpen(false) })
  }

  function handleEdit(values: CropFormValues) {
    if (!editCrop) return
    const payload: CropUpdate = {
      name: values.name,
      variety: values.variety || undefined,
      growth_stage: values.growth_stage as GrowthStage,
      status: values.status as CropStatus,
      planting_date: values.planting_date || undefined,
      expected_harvest_date: values.expected_harvest_date || undefined,
    }
    updateCrop({ id: editCrop.id, payload }, { onSuccess: () => setEditCrop(null) })
  }

  const activeCrops = crops?.filter((c) => c.status === 'active').length ?? 0
  const harvestedCrops = crops?.filter((c) => c.status === 'harvested').length ?? 0

  const selectedFarm = farms?.find((f) => f.id === selectedFarmId)
  const selectedField = fields?.find((f) => f.id === selectedFieldId)

  return (
    <div className="space-y-6">
      {/* Cascading filters + Add Crop */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-muted-foreground">Farm:</span>
        </div>
        {farmsLoading ? (
          <Skeleton className="h-10 w-44" />
        ) : (
          <Select
            value={selectedFarmId ? String(selectedFarmId) : 'all'}
            onValueChange={handleFarmChange}
          >
            <SelectTrigger className="w-44">
              <SelectValue placeholder="All farms" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All farms</SelectItem>
              {farms?.map((f) => (
                <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {selectedFarmId && (
          <>
            <span className="text-muted-foreground">›</span>
            <span className="text-sm font-medium text-muted-foreground">Field:</span>
            <Select
              value={selectedFieldId ? String(selectedFieldId) : 'all'}
              onValueChange={(v) => setSelectedFieldId(v === 'all' ? undefined : Number(v))}
            >
              <SelectTrigger className="w-44">
                <SelectValue placeholder="All fields" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All fields</SelectItem>
                {fields?.map((f) => (
                  <SelectItem key={f.id} value={String(f.id)}>{f.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </>
        )}

        <div className="flex-1" />
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Crop
        </Button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold">{crops?.length ?? '—'}</p>
            <p className="text-xs text-muted-foreground mt-0.5">Total Crops</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-green-600">{crops ? activeCrops : '—'}</p>
            <p className="text-xs text-muted-foreground mt-0.5">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-slate-500">{crops ? harvestedCrops : '—'}</p>
            <p className="text-xs text-muted-foreground mt-0.5">Harvested</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold">
              {crops
                ? [...new Set(crops.map((c) => c.name))].length
                : '—'}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">Unique Varieties</p>
          </CardContent>
        </Card>
      </div>

      {/* Crops table */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              {selectedField
                ? `Crops — ${selectedField.name}`
                : selectedFarm
                ? `Crops — ${selectedFarm.name}`
                : 'All Crops'}
            </CardTitle>
            {crops && crops.length > 0 && (
              <div className="flex items-center gap-1.5 text-xs text-green-600">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>{activeCrops} active</span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {cropsLoading ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : isError ? (
            <div className="py-12 text-center text-sm text-destructive">
              Failed to load crops. Is the backend running?
            </div>
          ) : crops?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <Wheat className="mb-3 h-10 w-10 opacity-20" />
              <p className="font-medium">No crops yet</p>
              <p className="text-sm">
                {selectedField
                  ? `Add the first crop to ${selectedField.name}.`
                  : 'Select a field or click "Add Crop" to get started.'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Crop</TableHead>
                  <TableHead>Field</TableHead>
                  <TableHead>Growth Stage</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Planting Date</TableHead>
                  <TableHead>Expected Harvest</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {crops?.map((crop) => {
                  const field = fields?.find((f) => f.id === crop.field_id)
                  return (
                    <TableRow key={crop.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{crop.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {crop.variety ?? <span className="italic">No variety</span>}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="text-sm font-medium">
                            {field?.name ?? `Field #${crop.field_id}`}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {farms?.find((f) => f.id === field?.farm_id)?.name ?? ''}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <GrowthStagePill stage={crop.growth_stage} />
                      </TableCell>
                      <TableCell>
                        <Badge variant={statusVariant(crop.status)}>
                          {statusLabel(crop.status)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {crop.planting_date ? formatDate(crop.planting_date) : '—'}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {crop.expected_harvest_date ? formatDate(crop.expected_harvest_date) : '—'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setEditCrop(crop)}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => setDeleteCrop(crop)}
                          >
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

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Add New Crop</DialogTitle>
            <DialogDescription>
              Register a crop within one of your fields.
            </DialogDescription>
          </DialogHeader>
          <CropForm
            mode="create"
            lockedFieldId={selectedFieldId}
            preselectedFarmId={selectedFarmId}
            defaultValues={
              selectedFieldId
                ? { field_id: String(selectedFieldId) }
                : selectedFarmId
                ? {}
                : undefined
            }
            onSubmit={handleCreate}
            isPending={creating}
            onCancel={() => setCreateOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editCrop} onOpenChange={(v) => !v && setEditCrop(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Crop</DialogTitle>
            <DialogDescription>
              Update details for {editCrop?.name}
              {editCrop?.variety ? ` (${editCrop.variety})` : ''}.
            </DialogDescription>
          </DialogHeader>
          {editCrop && (
            <CropForm
              mode="edit"
              lockedFieldId={editCrop.field_id}
              defaultValues={{
                field_id: String(editCrop.field_id),
                name: editCrop.name,
                variety: editCrop.variety ?? '',
                growth_stage: editCrop.growth_stage,
                status: editCrop.status,
                planting_date: editCrop.planting_date ?? '',
                expected_harvest_date: editCrop.expected_harvest_date ?? '',
              }}
              onSubmit={handleEdit}
              isPending={updating}
              onCancel={() => setEditCrop(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <DeleteCropDialog
        crop={deleteCrop}
        open={!!deleteCrop}
        onClose={() => setDeleteCrop(null)}
      />
    </div>
  )
}
