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
import { Sparkles, Info, Filter } from "lucide-react"

interface OpportunityMatrixProps {
  products: Product[]
  onSelectProduct: (product: Product) => void
}

export const OpportunityMatrix: React.FC<OpportunityMatrixProps> = ({
  products,
  onSelectProduct,
}) => {
  const [selectedQuadrant, setSelectedQuadrant] = useState<string>("all")

  const scatterData = useMemo(() => {
    return products.map((p) => ({
      ...p,
      x: p.demand ?? 0,
      y: p.brand ?? 0,
      z: p.combined ?? 50,
      isPriority: p.priority,
    }))
  }, [products])

  const filteredData = useMemo(() => {
    if (selectedQuadrant === "gold") {
      return scatterData.filter((d) => d.x >= 50 && d.y >= 50)
    }
    if (selectedQuadrant === "niche") {
      return scatterData.filter((d) => d.x < 50 && d.y >= 50)
    }
    if (selectedQuadrant === "volume") {
      return scatterData.filter((d) => d.x >= 50 && d.y < 50)
    }
    if (selectedQuadrant === "watch") {
      return scatterData.filter((d) => d.x < 50 && d.y < 50)
    }
    return scatterData
  }, [scatterData, selectedQuadrant])

  // Custom Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as Product
      return (
        <div className="bg-white/95 backdrop-blur-md p-3 rounded-lg border border-[#cbd8d1] shadow-lg max-w-xs text-xs space-y-1.5 z-50">
          <div className="flex items-center justify-between gap-2 border-b border-gray-100 pb-1.5">
            <span className="font-bold text-[#176449] bg-emerald-50 px-1.5 py-0.5 rounded text-[11px]">
              Rank #{data.rank ?? "?"}
            </span>
            <span className="text-gray-500 font-mono text-[10px]">{data.id}</span>
          </div>

          <p className="font-medium text-[#111916] line-clamp-2 leading-tight">
            {data.title}
          </p>

          <div className="grid grid-cols-2 gap-2 pt-1">
            <div className="bg-[#f0f4f2] p-1.5 rounded">
              <div className="text-[10px] text-[#5a6e65]">Demanda</div>
              <div className="font-bold text-blue-800">
                {data.demand ?? 0}
                <span className="text-[9px] text-[#5a6e65] font-normal"> ({data.demandCoverage ?? 0}%)</span>
              </div>
            </div>

            <div className="bg-[#f0f4f2] p-1.5 rounded">
              <div className="text-[10px] text-[#5a6e65]">Potencial Marca</div>
              <div className="font-bold text-[#176449]">
                {data.brand ?? 0}
                <span className="text-[9px] text-[#5a6e65] font-normal"> ({data.brandCoverage ?? 0}%)</span>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-gray-100 text-[10px] text-[#5a6e65]">
            <span>Score: <strong className="text-purple-700">{data.combined ?? 0}</strong></span>
            <span className="text-[#176449] font-medium">Clique para abrir ficha →</span>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <Card className="border-[#dbe4df] bg-white shadow-xs">
      <CardHeader className="pb-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold text-[#111916]">
                Matriz Estratégica: Demanda × Potencial de Marca
              </CardTitle>
              <Badge className="bg-[#176449] text-white text-[10px]">
                {filteredData.length} itens exibidos
              </Badge>
            </div>
            <CardDescription className="text-xs text-[#5a6e65] mt-0.5">
              Identifique produtos com alta demanda e espaço para posicionamento de marca própria.
            </CardDescription>
          </div>

          {/* Quadrant quick filters */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 text-xs">
            <button
              onClick={() => setSelectedQuadrant("all")}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                selectedQuadrant === "all"
                  ? "bg-[#176449] text-white"
                  : "bg-[#f0f4f2] text-[#5a6e65] hover:bg-[#e2ede7]"
              }`}
            >
              Todos ({scatterData.length})
            </button>
            <button
              onClick={() => setSelectedQuadrant("gold")}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                selectedQuadrant === "gold"
                  ? "bg-emerald-700 text-white"
                  : "bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200"
              }`}
            >
              ★ Alta Demanda & Marca
            </button>
            <button
              onClick={() => setSelectedQuadrant("volume")}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                selectedQuadrant === "volume"
                  ? "bg-blue-700 text-white"
                  : "bg-blue-50 text-blue-800 hover:bg-blue-100 border border-blue-200"
              }`}
            >
              Volume Puro
            </button>
            <button
              onClick={() => setSelectedQuadrant("niche")}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                selectedQuadrant === "niche"
                  ? "bg-purple-700 text-white"
                  : "bg-purple-50 text-purple-800 hover:bg-purple-100 border border-purple-200"
              }`}
            >
              Nicho Marca
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-2">
        {/* Visual guide header */}
        <div className="grid grid-cols-2 text-[11px] mb-2 px-6 py-1.5 bg-[#f8faf9] rounded-lg border border-[#e2ede7] text-[#5a6e65]">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-500" />
            <span>Nicho de Diferenciação (Alta Marca / Baixo Volume)</span>
          </div>
          <div className="flex items-center justify-end gap-1.5 font-medium text-[#176449]">
            <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
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
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                type="number"
                dataKey="x"
                name="Demanda"
                unit=""
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: "#5a6e65" }}
                label={{
                  value: "Demanda (0 - 100) →",
                  position: "insideBottom",
                  offset: -12,
                  fontSize: 11,
                  fill: "#14523d",
                  fontWeight: 600,
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Potencial de Marca"
                unit=""
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: "#5a6e65" }}
                label={{
                  value: "Potencial de Marca (0 - 100) →",
                  angle: -90,
                  position: "insideLeft",
                  offset: 5,
                  fontSize: 11,
                  fill: "#14523d",
                  fontWeight: 600,
                }}
              />
              <Tooltip content={<CustomTooltip />} />

              {/* Threshold lines at 50/50 */}
              <ReferenceLine x={50} stroke="#94a3b8" strokeDasharray="4 4" />
              <ReferenceLine y={50} stroke="#94a3b8" strokeDasharray="4 4" />

              <Scatter
                name="Produtos"
                data={filteredData}
                cursor="pointer"
              >
                {filteredData.map((entry, index) => {
                  let fillColor = "#64748b" // default gray
                  if (entry.x >= 50 && entry.y >= 50) {
                    fillColor = "#176449" // Gold quadrant: Emerald
                  } else if (entry.x >= 50) {
                    fillColor = "#2563eb" // High demand, low brand: Blue
                  } else if (entry.y >= 50) {
                    fillColor = "#9333ea" // Low demand, high brand: Purple
                  }

                  return (
                    <Cell
                      key={`cell-${index}`}
                      fill={fillColor}
                      fillOpacity={0.8}
                      stroke={entry.priority ? "#059669" : "#ffffff"}
                      strokeWidth={entry.priority ? 2 : 1}
                      r={entry.priority ? 7 : Math.max(4, Math.min(8, (entry.z / 100) * 8))}
                      className="transition-transform hover:scale-125"
                    />
                  )
                })}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Legend footer */}
        <div className="flex flex-wrap items-center justify-between text-[11px] text-[#5a6e65] mt-2 pt-2 border-t border-gray-100">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#176449]" /> Alta Demanda & Marca (Prioridade)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600" /> Volume / Commodities
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-600" /> Nicho Diferenciável
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500" /> Investigação
            </span>
          </div>
          <span className="italic text-gray-400">Clique em qualquer ponto do gráfico para inspecionar</span>
        </div>
      </CardContent>
    </Card>
  )
}
