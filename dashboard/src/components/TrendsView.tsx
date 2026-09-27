import React, { useState, useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendFilters } from "@/components/TrendFilters"
import { VelocitySparkline } from "@/components/VelocitySparkline"
import { TrendOpportunity } from "@/types"
import { TrendingUp, Target, Flame, BarChart2, ExternalLink, ChevronDown, ChevronUp } from "lucide-react"

interface Props {
  items: TrendOpportunity[]
}

const STRATEGY_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  OCEANO_AZUL: { label: "Oceano Azul", color: "bg-emerald-100 text-emerald-800", icon: "🔥" },
  TENDENCIA: { label: "Tendência", color: "bg-blue-100 text-blue-800", icon: "🚀" },
  EMERGENTE: { label: "Emergente", color: "bg-amber-100 text-amber-800", icon: "📈" },
  SATURADO: { label: "Saturado", color: "bg-red-100 text-red-800", icon: "⚠️" },
  PENDENTE: { label: "Pendente", color: "bg-gray-100 text-gray-600", icon: "⏳" },
}

export const TrendsView: React.FC<Props> = ({ items }) => {
  const [strategyFilter, setStrategyFilter] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const categories = useMemo(() =>
    [...new Set(items.map((i) => i.category))].sort(), [items])

  const counts = useMemo(() => {
    const c: Record<string, number> = { "": items.length }
    for (const item of items) {
      c[item.strategy] = (c[item.strategy] || 0) + 1
    }
    return c
  }, [items])

  const filtered = useMemo(() => {
    let result = items
    if (strategyFilter) result = result.filter((i) => i.strategy === strategyFilter)
    if (categoryFilter) result = result.filter((i) => i.category === categoryFilter)
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter((i) =>
        i.title.toLowerCase().includes(q) ||
        (i.supplier_name || "").toLowerCase().includes(q) ||
        (i.ml_query || "").toLowerCase().includes(q)
      )
    }
    return result
  }, [items, strategyFilter, categoryFilter, searchQuery])

  const oceanCount = items.filter((i) => i.strategy === "OCEANO_AZUL").length
  const trendCount = items.filter((i) => i.strategy === "TENDENCIA").length
  const topAccel = items.length > 0
    ? items.reduce((a, b) => a.sales_velocity_7d > b.sales_velocity_7d ? a : b)
    : null

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-xs text-[#6b8a7a]">
              <BarChart2 className="h-4 w-4" /> Monitorados
            </div>
            <p className="mt-1 text-2xl font-bold text-[#111916]">{items.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-xs text-emerald-600">
              <Flame className="h-4 w-4" /> Oceanos Azuis
            </div>
            <p className="mt-1 text-2xl font-bold text-emerald-700">{oceanCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-xs text-blue-600">
              <TrendingUp className="h-4 w-4" /> Tendências
            </div>
            <p className="mt-1 text-2xl font-bold text-blue-700">{trendCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-xs text-[#6b8a7a]">
              <Target className="h-4 w-4" /> Top Aceleração
            </div>
            <p className="mt-1 text-lg font-bold text-[#111916]">
              {topAccel ? `+${topAccel.sales_velocity_7d.toLocaleString()}/7d` : "—"}
            </p>
            <p className="text-[10px] text-[#6b8a7a] truncate">
              {topAccel?.title || ""}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <TrendFilters
        activeStrategy={strategyFilter} onStrategyChange={setStrategyFilter}
        activeCategory={categoryFilter} onCategoryChange={setCategoryFilter}
        searchQuery={searchQuery} onSearchChange={setSearchQuery}
        categories={categories} counts={counts}
      />

      {/* Table */}
      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <TrendingUp className="mx-auto h-12 w-12 text-[#cbd8d1]" />
            <p className="mt-3 text-sm text-[#6b8a7a]">
              {items.length === 0
                ? "O robô ainda não coletou dados. A primeira coleta roda às 4h da manhã."
                : "Nenhum produto encontrado com esses filtros."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#e0e8e3] text-left text-[#6b8a7a]">
                  <th className="px-3 py-2 font-medium">Score</th>
                  <th className="px-3 py-2 font-medium">Produto</th>
                  <th className="px-3 py-2 font-medium">Vendas China</th>
                  <th className="px-3 py-2 font-medium">Velocidade 7d</th>
                  <th className="px-3 py-2 font-medium">Concorr. BR</th>
                  <th className="px-3 py-2 font-medium">Custo BR</th>
                  <th className="px-3 py-2 font-medium">Margem Líq.</th>
                  <th className="px-3 py-2 font-medium">Estratégia</th>
                  <th className="px-3 py-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const cfg = STRATEGY_CONFIG[item.strategy] || STRATEGY_CONFIG.PENDENTE
                  const isExpanded = expandedId === `${item.product_id}-${item.source}`
                  return (
                    <React.Fragment key={`${item.product_id}-${item.source}`}>
                      <tr
                        className="border-b border-[#f0f4f2] hover:bg-[#f8faf9] cursor-pointer"
                        onClick={() => setExpandedId(isExpanded ? null : `${item.product_id}-${item.source}`)}
                      >
                        <td className="px-3 py-2.5">
                          <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#f0f4f2] text-xs font-bold">
                            {Math.round(item.trend_score)}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 max-w-[200px]">
                          <p className="font-medium text-[#111916] truncate">{item.title}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <VelocitySparkline data={item.sparkline} />
                            <span className="text-[10px] text-[#6b8a7a]">
                              {item.source === "alibaba" ? "Alibaba" : "AliExpress"}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-2.5 font-mono">
                          {item.sales_total?.toLocaleString() ?? "—"}
                        </td>
                        <td className="px-3 py-2.5 font-mono text-emerald-700 font-semibold">
                          +{item.sales_velocity_7d.toLocaleString()}
                        </td>
                        <td className="px-3 py-2.5">
                          {item.ml_competitors !== null ? (
                            <span className={item.ml_competitors === 0 ? "font-semibold text-emerald-700" : ""}>
                              {item.ml_competitors === 0 ? "Nenhum" : `${item.ml_competitors} anúncios`}
                            </span>
                          ) : "—"}
                        </td>
                        <td className="px-3 py-2.5 font-mono">
                          {item.landed_cost_brl != null
                            ? `R$ ${item.landed_cost_brl.toFixed(2)}`
                            : "—"}
                        </td>
                        <td className="px-3 py-2.5 font-mono">
                          {item.net_margin_pct != null ? (
                            <span className={item.net_margin_pct >= 35 ? "text-emerald-700 font-semibold" : ""}>
                              {item.net_margin_pct.toFixed(1)}%
                            </span>
                          ) : "—"}
                        </td>
                        <td className="px-3 py-2.5">
                          <Badge className={cfg.color}>{cfg.icon} {cfg.label}</Badge>
                        </td>
                        <td className="px-3 py-2.5">
                          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-[#f8faf9]">
                          <td colSpan={9} className="px-6 py-4">
                            <div className="grid grid-cols-2 gap-4 text-xs lg:grid-cols-4">
                              <div>
                                <p className="text-[#6b8a7a]">Velocidade 30d</p>
                                <p className="font-semibold">+{item.sales_velocity_30d.toLocaleString()} vendas</p>
                              </div>
                              <div>
                                <p className="text-[#6b8a7a]">Aceleração</p>
                                <p className="font-semibold">{item.acceleration > 0 ? "+" : ""}{item.acceleration.toFixed(1)}%</p>
                              </div>
                              <div>
                                <p className="text-[#6b8a7a]">Preço Sugerido BR</p>
                                <p className="font-semibold">
                                  {item.suggested_price_brl != null ? `R$ ${item.suggested_price_brl.toFixed(2)}` : "—"}
                                </p>
                              </div>
                              <div>
                                <p className="text-[#6b8a7a]">Full no ML</p>
                                <p className="font-semibold">
                                  {item.ml_full_share_pct != null ? `${item.ml_full_share_pct.toFixed(0)}%` : "—"}
                                </p>
                              </div>
                              {item.supplier_name && (
                                <div>
                                  <p className="text-[#6b8a7a]">Fornecedor</p>
                                  <p className="font-semibold">{item.supplier_name}
                                    {item.is_verified && <span className="ml-1 text-emerald-600">✓</span>}
                                  </p>
                                </div>
                              )}
                              {item.moq && (
                                <div>
                                  <p className="text-[#6b8a7a]">MOQ</p>
                                  <p className="font-semibold">{item.moq} un</p>
                                </div>
                              )}
                            </div>
                            <div className="mt-3 flex gap-2">
                              <a href={item.url} target="_blank" rel="noopener noreferrer"
                                 className="inline-flex items-center gap-1 rounded-md bg-[#176449] px-3 py-1.5 text-xs text-white hover:bg-[#124f3a]">
                                <ExternalLink className="h-3 w-3" /> Ver na China
                              </a>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
