import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2, Tractor } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter, DialogDescription,
} from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useFarms, useCreateFarm, useUpdateFarm, useDeleteFarm } from '@/api/farms'
import { formatDate } from '@/lib/utils'
import type { Farm } from '@/types'

// Form uses string inputs; we validate and convert on submit
interface FarmFormValues {
  name: string
  location: string
  area: string
}

const farmSchema = z.object({
  name: z.string().min(1, 'Farm name is required').max(255),
  location: z.string().max(500),
  area: z.string().refine((v) => v === '' || (!isNaN(Number(v)) && Number(v) > 0), {
    message: 'Area must be a positive number',
  }),
})

interface FarmFormProps {
  defaultValues?: Partial<FarmFormValues>
  onSubmit: (values: FarmFormValues) => void
  isPending: boolean
  onCancel: () => void
  mode: 'create' | 'edit'
}

function FarmForm({ defaultValues, onSubmit, isPending, onCancel, mode }: FarmFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<FarmFormValues>({
    resolver: zodResolver(farmSchema),
    defaultValues: { name: '', location: '', area: '', ...defaultValues },
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Farm Name *</Label>
        <Input id="name" placeholder="e.g. Green Valley Farm" {...register('name')} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="location">Location</Label>
        <Input id="location" placeholder="e.g. Karnataka, India" {...register('location')} />
        {errors.location && <p className="text-xs text-destructive">{errors.location.message}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="area">Area (hectares)</Label>
        <Input id="area" type="number" step="0.01" placeholder="e.g. 120.5" {...register('area')} />
        {errors.area && <p className="text-xs text-destructive">{errors.area.message}</p>}
      </div>
      <DialogFooter className="pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Saving…' : mode === 'create' ? 'Create Farm' : 'Save Changes'}
        </Button>
      </DialogFooter>
    </form>
  )
}

function DeleteConfirmDialog({
  farm,
  open,
  onClose,
}: {
  farm: Farm | null
  open: boolean
  onClose: () => void
}) {
  const { mutate: deleteFarm, isPending } = useDeleteFarm()

  function handleDelete() {
    if (!farm) return
    deleteFarm(farm.id, { onSuccess: onClose })
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Farm</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong>{farm?.name}</strong>? This action cannot be
            undone and will remove all associated data.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>Cancel</Button>
          <Button variant="destructive" onClick={handleDelete} disabled={isPending}>
            {isPending ? 'Deleting…' : 'Delete Farm'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function Farms() {
  const { data: farms, isLoading, isError } = useFarms()
  const { mutate: createFarm, isPending: creating } = useCreateFarm()
  const { mutate: updateFarm, isPending: updating } = useUpdateFarm()

  const [createOpen, setCreateOpen] = useState(false)
  const [editFarm, setEditFarm] = useState<Farm | null>(null)
  const [deleteFarm, setDeleteFarm] = useState<Farm | null>(null)

  function handleCreate(values: FarmFormValues) {
    createFarm(
      {
        name: values.name,
        location: values.location || undefined,
        area: values.area ? Number(values.area) : undefined,
      },
      { onSuccess: () => setCreateOpen(false) }
    )
  }

  function handleEdit(values: FarmFormValues) {
    if (!editFarm) return
    updateFarm(
      {
        id: editFarm.id,
        payload: {
          name: values.name,
          location: values.location || undefined,
          area: values.area ? Number(values.area) : undefined,
        },
      },
      { onSuccess: () => setEditFarm(null) }
    )
  }

  return (
    <div className="space-y-6">
      {/* Action header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            {farms ? `${farms.length} farm${farms.length !== 1 ? 's' : ''} registered` : ''}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Farm
        </Button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-foreground">{farms?.length ?? '—'}</p>
            <p className="text-xs text-muted-foreground mt-0.5">Total Farms</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-foreground">
              {farms?.reduce((s, f) => s + (f.area ?? 0), 0).toFixed(1) ?? '—'}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">Total Area (ha)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-foreground">
              {farms?.filter((f) => f.location).length ?? '—'}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">With Location</p>
          </CardContent>
        </Card>
      </div>

      {/* Farms table */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">All Farms</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : isError ? (
            <div className="py-12 text-center text-sm text-destructive">
              Failed to load farms. Is the backend running?
            </div>
          ) : farms?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <Tractor className="mb-3 h-10 w-10 opacity-20" />
              <p className="font-medium">No farms yet</p>
              <p className="text-sm">Click "Add Farm" to register your first farm.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Farm Name</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Area</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {farms?.map((farm) => (
                  <TableRow key={farm.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{farm.name}</p>
                        <p className="text-xs text-muted-foreground">ID #{farm.id}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{farm.location ?? '—'}</TableCell>
                    <TableCell>{farm.area != null ? `${farm.area} ha` : '—'}</TableCell>
                    <TableCell>
                      <Badge variant="success">Active</Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDate(farm.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setEditFarm(farm)}
                          className="h-8 w-8"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteFarm(farm)}
                          className="h-8 w-8 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Register New Farm</DialogTitle>
            <DialogDescription>Add a new agricultural farm to the platform.</DialogDescription>
          </DialogHeader>
          <FarmForm mode="create" onSubmit={handleCreate} isPending={creating} onCancel={() => setCreateOpen(false)} />
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editFarm} onOpenChange={(v) => !v && setEditFarm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Farm</DialogTitle>
            <DialogDescription>Update details for {editFarm?.name}.</DialogDescription>
          </DialogHeader>
          {editFarm && (
            <FarmForm
              mode="edit"
              defaultValues={{
                name: editFarm.name,
                location: editFarm.location ?? '',
                area: editFarm.area != null ? String(editFarm.area) : '',
              }}
              onSubmit={handleEdit}
              isPending={updating}
              onCancel={() => setEditFarm(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirm */}
      <DeleteConfirmDialog
        farm={deleteFarm}
        open={!!deleteFarm}
        onClose={() => setDeleteFarm(null)}
      />
    </div>
  )
}
