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
import { formatCategoryName } from "@/lib/categories"

interface CategoryChartProps {
  products: Product[]
  selectedCategory: string
  onSelectCategory: (cat: string) => void
  isDark?: boolean
}

export const CategoryChart: React.FC<CategoryChartProps> = ({
  products,
  selectedCategory,
  onSelectCategory,
  isDark = false,
}) => {
  const categoryStats = useMemo(() => {
    const map = new Map<string, { count: number; totalDemand: number; totalBrand: number }>()

    products.forEach((p) => {
      const cat = formatCategoryName(p.category)
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
    <Card className="border-[#dbe4df] dark:border-[#22362b] bg-white dark:bg-[#13201a] shadow-xs transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-bold text-[#111916] dark:text-white">
              Volume por Categoria
            </CardTitle>
            <CardDescription className="text-xs text-[#5a6e65] dark:text-[#8ea398] mt-0.5">
              Categorias mais frequentes no ranking dos 100 mais vendidos.
            </CardDescription>
          </div>
          {selectedCategory && (
            <button
              onClick={() => onSelectCategory("")}
              className="text-xs text-[#176449] dark:text-[#34d399] hover:underline font-medium"
            >
              Limpar filtro
            </button>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="w-full h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={categoryStats}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={isDark ? "#1d2e26" : "#e2e8f0"}
                horizontal={false}
              />
              <XAxis
                type="number"
                tick={{ fontSize: 11, fill: isDark ? "#8ea398" : "#5a6e65" }}
                axisLine={{ stroke: isDark ? "#22362b" : "#cbd8d1" }}
              />
              <YAxis
                type="category"
                dataKey="category"
                width={145}
                tick={{ fontSize: 11, fill: isDark ? "#e2e8f0" : "#111916", fontWeight: 500 }}
                axisLine={{ stroke: isDark ? "#22362b" : "#cbd8d1" }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? "#0c1410" : "#ffffff",
                  borderColor: isDark ? "#22362b" : "#cbd8d1",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: isDark ? "#f1f5f9" : "#111916",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
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
                {categoryStats.map((entry, index) => {
                  const isSelected = selectedCategory === entry.category
                  const fill = isSelected
                    ? isDark
                      ? "#34d399"
                      : "#176449"
                    : isDark
                    ? "#0284c7"
                    : "#3b82f6"

                  return (
                    <Cell
                      key={`cell-${index}`}
                      fill={fill}
                      className="hover:opacity-85 transition-opacity"
                    />
                  )
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="text-[11px] text-center text-gray-400 dark:text-zinc-500 mt-1">
          Dica: clique em uma barra para filtrar os produtos daquela categoria
        </div>
      </CardContent>
    </Card>
  )
}
