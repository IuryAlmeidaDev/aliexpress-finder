import React, { useMemo } from "react"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RunReport, Product } from "@/types"
import { Calendar, TrendingUp, Clock, AlertCircle } from "lucide-react"

interface TrendChartProps {
  runs: RunReport[]
  currentProducts: Product[]
  isDark?: boolean
}

export const TrendChart: React.FC<TrendChartProps> = ({ runs, currentProducts, isDark = false }) => {
  // If multiple runs exist, calculate historical trend
  const hasMultipleRuns = runs.length > 1

  const trendData = useMemo(() => {
    return runs.map((run, idx) => {
      const prods = run.products
      const total = prods.length
      const avgDemand = total
        ? Math.round((prods.reduce((acc, p) => acc + (p.demand ?? 0), 0) / total) * 10) / 10
        : 0
      const avgBrand = total
        ? Math.round((prods.reduce((acc, p) => acc + (p.brand ?? 0), 0) / total) * 10) / 10
        : 0
      const opportunities = prods.filter((p) => p.priority).length

      const d = new Date(run.date)
      const dateLabel = d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })

      return {
        name: `Coleta #${idx + 1} (${dateLabel})`,
        date: dateLabel,
        avgDemand,
        avgBrand,
        opportunities,
        total,
      }
    })
  }, [runs])

  // If only 1 run, show score distribution histogram
  const distributionData = useMemo(() => {
    const buckets = [
      { range: "0 - 20", demand: 0, brand: 0, combined: 0 },
      { range: "21 - 40", demand: 0, brand: 0, combined: 0 },
      { range: "41 - 60", demand: 0, brand: 0, combined: 0 },
      { range: "61 - 80", demand: 0, brand: 0, combined: 0 },
      { range: "81 - 100", demand: 0, brand: 0, combined: 0 },
    ]

    currentProducts.forEach((p) => {
      const d = p.demand ?? 0
      const b = p.brand ?? 0
      const c = p.combined ?? 0

      const getIdx = (v: number) => {
        if (v <= 20) return 0
        if (v <= 40) return 1
        if (v <= 60) return 2
        if (v <= 80) return 3
        return 4
      }

      buckets[getIdx(d)].demand++
      buckets[getIdx(b)].brand++
      buckets[getIdx(c)].combined++
    })

    return buckets
  }, [currentProducts])

  return (
    <Card className="border-[#dbe4df] dark:border-[#22362b] bg-white dark:bg-[#13201a] shadow-xs transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold text-[#111916] dark:text-white">
                {hasMultipleRuns ? "Evolução Histórica das Coletas" : "Distribuição dos Scores de Mercado"}
              </CardTitle>
              <Badge variant="outline" className="text-xs bg-[#e8f1ec] dark:bg-[#152e22] text-[#14523d] dark:text-[#34d399] border-[#cbd8d1] dark:border-[#1f4232]">
                {hasMultipleRuns ? `${runs.length} Pontos no Tempo` : "Linha de Base"}
              </Badge>
            </div>
            <CardDescription className="text-xs text-[#5a6e65] dark:text-[#8ea398] mt-0.5">
              {hasMultipleRuns
                ? "Acompanhamento da demanda média, potencial de marca e promoções ao longo das semanas."
                : "Concentração das notas de demanda, potencial de marca e score combinado na coleta atual."}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {hasMultipleRuns ? (
          <div className="w-full h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 15, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#1d2e26" : "#e2e8f0"} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: isDark ? "#8ea398" : "#5a6e65" }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: isDark ? "#8ea398" : "#5a6e65" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: isDark ? "#0c1410" : "#ffffff",
                    borderColor: isDark ? "#22362b" : "#cbd8d1",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: isDark ? "#f1f5f9" : "#111916",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
                <Line
                  type="monotone"
                  dataKey="avgDemand"
                  name="Demanda Média"
                  stroke={isDark ? "#38bdf8" : "#2563eb"}
                  strokeWidth={2.5}
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="avgBrand"
                  name="Potencial Marca Médio"
                  stroke={isDark ? "#34d399" : "#176449"}
                  strokeWidth={2.5}
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="opportunities"
                  name="Oportunidades Promovidas"
                  stroke={isDark ? "#10b981" : "#059669"}
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div>
            <div className="mb-3 p-3 bg-[#f8faf9] dark:bg-[#0c1410] rounded-lg border border-[#e2ede7] dark:border-[#1d2e26] flex items-start gap-2 text-xs text-[#5a6e65] dark:text-[#8ea398]">
              <Clock className="w-4 h-4 text-[#176449] dark:text-[#10b981] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#111916] dark:text-zinc-200">Linha de Base Estabelecida: </span>
                Esta é a 1ª coleta realizada pelo Radar. Conforme as coletas automáticas semanais
                (toda segunda-feira às 07:07) ou novas planilhas forem adicionadas, este gráfico exibirá
                a evolução contínua da demanda e a promoção de novas oportunidades.
              </div>
            </div>

            <div className="w-full h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distributionData} margin={{ top: 15, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#1d2e26" : "#e2e8f0"} />
                  <XAxis dataKey="range" tick={{ fontSize: 11, fill: isDark ? "#8ea398" : "#5a6e65" }} />
                  <YAxis tick={{ fontSize: 11, fill: isDark ? "#8ea398" : "#5a6e65" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: isDark ? "#0c1410" : "#ffffff",
                      borderColor: isDark ? "#22362b" : "#cbd8d1",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: isDark ? "#f1f5f9" : "#111916",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "5px" }} />
                  <Bar
                    dataKey="demand"
                    name="Demanda (Itens)"
                    fill={isDark ? "#38bdf8" : "#3b82f6"}
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    dataKey="brand"
                    name="Potencial Marca (Itens)"
                    fill={isDark ? "#10b981" : "#176449"}
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    dataKey="combined"
                    name="Score Combinado (Itens)"
                    fill={isDark ? "#a855f7" : "#8b5cf6"}
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
