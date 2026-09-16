import React, { useMemo } from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Product } from "@/types"

interface CategoryChartProps {
  products: Product[]
  selectedCategory: string
  onSelectCategory: (cat: string) => void
}

export const CategoryChart: React.FC<CategoryChartProps> = ({
  products,
  selectedCategory,
  onSelectCategory,
}) => {
  const categoryStats = useMemo(() => {
    const map = new Map<string, { count: number; totalDemand: number; totalBrand: number }>()

    products.forEach((p) => {
      const cat = p.category || "Geral"
      const existing = map.get(cat) || { count: 0, totalDemand: 0, totalBrand: 0 }
      existing.count++
      existing.totalDemand += p.demand ?? 0
      existing.totalBrand += p.brand ?? 0
      map.set(cat, existing)
    })

    return Array.from(map.entries())
      .map(([cat, stats]) => ({
        category: cat,
        count: stats.count,
        avgDemand: Math.round((stats.totalDemand / stats.count) * 10) / 10,
        avgBrand: Math.round((stats.totalBrand / stats.count) * 10) / 10,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8)
  }, [products])

  return (
    <Card className="border-[#dbe4df] bg-white shadow-xs">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-bold text-[#111916]">
              Volume por Categoria
            </CardTitle>
            <CardDescription className="text-xs text-[#5a6e65] mt-0.5">
              Categorias mais presentes no ranking dos 100 mais vendidos.
            </CardDescription>
          </div>
          {selectedCategory && (
            <button
              onClick={() => onSelectCategory("")}
              className="text-xs text-[#176449] hover:underline font-medium"
            >
              Limpar filtro
            </button>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="w-full h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={categoryStats}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#5a6e65" }} />
              <YAxis
                type="category"
                dataKey="category"
                width={80}
                tick={{ fontSize: 11, fill: "#111916", fontWeight: 500 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  borderColor: "#cbd8d1",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                formatter={(val: any, name: any) => {
                  if (name === "count") return [`${val} produtos`, "Itens no ranking"]
                  return [val, name]
                }}
              />
              <Bar
                dataKey="count"
                name="count"
                cursor="pointer"
                onClick={(data: any) => onSelectCategory(data.category)}
                radius={[0, 4, 4, 0]}
              >
                {categoryStats.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={selectedCategory === entry.category ? "#176449" : "#3b82f6"}
                    className="hover:opacity-80 transition-opacity"
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="text-[11px] text-center text-gray-400 mt-1">
          Dica: clique em uma barra para filtrar os produtos daquela categoria
        </div>
      </CardContent>
    </Card>
  )
}
