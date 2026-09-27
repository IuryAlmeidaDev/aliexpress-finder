import React, { useState, useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TrendFilters } from "@/components/TrendFilters"
import { VelocitySparkline } from "@/components/VelocitySparkline"
import { TrendOpportunity } from "@/types"
import {
  TrendingUp,
  Target,
  Flame,
  BarChart2,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  Search,
} from "lucide-react"

interface Props {
  items: TrendOpportunity[]
}

const STRATEGY_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  OCEANO_AZUL: { label: "Oceano Azul", color: "bg-emerald-100 text-emerald-800 border-emerald-300", icon: "🔥" },
  TENDENCIA: { label: "Tendência", color: "bg-blue-100 text-blue-800 border-blue-300", icon: "🚀" },
  EMERGENTE: { label: "Emergente", color: "bg-amber-100 text-amber-800 border-amber-300", icon: "📈" },
  SATURADO: { label: "Saturado", color: "bg-red-100 text-red-800 border-red-300", icon: "⚠️" },
  PENDENTE: { label: "Pendente", color: "bg-gray-100 text-gray-700 border-gray-300", icon: "⏳" },
}

type SortField =
  | "trend_score"
  | "title"
  | "sales_total"
  | "sales_velocity_7d"
  | "ml_competitors"
  | "landed_cost_brl"
  | "net_margin_pct"

export const TrendsView: React.FC<Props> = ({ items }) => {
  const [strategyFilter, setStrategyFilter] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [sortField, setSortField] = useState<SortField>("trend_score")
  const [sortAsc, setSortAsc] = useState(false)
  const [page, setPage] = useState(1)
  const pageSize = 20

  const categories = useMemo(
    () => [...new Set(items.map((i) => i.category))].filter(Boolean).sort(),
    [items]
  )

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
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim()
      result = result.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          (i.supplier_name || "").toLowerCase().includes(q) ||
          (i.ml_query || "").toLowerCase().includes(q) ||
          (i.category || "").toLowerCase().includes(q)
      )
    }
    return result
  }, [items, strategyFilter, categoryFilter, searchQuery])

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      let valA: any = 0
      let valB: any = 0

      if (sortField === "trend_score") {
        valA = a.trend_score ?? 0
        valB = b.trend_score ?? 0
      } else if (sortField === "title") {
        return sortAsc ? a.title.localeCompare(b.title) : b.title.localeCompare(a.title)
      } else if (sortField === "sales_total") {
        valA = a.sales_total ?? 0
        valB = b.sales_total ?? 0
      } else if (sortField === "sales_velocity_7d") {
        valA = a.sales_velocity_7d ?? 0
        valB = b.sales_velocity_7d ?? 0
      } else if (sortField === "ml_competitors") {
        valA = a.ml_competitors ?? 9999
        valB = b.ml_competitors ?? 9999
      } else if (sortField === "landed_cost_brl") {
        valA = a.landed_cost_brl ?? 0
        valB = b.landed_cost_brl ?? 0
      } else if (sortField === "net_margin_pct") {
        valA = a.net_margin_pct ?? 0
        valB = b.net_margin_pct ?? 0
      }

      if (sortAsc) {
        return valA > valB ? 1 : -1
      } else {
        return valA < valB ? 1 : -1
      }
    })
  }, [filtered, sortField, sortAsc])

  const totalPages = Math.ceil(sorted.length / pageSize) || 1
  const paginated = useMemo(() => {
    const start = (page - 1) * pageSize
    return sorted.slice(start, start + pageSize)
  }, [sorted, page])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(field === "title" || field === "ml_competitors")
    }
    setPage(1)
  }

  const oceanCount = items.filter((i) => i.strategy === "OCEANO_AZUL").length
  const trendCount = items.filter((i) => i.strategy === "TENDENCIA").length
  const topAccel =
    items.length > 0
      ? items.reduce((a, b) => (a.sales_velocity_7d > b.sales_velocity_7d ? a : b))
      : null

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Card className="border-[#dbe4df] bg-white shadow-xs">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-xs text-[#5a6e65]">
              <span>Monitorados</span>
              <BarChart2 className="h-4 w-4 text-[#176449]" />
            </div>
            <p className="mt-1 text-2xl font-bold text-[#111916]">{items.length}</p>
            <p className="text-[11px] text-[#5a6e65] mt-1">Produtos rastreados na China</p>
          </CardContent>
        </Card>

        <Card className="border-emerald-200 bg-emerald-50/50 shadow-xs">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-xs font-medium text-emerald-800">
              <span>Oceanos Azuis</span>
              <Flame className="h-4 w-4 text-emerald-600" />
            </div>
            <p className="mt-1 text-2xl font-bold text-emerald-950">{oceanCount}</p>
            <p className="text-[11px] text-emerald-700 mt-1">0 concorrentes diretos no Brasil</p>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50/50 shadow-xs">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-xs font-medium text-blue-800">
              <span>Tendências Virais</span>
              <TrendingUp className="h-4 w-4 text-blue-600" />
            </div>
            <p className="mt-1 text-2xl font-bold text-blue-950">{trendCount}</p>
            <p className="text-[11px] text-blue-700 mt-1">Crescimento acelerado na China</p>
          </CardContent>
        </Card>

        <Card className="border-[#dbe4df] bg-white shadow-xs">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-xs text-[#5a6e65]">
              <span>Top Aceleração</span>
              <Target className="h-4 w-4 text-[#176449]" />
            </div>
            <p className="mt-1 text-xl font-bold text-[#111916]">
              {topAccel ? `+${topAccel.sales_velocity_7d.toLocaleString()} / 7d` : "—"}
            </p>
            <p className="text-[11px] text-[#5a6e65] truncate mt-1" title={topAccel?.title}>
              {topAccel?.title || "Nenhum produto"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <TrendFilters
        activeStrategy={strategyFilter}
        onStrategyChange={(s) => {
          setStrategyFilter(s)
          setPage(1)
        }}
        activeCategory={categoryFilter}
        onCategoryChange={(c) => {
          setCategoryFilter(c)
          setPage(1)
        }}
        searchQuery={searchQuery}
        onSearchChange={(q) => {
          setSearchQuery(q)
          setPage(1)
        }}
        categories={categories}
        counts={counts}
      />

      {/* Table */}
      {sorted.length === 0 ? (
        <Card className="border-[#dbe4df] bg-white shadow-xs">
          <CardContent className="py-12 text-center">
            <TrendingUp className="mx-auto h-12 w-12 text-[#cbd8d1]" />
            <p className="mt-3 text-sm font-medium text-[#111916]">
              {items.length === 0
                ? "O robô ainda não coletou dados. A primeira coleta roda às 4h da manhã."
                : "Nenhum produto encontrado com os filtros selecionados."}
            </p>
            {items.length > 0 && (
              <Button
                variant="outline"
                size="xs"
                onClick={() => {
                  setStrategyFilter("")
                  setCategoryFilter("")
                  setSearchQuery("")
                  setPage(1)
                }}
                className="mt-3 text-xs border-[#cbd8d1]"
              >
                Limpar filtros
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card className="border-[#dbe4df] bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-[#f8faf9] border-b border-[#dbe4df] text-[#5a6e65] font-semibold select-none">
                  <th
                    onClick={() => handleSort("trend_score")}
                    className="px-3 py-2.5 cursor-pointer hover:text-[#111916] transition-colors w-16"
                  >
                    <div className="flex items-center gap-1">
                      Score <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort("title")}
                    className="px-3 py-2.5 cursor-pointer hover:text-[#111916] transition-colors"
                  >
                    <div className="flex items-center gap-1">
                      Produto <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort("sales_total")}
                    className="px-3 py-2.5 cursor-pointer hover:text-[#111916] transition-colors text-right w-24"
                  >
                    <div className="flex items-center justify-end gap-1">
                      Vendas China <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort("sales_velocity_7d")}
                    className="px-3 py-2.5 cursor-pointer hover:text-[#111916] transition-colors text-right w-28"
                  >
                    <div className="flex items-center justify-end gap-1">
                      Velocidade 7d <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort("ml_competitors")}
                    className="px-3 py-2.5 cursor-pointer hover:text-[#111916] transition-colors text-center w-24"
                  >
                    <div className="flex items-center justify-center gap-1">
                      Concorr. BR <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort("landed_cost_brl")}
                    className="px-3 py-2.5 cursor-pointer hover:text-[#111916] transition-colors text-right w-24"
                  >
                    <div className="flex items-center justify-end gap-1">
                      Custo BR <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort("net_margin_pct")}
                    className="px-3 py-2.5 cursor-pointer hover:text-[#111916] transition-colors text-right w-24"
                  >
                    <div className="flex items-center justify-end gap-1">
                      Margem Líq. <ArrowUpDown className="w-3 h-3" />
                    </div>
                  </th>
                  <th className="px-3 py-2.5 w-28 text-center">Estratégia</th>
                  <th className="px-3 py-2.5 w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#edf2ef]">
                {paginated.map((item) => {
                  const cfg = STRATEGY_CONFIG[item.strategy] || STRATEGY_CONFIG.PENDENTE
                  const itemKey = `${item.product_id}-${item.source}`
                  const isExpanded = expandedId === itemKey
                  return (
                    <React.Fragment key={itemKey}>
                      <tr
                        className="hover:bg-[#f3f7f5] transition-colors cursor-pointer group"
                        onClick={() => setExpandedId(isExpanded ? null : itemKey)}
                      >
                        <td className="px-3 py-2.5">
                          <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[#f0f4f2] text-xs font-bold text-[#111916]">
                            {Math.round(item.trend_score)}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 max-w-[240px]">
                          <p className="font-semibold text-[#111916] line-clamp-1 group-hover:text-[#176449] transition-colors" title={item.title}>
                            {item.title}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <VelocitySparkline data={item.sparkline} />
                            <Badge variant="outline" className="text-[9px] py-0 px-1 border-gray-200 text-[#5a6e65]">
                              {item.source === "alibaba" ? "Alibaba" : "AliExpress"}
                            </Badge>
                          </div>
                        </td>
                        <td className="px-3 py-2.5 font-mono text-right text-gray-700">
                          {item.sales_total?.toLocaleString() ?? "—"}
                        </td>
                        <td className="px-3 py-2.5 font-mono text-right text-emerald-700 font-semibold">
                          +{item.sales_velocity_7d.toLocaleString()}
                        </td>
                        <td className="px-3 py-2.5 text-center">
                          {item.ml_competitors !== null ? (
                            <span className={item.ml_competitors === 0 ? "font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded" : "text-gray-700"}>
                              {item.ml_competitors === 0 ? "0 anúncios" : `${item.ml_competitors} anunc.`}
                            </span>
                          ) : (
                            <span className="text-[#5a6e65]">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2.5 font-mono text-right font-medium text-gray-900">
                          {item.landed_cost_brl != null
                            ? `R$ ${item.landed_cost_brl.toFixed(2)}`
                            : "—"}
                        </td>
                        <td className="px-3 py-2.5 font-mono text-right">
                          {item.net_margin_pct != null ? (
                            <span
                              className={`font-semibold ${
                                item.net_margin_pct >= 35
                                  ? "text-emerald-700"
                                  : item.net_margin_pct >= 20
                                  ? "text-blue-700"
                                  : "text-amber-700"
                              }`}
                            >
                              {item.net_margin_pct.toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-[#5a6e65]">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2.5 text-center">
                          <Badge variant="outline" className={`text-[10px] font-semibold border ${cfg.color}`}>
                            {cfg.icon} {cfg.label}
                          </Badge>
                        </td>
                        <td className="px-3 py-2.5 text-right text-[#5a6e65]">
                          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-[#f8faf9]">
                          <td colSpan={9} className="px-6 py-4 border-b border-[#e0e8e3]">
                            <div className="grid grid-cols-2 gap-4 text-xs lg:grid-cols-4">
                              <div className="bg-white p-2.5 rounded-lg border border-[#dbe4df]">
                                <p className="text-[#5a6e65]">Velocidade 30d</p>
                                <p className="font-semibold text-sm text-[#111916] mt-0.5">
                                  +{item.sales_velocity_30d.toLocaleString()} vendas
                                </p>
                              </div>
                              <div className="bg-white p-2.5 rounded-lg border border-[#dbe4df]">
                                <p className="text-[#5a6e65]">Aceleração Semanal</p>
                                <p className="font-semibold text-sm text-[#111916] mt-0.5">
                                  {item.acceleration > 0 ? "+" : ""}
                                  {item.acceleration.toFixed(1)}%
                                </p>
                              </div>
                              <div className="bg-white p-2.5 rounded-lg border border-[#dbe4df]">
                                <p className="text-[#5a6e65]">Preço Sugerido BR</p>
                                <p className="font-semibold text-sm text-emerald-800 mt-0.5">
                                  {item.suggested_price_brl != null
                                    ? `R$ ${item.suggested_price_brl.toFixed(2)}`
                                    : "—"}
                                </p>
                              </div>
                              <div className="bg-white p-2.5 rounded-lg border border-[#dbe4df]">
                                <p className="text-[#5a6e65]">Participação no Full</p>
                                <p className="font-semibold text-sm text-[#111916] mt-0.5">
                                  {item.ml_full_share_pct != null
                                    ? `${item.ml_full_share_pct.toFixed(0)}% dos concorrentes`
                                    : "—"}
                                </p>
                              </div>
                              {item.supplier_name && (
                                <div className="bg-white p-2.5 rounded-lg border border-[#dbe4df]">
                                  <p className="text-[#5a6e65]">Fornecedor</p>
                                  <p className="font-semibold text-[#111916] mt-0.5">
                                    {item.supplier_name}
                                    {item.is_verified && (
                                      <span className="ml-1 text-emerald-600 font-bold" title="Fornecedor Verificado">✓</span>
                                    )}
                                  </p>
                                </div>
                              )}
                              {item.moq && (
                                <div className="bg-white p-2.5 rounded-lg border border-[#dbe4df]">
                                  <p className="text-[#5a6e65]">Pedido Mínimo (MOQ)</p>
                                  <p className="font-semibold text-[#111916] mt-0.5">{item.moq} unidades</p>
                                </div>
                              )}
                            </div>

                            <div className="mt-4 flex flex-wrap items-center gap-2">
                              {item.url && (
                                <a
                                  href={item.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1.5 rounded-md bg-[#176449] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#12523b] transition-colors"
                                >
                                  <ExternalLink className="h-3.5 w-3.5" /> Ver Produto na China
                                </a>
                              )}
                              {item.ml_query && (
                                <a
                                  href={`https://lista.mercadolivre.com.br/${encodeURIComponent(item.ml_query)}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1.5 rounded-md bg-[#e8f1ec] text-[#14523d] border border-[#cbd8d1] px-3 py-1.5 text-xs font-medium hover:bg-[#d5e6dc] transition-colors"
                                >
                                  <Search className="h-3.5 w-3.5" /> Buscar Concorrentes no Mercado Livre
                                </a>
                              )}
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

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-[#dbe4df] bg-[#f8faf9] text-xs text-[#5a6e65]">
            <div>
              Mostrando {sorted.length === 0 ? 0 : (page - 1) * pageSize + 1} a{" "}
              {Math.min(page * pageSize, sorted.length)} de {sorted.length} itens
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon-xs"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="h-7 w-7"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </Button>
              <span className="px-2 font-medium text-[#111916]">
                Página {page} de {totalPages}
              </span>
              <Button
                variant="outline"
                size="icon-xs"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="h-7 w-7"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
