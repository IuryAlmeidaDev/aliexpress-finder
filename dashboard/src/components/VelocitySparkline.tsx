import React from "react"
import { LineChart, Line, ResponsiveContainer } from "recharts"

interface Props {
  data: number[]
  color?: string
  width?: number
  height?: number
}

export const VelocitySparkline: React.FC<Props> = ({
  data, color = "#176449", width = 100, height = 32
}) => {
  if (!data || data.length === 0) return <span className="text-xs text-gray-400">—</span>
  const points = data.map((value, i) => ({ i, value }))
  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points}>
          <Line type="monotone" dataKey="value" stroke={color}
                strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
