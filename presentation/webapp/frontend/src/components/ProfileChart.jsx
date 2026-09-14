import { CartesianGrid, Line, LineChart, ReferenceDot, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from 'recharts'

// Renders one or two profiles as a line chart. The y-axis auto-scales to
// the actual min/max of the data shown (plus a little padding), rather
// than a fixed [0, 1] — the profiles usually only vary within a narrow
// band, and a fixed axis flattened that variation into a barely-visible
// squiggle.
// `series`: [{ data: number[], peaks?: number[], color, name }]
// `levelLine`: if given, draws a dashed reference line at that y value —
// used for the "peak sensitivity" sliders, which only move this line
// (no recompute) until the user re-runs the comparison. Included in the
// auto-scaled range so the line is never scaled off the chart.
export default function ProfileChart({ series, levelLine, levelLineColor = '#2f9e44', height = 140 }) {
  const length = Math.max(...series.map((s) => s.data.length), 1)
  const points = Array.from({ length }, (_, i) => {
    const row = { i }
    series.forEach((s, idx) => {
      row[`v${idx}`] = s.data[i] ?? null
    })
    return row
  })

  const values = series.flatMap((s) => s.data).filter((v) => v != null)
  if (typeof levelLine === 'number') values.push(levelLine)
  const dataMin = values.length ? Math.min(...values) : 0
  const dataMax = values.length ? Math.max(...values) : 1
  const pad = Math.max((dataMax - dataMin) * 0.12, 0.01)
  const domain = [dataMin - pad, dataMax + pad]

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={points} margin={{ top: 6, right: 10, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eae7df" />
        <XAxis dataKey="i" tick={false} axisLine={{ stroke: '#e4e1da' }} />
        <YAxis
          tick={{ fontSize: 10, fill: '#6b6860' }}
          width={40}
          domain={domain}
          tickFormatter={(v) => v.toFixed(2)}
        />
        {typeof levelLine === 'number' && (
          <ReferenceLine y={levelLine} stroke={levelLineColor} strokeDasharray="5 4" strokeWidth={1.5} />
        )}
        {series.map((s, idx) => (
          <Line
            key={idx}
            type="monotone"
            dataKey={`v${idx}`}
            stroke={s.color}
            dot={false}
            strokeWidth={1.6}
            isAnimationActive={false}
            name={s.name}
          />
        ))}
        {series.flatMap((s, idx) =>
          (s.peaks || []).map((p, j) => (
            <ReferenceDot
              key={`${idx}-${j}`}
              x={p}
              y={s.data[p] ?? 0}
              r={2.5}
              fill={s.color}
              stroke="none"
              isFront
            />
          )),
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}
