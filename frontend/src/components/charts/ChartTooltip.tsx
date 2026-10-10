type TooltipEntry = {
  dataKey?: string | number
  name?: string
  value?: number | string
  color?: string
}

export function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: TooltipEntry[]
  label?: string | number
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border bg-card p-3 shadow-lg text-sm">
      <p className="mb-2 text-xs font-medium text-muted-foreground">{label}</p>
      {payload.map((p) =>
        p.value ? (
          <p key={String(p.dataKey)} className="font-medium" style={{ color: p.color }}>
            {p.name}: {p.value}
          </p>
        ) : null,
      )}
    </div>
  )
}
