import React from "react"

interface Props {
  data: number[]
  color?: string
  width?: number
  height?: number
}

export const VelocitySparkline: React.FC<Props> = ({
  data,
  color = "#176449",
  width = 90,
  height = 24,
}) => {
  if (!data || data.length === 0) {
    return <span className="text-xs text-[#5a6e65]">—</span>
  }

  if (data.length === 1) {
    return (
      <svg width={width} height={height} className="overflow-visible shrink-0">
        <line
          x1={0}
          y1={height / 2}
          x2={width}
          y2={height / 2}
          stroke={color}
          strokeWidth="1.5"
          strokeDasharray="2 2"
        />
      </svg>
    )
  }

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const padding = 2
  const effectiveHeight = height - padding * 2

  const points = data
    .map((val, idx) => {
      const x = (idx / (data.length - 1)) * width
      const y = height - padding - ((val - min) / range) * effectiveHeight
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(" ")

  return (
    <svg
      width={width}
      height={height}
      className="overflow-visible shrink-0"
      aria-hidden="true"
    >
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  )
}
