import React, { useState, useMemo } from "react"
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Product } from "@/types"
import { Sparkles, Info, Filter, Layers } from "lucide-react"
import { formatCategoryName } from "@/lib/categories"

interface OpportunityMatrixProps {
  products: Product[]
  onSelectProduct: (product: Product) => void
  isDark?: boolean
}

// Simple deterministic hash to provide stable jitter without layout shifts
function getDeterministicJitter(id: string, index: number): { xOffset: number; yOffset: number } {
  let hash = (index + 1) * 31
  for (let i = 0; i < id.length; i++) {
    hash = (hash * 33 + id.charCodeAt(i)) & 0x7fffffff
  }
  // yOffset between -2.2 and +2.2
  const yOffset = ((hash % 100) / 50 - 1) * 2.2
  // xOffset between -1.2 and +1.2
  const xOffset = (((hash >> 4) % 100) / 50 - 1) * 1.2
  return { xOffset, yOffset }
}

export const OpportunityMatrix: React.FC<OpportunityMatrixProps> = ({
  products,
  onSelectProduct,
  isDark = false,
}) => {
  const [selectedQuadrant, setSelectedQuadrant] = useState<string>("all")
  const [spreadPoints, setSpreadPoints] = useState<boolean>(true)

  const scatterData = useMemo(() => {
    return products.map((p, idx) => {
      const rawX = p.demand ?? 0
      const rawY = p.brand ?? 0
      const isBaselineBrand = Math.abs(rawY - 46.7) < 0.2

      let xDisplay = rawX
      let yDisplay = rawY

      if (spreadPoints) {
        const { xOffset, yOffset } = getDeterministicJitter(p.id, idx)
        // If it's the 46.7 baseline line, spread Y slightly to prevent solid overlapping horizontal line
        if (isBaselineBrand) {
          yDisplay = Math.max(5, Math.min(95, rawY + yOffset))
          xDisplay = Math.max(5, Math.min(95, rawX + xOffset))
        } else {
          // Subtle micro-spread to prevent exact point overlap
          xDisplay = Math.max(5, Math.min(95, rawX + xOffset * 0.4))
          yDisplay = Math.max(5, Math.min(95, rawY + yOffset * 0.4))
        }
      }

      return {
        ...p,
        x: Math.round(xDisplay * 10) / 10,
        y: Math.round(yDisplay * 10) / 10,
        rawX,
        rawY,
        z: p.combined ?? 50,
        isPriority: p.priority,
        categoryName: formatCategoryName(p.category),
      }
    })
  }, [products, spreadPoints])

  const filteredData = useMemo(() => {
    if (selectedQuadrant === "gold") {
      return scatterData.filter((d) => d.rawX >= 50 && d.rawY >= 50)
    }
    if (selectedQuadrant === "niche") {
      return scatterData.filter((d) => d.rawX < 50 && d.rawY >= 50)
    }
    if (selectedQuadrant === "volume") {
      return scatterData.filter((d) => d.rawX >= 50 && d.rawY < 50)
    }
    if (selectedQuadrant === "watch") {
      return scatterData.filter((d) => d.rawX < 50 && d.rawY < 50)
    }
    return scatterData
  }, [scatterData, selectedQuadrant])

  // Custom Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white/95 dark:bg-[#0c1410]/95 backdrop-blur-md p-3.5 rounded-xl border border-[#cbd8d1] dark:border-[#22362b] shadow-xl max-w-xs text-xs space-y-2 z-50 text-[#111916] dark:text-zinc-100">
          <div className="flex items-center justify-between gap-2 border-b border-gray-100 dark:border-[#1d2e26] pb-1.5">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-[#176449] dark:text-[#34d399] bg-[#e8f1ec] dark:bg-[#152e22] px-1.5 py-0.5 rounded text-[11px]">
                Rank #{data.rank ?? "?"}
              </span>
              <span className="text-[10px] text-gray-500 dark:text-zinc-400 font-medium">
                {data.categoryName}
              </span>
            </div>
            <span className="text-gray-400 dark:text-zinc-500 font-mono text-[10px]">{data.id}</span>
          </div>

          <p className="font-medium text-[#111916] dark:text-white line-clamp-2 leading-tight">
            {data.title}
          </p>

          <div className="grid grid-cols-2 gap-2 pt-1">
            <div className="bg-[#f0f4f2] dark:bg-[#13201a] p-2 rounded-lg border border-[#e2ede7] dark:border-[#1d2e26]">
              <div className="text-[10px] text-[#5a6e65] dark:text-[#8ea398]">Demanda</div>
              <div className="font-bold text-blue-700 dark:text-blue-400 text-sm">
                {data.rawX ?? data.demand ?? 0}
                <span className="text-[9px] text-[#5a6e65] dark:text-[#8ea398] font-normal"> ({data.demandCoverage ?? 0}%)</span>
              </div>
            </div>

            <div className="bg-[#f0f4f2] dark:bg-[#13201a] p-2 rounded-lg border border-[#e2ede7] dark:border-[#1d2e26]">
              <div className="text-[10px] text-[#5a6e65] dark:text-[#8ea398]">Potencial Marca</div>
              <div className="font-bold text-[#176449] dark:text-[#34d399] text-sm">
                {data.rawY ?? data.brand ?? 0}
                <span className="text-[9px] text-[#5a6e65] dark:text-[#8ea398] font-normal"> ({data.brandCoverage ?? 0}%)</span>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-gray-100 dark:border-[#1d2e26] text-[10px] text-[#5a6e65] dark:text-[#8ea398]">
            <span>
              Score Geral: <strong className="text-[#176449] dark:text-[#34d399] font-mono">{data.combined ?? 0}</strong>
            </span>
            <span className="text-[#176449] dark:text-[#34d399] font-medium">Ver detalhes →</span>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <Card className="border-[#dbe4df] dark:border-[#22362b] bg-white dark:bg-[#13201a] shadow-xs transition-colors">
      <CardHeader className="pb-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold text-[#111916] dark:text-white">
                Matriz Estratégica: Demanda × Potencial de Marca
              </CardTitle>
              <Badge className="bg-[#176449] dark:bg-[#152e22] text-white dark:text-[#34d399] text-[10px] border border-transparent dark:border-[#1f4232]">
                {filteredData.length} itens exibidos
              </Badge>
            </div>
            <CardDescription className="text-xs text-[#5a6e65] dark:text-[#8ea398] mt-0.5">
              Identifique produtos com alta demanda e espaço para posicionamento de marca própria.
            </CardDescription>
          </div>

          {/* Quick quadrant filter pills */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 text-xs">
            <button
              onClick={() => setSelectedQuadrant("all")}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                selectedQuadrant === "all"
                  ? "bg-[#176449] text-white"
                  : "bg-[#f0f4f2] dark:bg-[#0c1410] text-[#5a6e65] dark:text-[#8ea398] hover:bg-[#e2ede7] dark:hover:bg-[#1b2c23]"
              }`}
            >
              Todos ({scatterData.length})
            </button>
            <button
              onClick={() => setSelectedQuadrant("gold")}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                selectedQuadrant === "gold"
                  ? "bg-emerald-700 dark:bg-emerald-600 text-white"
                  : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 hover:bg-emerald-100 border border-emerald-200 dark:border-emerald-800/60"
              }`}
            >
              ★ Alta Demanda & Marca
            </button>
            <button
              onClick={() => setSelectedQuadrant("volume")}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                selectedQuadrant === "volume"
                  ? "bg-blue-700 dark:bg-blue-600 text-white"
                  : "bg-blue-50 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300 hover:bg-blue-100 border border-blue-200 dark:border-blue-800/60"
              }`}
            >
              Volume Puro
            </button>
            <button
              onClick={() => setSelectedQuadrant("niche")}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                selectedQuadrant === "niche"
                  ? "bg-teal-700 dark:bg-teal-600 text-white"
                  : "bg-teal-50 dark:bg-teal-950/40 text-teal-800 dark:text-teal-300 hover:bg-teal-100 border border-teal-200 dark:border-teal-800/60"
              }`}
            >
              Nicho Marca
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-2">
        {/* Visual guide header */}
        <div className="grid grid-cols-2 text-[11px] mb-2 px-4 py-1.5 bg-[#f8faf9] dark:bg-[#0c1410] rounded-lg border border-[#e2ede7] dark:border-[#1d2e26] text-[#5a6e65] dark:text-[#8ea398]">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-teal-500" />
            <span>Nicho de Marca (Alta Marca / Demanda Emergente)</span>
          </div>
          <div className="flex items-center justify-end gap-1.5 font-medium text-[#176449] dark:text-[#34d399]">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Quadrante de Ouro: Alta Demanda & Alto Potencial de Marca</span>
          </div>
        </div>

        {/* Chart Area */}
        <div className="w-full h-[360px]">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart
              margin={{ top: 20, right: 30, bottom: 25, left: 10 }}
              onClick={(e: any) => {
                if (e && e.activePayload && e.activePayload[0]) {
                  onSelectProduct(e.activePayload[0].payload)
                }
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#1d2e26" : "#e2e8f0"} />
              <XAxis
                type="number"
                dataKey="x"
                name="Demanda"
                unit=""
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: isDark ? "#8ea398" : "#5a6e65" }}
                axisLine={{ stroke: isDark ? "#22362b" : "#cbd8d1" }}
                label={{
                  value: "Demanda (0 - 100) →",
                  position: "insideBottom",
                  offset: -12,
                  fontSize: 11,
                  fill: isDark ? "#34d399" : "#14523d",
                  fontWeight: 600,
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Potencial de Marca"
                unit=""
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: isDark ? "#8ea398" : "#5a6e65" }}
                axisLine={{ stroke: isDark ? "#22362b" : "#cbd8d1" }}
                label={{
                  value: "Potencial de Marca (0 - 100) →",
                  angle: -90,
                  position: "insideLeft",
                  offset: 5,
                  fontSize: 11,
                  fill: isDark ? "#34d399" : "#14523d",
                  fontWeight: 600,
                }}
              />
              <Tooltip content={<CustomTooltip />} />

              {/* Threshold lines at 50/50 */}
              <ReferenceLine x={50} stroke={isDark ? "#244033" : "#94a3b8"} strokeDasharray="4 4" />
              <ReferenceLine y={50} stroke={isDark ? "#244033" : "#94a3b8"} strokeDasharray="4 4" />

              <Scatter
                name="Produtos"
                data={filteredData}
                cursor="pointer"
              >
                {filteredData.map((entry, index) => {
                  let fillColor = isDark ? "#64748b" : "#64748b"
                  if (entry.rawX >= 50 && entry.rawY >= 50) {
                    fillColor = isDark ? "#10b981" : "#176449" // Gold quadrant: Emerald
                  } else if (entry.rawX >= 50) {
                    fillColor = isDark ? "#38bdf8" : "#2563eb" // High demand, low brand: Blue
                  } else if (entry.rawY >= 50) {
                    fillColor = isDark ? "#2dd4bf" : "#0d9488" // Low demand, high brand: Teal
                  }

                  return (
                    <Cell
                      key={`cell-${index}`}
                      fill={fillColor}
                      fillOpacity={0.82}
                      stroke={entry.priority ? (isDark ? "#34d399" : "#059669") : (isDark ? "#0c1410" : "#ffffff")}
                      strokeWidth={entry.priority ? 2.5 : 1}
                      r={entry.priority ? 7.5 : Math.max(4.5, Math.min(8.5, (entry.z / 100) * 8.5))}
                      className="transition-transform hover:scale-130 cursor-pointer"
                      onClick={() => onSelectProduct(entry)}
                    />
                  )
                })}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Legend footer with smart dispersion notice */}
        <div className="flex flex-wrap items-center justify-between text-[11px] text-[#5a6e65] dark:text-[#8ea398] mt-2 pt-2 border-t border-gray-100 dark:border-[#1d2e26]">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#176449] dark:bg-[#10b981]" /> Alta Demanda & Marca (Prioridade)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600 dark:bg-sky-400" /> Volume / Commodities
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-teal-600 dark:bg-teal-400" /> Nicho Diferenciável
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500" /> Investigação
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-gray-400 dark:text-zinc-500">
              ✨ Dispersão orgânica ativa para visualização de pontos sobrepostos
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
