import { useState } from 'react'
import { Radio, Inbox, CheckCircle2, AlertCircle, Layers } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { useEventCatalog, useOutboxEntries, useOutboxStats } from '@/api/events'
import { formatDateTime } from '@/lib/utils'
import type { OutboxEntryStatus } from '@/types'

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  loading,
}: {
  label: string
  value: number
  icon: React.ComponentType<{ className?: string }>
  color: string
  loading?: boolean
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            {loading ? (
              <Skeleton className="mt-2 h-8 w-16" />
            ) : (
              <p className="mt-1 text-3xl font-bold">{value}</p>
            )}
          </div>
          <div className={`rounded-lg p-3 ${color}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function Events() {
  const [outboxStatus, setOutboxStatus] = useState<OutboxEntryStatus>('pending')
  const catalog = useEventCatalog()
  const stats = useOutboxStats()
  const entries = useOutboxEntries(outboxStatus)

  return (
    <div className="space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Domain Events</h1>
        <p className="text-muted-foreground">
          Phase 14 event catalog, transactional outbox, and consumer processing ledger.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard
          label="Outbox pending"
          value={stats.data?.pending ?? 0}
          icon={Inbox}
          color="bg-amber-500"
          loading={stats.isLoading}
        />
        <StatCard
          label="Published"
          value={stats.data?.published ?? 0}
          icon={CheckCircle2}
          color="bg-emerald-600"
          loading={stats.isLoading}
        />
        <StatCard
          label="Relay failed"
          value={stats.data?.failed ?? 0}
          icon={AlertCircle}
          color="bg-red-600"
          loading={stats.isLoading}
        />
        <StatCard
          label="Outbox total"
          value={stats.data?.total ?? 0}
          icon={Layers}
          color="bg-slate-600"
          loading={stats.isLoading}
        />
        <StatCard
          label="Events processed"
          value={stats.data?.events_processed ?? 0}
          icon={Radio}
          color="bg-violet-600"
          loading={stats.isLoading}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Event catalog</CardTitle>
          <CardDescription>Registered domain event types and Redpanda topics</CardDescription>
        </CardHeader>
        <CardContent>
          {catalog.isLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Event type</TableHead>
                  <TableHead>Topic</TableHead>
                  <TableHead>Schema</TableHead>
                  <TableHead>Description</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(catalog.data?.events ?? []).map((row) => (
                  <TableRow key={row.event_type}>
                    <TableCell className="font-mono text-xs">{row.event_type}</TableCell>
                    <TableCell className="font-mono text-xs">{row.topic}</TableCell>
                    <TableCell>{row.schema_version}</TableCell>
                    <TableCell className="text-muted-foreground">{row.description}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Transactional outbox</CardTitle>
            <CardDescription>Rows awaiting relay or recently published</CardDescription>
          </div>
          <Select
            value={outboxStatus}
            onValueChange={(v) => setOutboxStatus(v as OutboxEntryStatus)}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="published">Published</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="all">All</SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent>
          {entries.isLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : entries.isError ? (
            <p className="text-sm text-destructive">{entries.error.message}</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Created</TableHead>
                  <TableHead>Event</TableHead>
                  <TableHead>Aggregate</TableHead>
                  <TableHead>Topic</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(entries.data?.entries ?? []).map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="text-xs">{formatDateTime(row.created_at)}</TableCell>
                    <TableCell className="font-mono text-xs">{row.event_type}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {row.aggregate_type}
                      <span className="block text-muted-foreground truncate max-w-[140px]">
                        {row.aggregate_id}
                      </span>
                    </TableCell>
                    <TableCell className="font-mono text-xs max-w-[200px] truncate">
                      {row.topic}
                    </TableCell>
                    <TableCell>
                      {row.published_at ? (
                        <Badge variant="success">Published</Badge>
                      ) : row.publish_attempts > 0 ? (
                        <Badge variant="destructive">Failed</Badge>
                      ) : (
                        <Badge variant="warning">Pending</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {(entries.data?.entries.length ?? 0) === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                      No outbox rows for this filter.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
