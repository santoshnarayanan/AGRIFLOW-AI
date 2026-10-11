import { useMemo, useState } from 'react'
import { Database, Sparkles, History } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { useFields } from '@/api/fields'
import {
  useFeatureCatalog,
  useFieldFeatureSnapshots,
  useMaterializeFieldFeatures,
} from '@/api/features'
import { formatDateTime } from '@/lib/utils'

export function FeatureStore() {
  const { data: fields = [], isLoading: fieldsLoading } = useFields()
  const [fieldId, setFieldId] = useState<string | null>(null)
  const catalog = useFeatureCatalog()
  const snapshots = useFieldFeatureSnapshots(fieldId)
  const materialize = useMaterializeFieldFeatures()

  const selectedField = useMemo(
    () => fields.find((f) => f.id === fieldId) ?? null,
    [fields, fieldId],
  )

  const latestSnapshot = snapshots.data?.snapshots[0] ?? null

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">AI Feature Store</h2>
        <p className="text-muted-foreground">
          CDD feature registry, field snapshots from continuous aggregates, and operator materialise.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Registry</CardTitle>
          </CardHeader>
          <CardContent>
            {catalog.isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <p className="text-2xl font-bold">{catalog.data?.registry_version}</p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">
              {catalog.data?.count ?? 0} features registered
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Selected field</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold truncate">
              {selectedField?.name ?? '—'}
            </p>
            <p className="text-xs text-muted-foreground">
              {fieldId ? `${fieldId.slice(0, 8)}…` : 'Choose a field to inspect snapshots'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Latest snapshot</CardTitle>
          </CardHeader>
          <CardContent>
            {snapshots.isLoading && fieldId ? (
              <Skeleton className="h-8 w-full" />
            ) : latestSnapshot ? (
              <p className="text-sm font-medium">{formatDateTime(latestSnapshot.as_of)}</p>
            ) : (
              <p className="text-sm text-muted-foreground">None materialised yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Materialise snapshot
          </CardTitle>
          <CardDescription>
            Requires operator JWT or development bypass. Event-driven projection also refreshes on
            domain events when enabled.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1 space-y-2">
            <label className="text-sm font-medium">Field</label>
            {fieldsLoading ? (
              <Skeleton className="h-10 w-full" />
            ) : (
              <Select
                value={fieldId ?? ''}
                onValueChange={(v) => setFieldId(v || null)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select field" />
                </SelectTrigger>
                <SelectContent>
                  {fields.map((f) => (
                    <SelectItem key={f.id} value={f.id}>
                      {f.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
          <Button
            disabled={!fieldId || materialize.isPending}
            onClick={() => fieldId && materialize.mutate(fieldId)}
          >
            <Database className="mr-2 h-4 w-4" />
            {materialize.isPending ? 'Materialising…' : 'Materialise now'}
          </Button>
        </CardContent>
        {materialize.isError && (
          <p className="px-6 pb-4 text-sm text-destructive">
            {materialize.error instanceof Error ? materialize.error.message : 'Materialise failed'}
          </p>
        )}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Feature catalog</CardTitle>
          <CardDescription>Governed features and continuous aggregate sources</CardDescription>
        </CardHeader>
        <CardContent>
          {catalog.isLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Feature</TableHead>
                  <TableHead>Unit</TableHead>
                  <TableHead>Window</TableHead>
                  <TableHead>Primary source</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {catalog.data?.features.map((f) => (
                  <TableRow key={f.feature_id}>
                    <TableCell>
                      <div className="font-medium">{f.display_name}</div>
                      <div className="text-xs text-muted-foreground">{f.feature_id}</div>
                    </TableCell>
                    <TableCell>{f.unit}</TableCell>
                    <TableCell>{f.window_days}d</TableCell>
                    <TableCell className="text-xs font-mono">{f.primary_source}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {fieldId && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Snapshot history
            </CardTitle>
          </CardHeader>
          <CardContent>
            {snapshots.isLoading ? (
              <Skeleton className="h-32 w-full" />
            ) : snapshots.data && snapshots.data.count > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>As of</TableHead>
                    <TableHead>Registry</TableHead>
                    <TableHead>Features</TableHead>
                    <TableHead>Notes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {snapshots.data.snapshots.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell>{formatDateTime(s.as_of)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{s.registry_version}</Badge>
                      </TableCell>
                      <TableCell>{Object.keys(s.features ?? {}).length}</TableCell>
                      <TableCell className="max-w-xs truncate text-xs text-muted-foreground">
                        {s.materialization_notes ?? '—'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-sm text-muted-foreground">No snapshots for this field.</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
