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
}

export const TrendChart: React.FC<TrendChartProps> = ({ runs, currentProducts }) => {
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
    <Card className="border-[#dbe4df] bg-white shadow-xs">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold text-[#111916]">
                {hasMultipleRuns ? "Evolução Histórica das Coletas" : "Distribuição dos Scores de Mercado"}
              </CardTitle>
              <Badge variant="outline" className="text-xs bg-[#e8f1ec] text-[#14523d] border-[#cbd8d1]">
                {hasMultipleRuns ? `${runs.length} Pontos no Tempo` : "Linha de Base"}
              </Badge>
            </div>
            <CardDescription className="text-xs text-[#5a6e65] mt-0.5">
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
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#5a6e65" }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#5a6e65" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderColor: "#cbd8d1",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
                <Line
                  type="monotone"
                  dataKey="avgDemand"
                  name="Demanda Média"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="avgBrand"
                  name="Potencial Marca Médio"
                  stroke="#176449"
                  strokeWidth={2.5}
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="opportunities"
                  name="Oportunidades Promovidas"
                  stroke="#059669"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div>
            <div className="mb-3 p-3 bg-[#f8faf9] rounded-lg border border-[#e2ede7] flex items-start gap-2 text-xs text-[#5a6e65]">
              <Clock className="w-4 h-4 text-[#176449] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#111916]">Linha de Base Estabelecida: </span>
                Esta é a 1ª coleta realizada pelo Radar. Conforme as coletas automáticas semanais
                (toda segunda-feira às 07:07) ou novas planilhas forem adicionadas, este gráfico exibirá
                a evolução contínua da demanda e a promoção de novas oportunidades.
              </div>
            </div>

            <div className="w-full h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distributionData} margin={{ top: 15, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="range" tick={{ fontSize: 11, fill: "#5a6e65" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#5a6e65" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderColor: "#cbd8d1",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "5px" }} />
                  <Bar dataKey="demand" name="Demanda (Itens)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="brand" name="Potencial Marca (Itens)" fill="#176449" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="combined" name="Score Combinado (Itens)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
