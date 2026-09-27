import React, { useState, useMemo } from "react"
import {
  Search,
  Download,
  Sparkles,
  ExternalLink,
  ArrowRight,
  TrendingUp,
  Award,
  AlertTriangle,
  Layers,
  DollarSign,
  Loader2,
  Package,
  ShieldCheck,
  CheckCircle2,
  Ship,
  Store,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  X,
  FileSpreadsheet,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet"
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts"
import { ArbitrageReport, ArbitrageItem } from "@/types"

interface ArbitrageViewProps {
  initialScans: ArbitrageReport[]
}

type SortField =
  | "strategy"
  | "title"
  | "china_fob"
  | "landed_cost"
  | "ml_price"
  | "net_margin"
  | "competitors"

export const ArbitrageView: React.FC<ArbitrageViewProps> = ({ initialScans }) => {
  const [scans, setScans] = useState<ArbitrageReport[]>(initialScans)
  const [selectedScanId, setSelectedScanId] = useState<string>(
    initialScans.length > 0 ? initialScans[0].id || "" : ""
  )
  const [query, setQuery] = useState<string>("")
  const [source, setSource] = useState<string>("alibaba")
  const [limit, setLimit] = useState<number>(12)
  const [maxMoq, setMaxMoq] = useState<number>(500)
  const [scanning, setScanning] = useState<boolean>(false)
  const [scanError, setScanError] = useState<string | null>(null)

  // Filters & State
  const [strategyFilter, setStrategyFilter] = useState<string>("all")
  const [tableSearch, setTableSearch] = useState<string>("")
  const [selectedItem, setSelectedItem] = useState<ArbitrageItem | null>(null)
  const [sortField, setSortField] = useState<SortField>("net_margin")
  const [sortAsc, setSortAsc] = useState<boolean>(false)
  const [page, setPage] = useState<number>(1)
  const pageSize = 15

  const activeReport = useMemo(() => {
    return scans.find((s) => s.id === selectedScanId) || scans[0] || null
  }, [scans, selectedScanId])

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setScanning(true)
    setScanError(null)

    try {
      const res = await fetch("/radar/api/arbitrage/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          source,
          limit,
          max_moq: maxMoq,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || "Falha ao escanear arbitragem.")
      }

      const report: ArbitrageReport = await res.json()
      setScans((prev) => [report, ...prev])
      setSelectedScanId(report.id || "")
      setQuery("")
      setPage(1)
    } catch (err: any) {
      setScanError(err.message || "Erro de conexão.")
    } finally {
      setScanning(false)
    }
  }

  const handleDownload = () => {
    if (!activeReport?.id) return
    window.open(`/radar/api/arbitrage/download/${activeReport.id}`, "_blank")
  }

  // Filtered Items in Table
  const filteredItems = useMemo(() => {
    if (!activeReport?.items) return []
    return activeReport.items.filter((item) => {
      if (strategyFilter !== "all" && item.strategy !== strategyFilter) return false
      if (tableSearch.trim()) {
        const q = tableSearch.toLowerCase()
        const matchesTitle = item.china_title.toLowerCase().includes(q)
        const matchesSupplier = item.supplier_name.toLowerCase().includes(q)
        const matchesSummary = (item.summary || "").toLowerCase().includes(q)
        if (!matchesTitle && !matchesSupplier && !matchesSummary) return false
      }
      return true
    })
  }, [activeReport, strategyFilter, tableSearch])

  // Sorted Items
  const sortedItems = useMemo(() => {
    return [...filteredItems].sort((a, b) => {
      let valA: any = 0
      let valB: any = 0

      if (sortField === "strategy") {
        valA = a.strategy_label
        valB = b.strategy_label
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA)
      } else if (sortField === "title") {
        return sortAsc ? a.china_title.localeCompare(b.china_title) : b.china_title.localeCompare(a.china_title)
      } else if (sortField === "china_fob") {
        valA = a.china_fob_brl
        valB = b.china_fob_brl
      } else if (sortField === "landed_cost") {
        valA = a.landed_cost_unit_brl
        valB = b.landed_cost_unit_brl
      } else if (sortField === "ml_price") {
        valA = a.reference_sale_price_brl
        valB = b.reference_sale_price_brl
      } else if (sortField === "net_margin") {
        valA = a.net_margin_pct
        valB = b.net_margin_pct
      } else if (sortField === "competitors") {
        valA = a.ml_competitors_count
        valB = b.ml_competitors_count
      }

      if (sortAsc) {
        return valA > valB ? 1 : -1
      } else {
        return valA < valB ? 1 : -1
      }
    })
  }, [filteredItems, sortField, sortAsc])

  const totalPages = Math.ceil(sortedItems.length / pageSize) || 1
  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize
    return sortedItems.slice(start, start + pageSize)
  }, [sortedItems, page])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(field === "title" || field === "competitors")
    }
    setPage(1)
  }

  // Scatter data: Landed Cost (X) vs ML Price (Y)
  const scatterData = useMemo(() => {
    if (!activeReport?.items) return []
    return activeReport.items.map((it) => ({
      ...it,
      x: it.landed_cost_unit_brl,
      y: it.reference_sale_price_brl,
      z: it.net_profit_brl,
    }))
  }, [activeReport])

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as ArbitrageItem
      return (
        <div className="bg-white/95 backdrop-blur-md p-3 rounded-lg border border-[#cbd8d1] shadow-lg max-w-xs text-xs space-y-1.5 z-50">
          <div className="flex items-center justify-between border-b border-[#edf2ef] pb-1">
            <span className="font-bold text-[#176449]">{data.strategy_label}</span>
            <span className="font-mono text-[10px] text-gray-500 uppercase">{data.source}</span>
          </div>
          <p className="font-medium text-[#111916] line-clamp-2 leading-tight">{data.china_title}</p>
          <div className="grid grid-cols-2 gap-2 pt-1">
            <div className="bg-[#f0f4f2] p-1.5 rounded">
              <span className="text-[10px] text-[#5a6e65]">Custo Desembarcado:</span>
              <div className="font-bold text-gray-900">R$ {data.landed_cost_unit_brl.toFixed(2)}</div>
            </div>
            <div className="bg-emerald-50 p-1.5 rounded">
              <span className="text-[10px] text-emerald-700">Preço Mercado Livre:</span>
              <div className="font-bold text-emerald-900">R$ {data.reference_sale_price_brl.toFixed(2)}</div>
            </div>
          </div>
          <div className="pt-1 flex items-center justify-between text-[11px] border-t border-[#edf2ef] text-[#5a6e65]">
            <span>
              Margem Líquida:{" "}
              <strong className={data.net_margin_pct >= 35 ? "text-emerald-700 font-bold" : "text-blue-700"}>
                {data.net_margin_pct.toFixed(1)}%
              </strong>
            </span>
            <span className="text-[#176449] font-medium">Clique para ver ficha →</span>
          </div>
        </div>
      )
    }
    return null
  }

  const getStrategyColor = (strategy: string) => {
    if (strategy === "OCEANO_AZUL") return "#059669"
    if (strategy === "ALTA_MARGEM") return "#2563eb"
    if (strategy === "MARCA_PROPRIA") return "#0d9488"
    return "#ea580c"
  }

  return (
    <div className="space-y-6">
      {/* 1. Header Search & Scan Box */}
      <Card className="border-[#dbe4df] bg-white shadow-xs">
        <CardHeader className="pb-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-[#176449] text-white flex items-center justify-center text-xs shadow-xs">
                  <Ship className="w-4 h-4 text-emerald-200" />
                </div>
                <CardTitle className="text-base font-bold text-[#111916]">
                  Radar de Arbitragem: China Wholesale × Mercado Livre
                </CardTitle>
                <Badge variant="outline" className="bg-[#e8f1ec] text-[#14523d] border-[#cbd8d1] text-[10px] font-semibold">
                  B2B Importação
                </Badge>
              </div>
              <CardDescription className="text-xs text-[#5a6e65] mt-1">
                Busque itens campeões de vendas com baixo valor no atacado da China e compare automaticamente a concorrência e o preço de venda no Brasil.
              </CardDescription>
            </div>

            {/* Scan selector if multiple scans */}
            {scans.length > 0 && (
              <div className="flex items-center gap-2">
                <select
                  value={selectedScanId}
                  onChange={(e) => {
                    setSelectedScanId(e.target.value)
                    setPage(1)
                  }}
                  className="h-8 rounded-md border border-[#cbd8d1] bg-[#f8faf9] px-2 text-xs text-[#111916] focus:outline-none"
                >
                  {scans.map((s, idx) => (
                    <option key={s.id || idx} value={s.id}>
                      {s.query} ({s.source}) · {s.total_scanned} itens
                    </option>
                  ))}
                </select>
                {activeReport && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownload}
                    className="h-8 text-xs border-[#cbd8d1] text-[#14523d] hover:bg-[#e8f1ec]"
                    title="Baixar planilha Excel do cruzamento"
                  >
                    <Download className="w-3.5 h-3.5 mr-1 text-[#176449]" /> Baixar Excel
                  </Button>
                )}
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleScan} className="flex flex-col sm:flex-row items-center gap-2">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Ex: organizador acrílico, garrafa térmica digital, dispenser automático..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-9 h-10 text-xs border-[#cbd8d1]"
                disabled={scanning}
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="h-10 rounded-md border border-[#cbd8d1] bg-white px-3 text-xs font-medium text-[#111916] focus:outline-none"
                disabled={scanning}
              >
                <option value="alibaba">Alibaba (Atacado B2B / Fábricas)</option>
                <option value="ali">AliExpress (Consumidor B2C / Demanda)</option>
                <option value="ambos">Ambos (Varredura Híbrida)</option>
              </select>

              <Button
                type="submit"
                disabled={scanning || !query.trim()}
                className="h-10 bg-[#176449] hover:bg-[#12523b] text-white text-xs font-medium px-4 shrink-0"
              >
                {scanning ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> Escaneando e Cruzando...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-1.5 text-emerald-200" /> Analisar Arbitragem
                  </>
                )}
              </Button>
            </div>
          </form>

          {scanError && (
            <Alert variant="destructive" className="mt-3 text-xs py-2 bg-red-50 border-red-200 text-red-900">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <AlertTitle className="text-xs font-semibold">Erro no escaneamento</AlertTitle>
              <AlertDescription className="text-xs">{scanError}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* 2. Active Report Dashboard View */}
      {activeReport ? (
        <>
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {/* Total */}
            <Card className="border-[#dbe4df] bg-white shadow-xs">
              <CardContent className="p-4">
                <div className="text-xs text-[#5a6e65]">Total Analisado</div>
                <div className="text-2xl font-bold text-[#111916] mt-0.5">{activeReport.total_scanned}</div>
                <div className="text-[11px] text-[#5a6e65] mt-1 truncate">
                  Câmbio: R$ {activeReport.usd_rate.toFixed(2)}
                </div>
              </CardContent>
            </Card>

            {/* Oceano Azul */}
            <Card className="border-emerald-200 bg-emerald-50/50 shadow-xs">
              <CardContent className="p-4">
                <div className="text-xs font-medium text-emerald-800 flex items-center justify-between">
                  <span>Oceano Azul</span>
                  <Award className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="text-2xl font-bold text-emerald-950 mt-0.5">{activeReport.blue_ocean_count}</div>
                <div className="text-[11px] text-emerald-700 mt-1">
                  0 concorrentes no Brasil
                </div>
              </CardContent>
            </Card>

            {/* Alta Margem */}
            <Card className="border-blue-200 bg-blue-50/50 shadow-xs">
              <CardContent className="p-4">
                <div className="text-xs font-medium text-blue-800 flex items-center justify-between">
                  <span>Alta Margem</span>
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                </div>
                <div className="text-2xl font-bold text-blue-950 mt-0.5">{activeReport.high_margin_count}</div>
                <div className="text-[11px] text-blue-700 mt-1">
                  &gt; 35% de lucro líquido
                </div>
              </CardContent>
            </Card>

            {/* Marca Própria */}
            <Card className="border-teal-200 bg-teal-50/50 shadow-xs">
              <CardContent className="p-4">
                <div className="text-xs font-medium text-teal-800 flex items-center justify-between">
                  <span>Marca Própria</span>
                  <Sparkles className="w-4 h-4 text-teal-600" />
                </div>
                <div className="text-2xl font-bold text-teal-950 mt-0.5">{activeReport.private_label_count}</div>
                <div className="text-[11px] text-teal-700 mt-1">
                  Espaço para diferenciação
                </div>
              </CardContent>
            </Card>

            {/* Saturado */}
            <Card className="border-orange-200 bg-orange-50/40 shadow-xs">
              <CardContent className="p-4">
                <div className="text-xs font-medium text-amber-800 flex items-center justify-between">
                  <span>Saturado</span>
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                </div>
                <div className="text-2xl font-bold text-amber-950 mt-0.5">{activeReport.saturated_count}</div>
                <div className="text-[11px] text-amber-700 mt-1">
                  Guerra de preços
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Scatter Plot: Custo Desembarcado x Preço Mercado Livre */}
          <Card className="border-[#dbe4df] bg-white shadow-xs">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold text-[#111916]">
                    Dispersão de Arbitragem: Custo Desembarcado (R$) × Preço Mercado Livre (R$)
                  </CardTitle>
                  <CardDescription className="text-xs text-[#5a6e65] mt-0.5">
                    Pontos mais acima da diagonal representam maior margem de lucro líquido entre a fábrica e a venda final.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              <div className="w-full h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart
                    margin={{ top: 20, right: 30, bottom: 25, left: 10 }}
                    onClick={(e: any) => {
                      if (e && e.activePayload && e.activePayload[0]) {
                        setSelectedItem(e.activePayload[0].payload)
                      }
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis
                      type="number"
                      dataKey="x"
                      name="Custo Desembarcado (R$)"
                      unit=" R$"
                      tick={{ fontSize: 11, fill: "#5a6e65" }}
                      label={{
                        value: "Custo Desembarcado Brasil (c/ Impostos II e ICMS) →",
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
                      name="Preço Mercado Livre (R$)"
                      unit=" R$"
                      tick={{ fontSize: 11, fill: "#5a6e65" }}
                      label={{
                        value: "Preço Médio Mercado Livre (R$) →",
                        angle: -90,
                        position: "insideLeft",
                        offset: 5,
                        fontSize: 11,
                        fill: "#14523d",
                        fontWeight: 600,
                      }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Scatter
                      name="Produtos"
                      data={scatterData}
                      cursor="pointer"
                    >
                      {scatterData.map((entry, index) => {
                        const color = getStrategyColor(entry.strategy)
                        return (
                          <Cell
                            key={`cell-${index}`}
                            fill={color}
                            fillOpacity={0.85}
                            stroke="#ffffff"
                            strokeWidth={1.5}
                            r={7}
                            onClick={() => setSelectedItem(entry)}
                          />
                        )
                      })}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>

              {/* Legend */}
              <div className="flex flex-wrap items-center justify-between text-[11px] text-[#5a6e65] mt-2 pt-2 border-t border-gray-100">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#059669]" /> Oceano Azul (0 concorrentes)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#2563eb]" /> Alta Margem (&gt;35%)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#0d9488]" /> Marca Própria
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#ea580c]" /> Saturado
                  </span>
                </div>
                <span className="italic text-gray-400">Clique em qualquer ponto do gráfico para abrir a ficha</span>
              </div>
            </CardContent>
          </Card>

          {/* 3. Filterable Comparison Table */}
          <Card className="border-[#dbe4df] bg-white shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-base font-bold text-[#111916]">
                      Tabela Comparativa de Oportunidades
                    </CardTitle>
                    <Badge variant="outline" className="text-xs bg-[#e8f1ec] text-[#14523d] border-[#cbd8d1]">
                      {sortedItems.length} de {activeReport.items.length} produtos
                    </Badge>
                  </div>
                  <CardDescription className="text-xs text-[#5a6e65] mt-0.5">
                    Compare margens líquidas, preços desembarcados e concorrência no Mercado Livre.
                  </CardDescription>
                </div>

                <div className="flex items-center gap-2">
                  <div className="relative w-64">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                    <Input
                      placeholder="Filtrar por nome ou fornecedor..."
                      value={tableSearch}
                      onChange={(e) => {
                        setTableSearch(e.target.value)
                        setPage(1)
                      }}
                      className="pl-8 h-8 text-xs border-[#cbd8d1]"
                    />
                  </div>
                </div>
              </div>

              {/* Strategy filter pills */}
              <div className="flex flex-wrap gap-1.5 pt-2 border-t border-gray-100">
                {[
                  { key: "all", label: "Todos", count: activeReport.items.length },
                  { key: "OCEANO_AZUL", label: "Oceano Azul", count: activeReport.blue_ocean_count },
                  { key: "ALTA_MARGEM", label: "Alta Margem", count: activeReport.high_margin_count },
                  { key: "MARCA_PROPRIA", label: "Marca Própria", count: activeReport.private_label_count },
                  { key: "SATURADO", label: "Saturado", count: activeReport.saturated_count },
                ].map((pill) => (
                  <button
                    key={pill.key}
                    onClick={() => {
                      setStrategyFilter(pill.key)
                      setPage(1)
                    }}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                      strategyFilter === pill.key
                        ? "bg-[#176449] text-white shadow-xs font-semibold"
                        : "bg-[#f0f4f2] text-[#5a6e65] hover:bg-[#e2ede7]"
                    }`}
                  >
                    {pill.label} ({pill.count})
                  </button>
                ))}
              </div>
            </CardHeader>

            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-[#f8faf9] border-y border-[#dbe4df] text-[#5a6e65] font-semibold select-none">
                      <th
                        onClick={() => handleSort("strategy")}
                        className="py-2.5 px-4 cursor-pointer hover:text-[#111916] transition-colors w-32"
                      >
                        <div className="flex items-center gap-1">
                          Estratégia <ArrowUpDown className="w-3 h-3" />
                        </div>
                      </th>
                      <th
                        onClick={() => handleSort("title")}
                        className="py-2.5 px-4 cursor-pointer hover:text-[#111916] transition-colors"
                      >
                        <div className="flex items-center gap-1">
                          Produto (China Wholesale) <ArrowUpDown className="w-3 h-3" />
                        </div>
                      </th>
                      <th
                        onClick={() => handleSort("china_fob")}
                        className="py-2.5 px-4 cursor-pointer hover:text-[#111916] transition-colors text-right w-24"
                      >
                        <div className="flex items-center justify-end gap-1">
                          FOB China <ArrowUpDown className="w-3 h-3" />
                        </div>
                      </th>
                      <th
                        onClick={() => handleSort("landed_cost")}
                        className="py-2.5 px-4 cursor-pointer hover:text-[#111916] transition-colors text-right w-28"
                      >
                        <div className="flex items-center justify-end gap-1">
                          Custo Brasil <ArrowUpDown className="w-3 h-3" />
                        </div>
                      </th>
                      <th
                        onClick={() => handleSort("ml_price")}
                        className="py-2.5 px-4 cursor-pointer hover:text-[#111916] transition-colors text-right w-28"
                      >
                        <div className="flex items-center justify-end gap-1">
                          Preço ML <ArrowUpDown className="w-3 h-3" />
                        </div>
                      </th>
                      <th
                        onClick={() => handleSort("net_margin")}
                        className="py-2.5 px-4 cursor-pointer hover:text-[#111916] transition-colors text-right w-28"
                      >
                        <div className="flex items-center justify-end gap-1">
                          Margem Líq. <ArrowUpDown className="w-3 h-3" />
                        </div>
                      </th>
                      <th
                        onClick={() => handleSort("competitors")}
                        className="py-2.5 px-4 cursor-pointer hover:text-[#111916] transition-colors text-center w-28"
                      >
                        <div className="flex items-center justify-center gap-1">
                          Concorrência <ArrowUpDown className="w-3 h-3" />
                        </div>
                      </th>
                      <th className="py-2.5 px-4 text-right w-24">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#edf2ef]">
                    {paginatedItems.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="py-8 text-center text-[#5a6e65]">
                          Nenhum produto encontrado com os filtros selecionados.
                        </td>
                      </tr>
                    ) : (
                      paginatedItems.map((item, idx) => {
                        let badgeBg = "bg-gray-100 text-gray-800 border-gray-300"
                        if (item.strategy === "OCEANO_AZUL") badgeBg = "bg-emerald-100 text-emerald-800 border-emerald-300"
                        else if (item.strategy === "ALTA_MARGEM") badgeBg = "bg-blue-100 text-blue-800 border-blue-300"
                        else if (item.strategy === "MARCA_PROPRIA") badgeBg = "bg-teal-100 text-teal-800 border-teal-300"
                        else if (item.strategy === "SATURADO") badgeBg = "bg-amber-100 text-amber-900 border-amber-300"

                        return (
                          <tr
                            key={idx}
                            onClick={() => setSelectedItem(item)}
                            className="hover:bg-[#f3f7f5] transition-colors cursor-pointer group"
                          >
                            {/* Strategy */}
                            <td className="py-3 px-4">
                              <Badge variant="outline" className={`text-[10px] font-semibold border ${badgeBg}`}>
                                {item.strategy_label}
                              </Badge>
                            </td>

                            {/* Title & Supplier */}
                            <td className="py-3 px-4 max-w-sm">
                              <div
                                className="font-semibold text-[#111916] line-clamp-1 group-hover:text-[#176449] transition-colors"
                                title={item.china_title}
                              >
                                {item.china_title}
                              </div>
                              <div className="flex items-center gap-2 mt-0.5 text-[10px] text-[#5a6e65]">
                                <span className="font-medium text-gray-700">{item.supplier_name}</span>
                                <span>·</span>
                                <span>MOQ: {item.moq} un</span>
                                {item.is_verified && (
                                  <span className="text-emerald-700 flex items-center gap-0.5 font-medium">
                                    <ShieldCheck className="w-2.5 h-2.5" /> Verificado
                                  </span>
                                )}
                              </div>
                            </td>

                            {/* FOB China */}
                            <td className="py-3 px-4 text-right">
                              <div className="font-bold text-[#111916]">US$ {item.china_fob_usd.toFixed(2)}</div>
                              <div className="text-[10px] text-gray-500 font-mono">R$ {item.china_fob_brl.toFixed(2)}</div>
                            </td>

                            {/* Landed Brasil */}
                            <td className="py-3 px-4 text-right">
                              <div className="font-semibold text-gray-900 font-mono">
                                R$ {item.landed_cost_unit_brl.toFixed(2)}
                              </div>
                              <div className="text-[10px] text-gray-500">c/ II e ICMS</div>
                            </td>

                            {/* ML Price */}
                            <td className="py-3 px-4 text-right">
                              <div className="font-bold text-emerald-800 font-mono">
                                R$ {item.reference_sale_price_brl.toFixed(2)}
                              </div>
                              <div className="text-[10px] text-gray-500">
                                {item.ml_competitors_count > 0 ? "Média ML" : "Sugerido"}
                              </div>
                            </td>

                            {/* Margin */}
                            <td className="py-3 px-4 text-right">
                              <div
                                className={`font-bold font-mono ${
                                  item.net_margin_pct >= 35
                                    ? "text-emerald-700"
                                    : item.net_margin_pct >= 20
                                    ? "text-blue-700"
                                    : "text-amber-700"
                                }`}
                              >
                                {item.net_margin_pct.toFixed(1)}%
                              </div>
                              <div className="text-[10px] text-gray-600 font-medium font-mono">
                                +R$ {item.net_profit_brl.toFixed(2)}
                              </div>
                            </td>

                            {/* ML Competition */}
                            <td className="py-3 px-4 text-center">
                              {item.ml_competitors_count > 0 ? (
                                <div>
                                  <span className="font-semibold text-[#111916]">{item.ml_competitors_count} anúncios</span>
                                  <div className="text-[10px] text-gray-500">{item.ml_full_share_pct.toFixed(0)}% no Full</div>
                                </div>
                              ) : (
                                <Badge variant="outline" className="text-[10px] bg-emerald-50 text-emerald-800 border-emerald-200">
                                  0 anúncios
                                </Badge>
                              )}
                            </td>

                            {/* Actions */}
                            <td className="py-3 px-4 text-right">
                              <Button
                                variant="ghost"
                                size="xs"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setSelectedItem(item)
                                }}
                                className="text-[#176449] hover:bg-[#e8f1ec] font-medium"
                              >
                                Ficha →
                              </Button>
                            </td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination footer */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-[#dbe4df] bg-[#f8faf9] text-xs text-[#5a6e65]">
                <div>
                  Mostrando {sortedItems.length === 0 ? 0 : (page - 1) * pageSize + 1} a{" "}
                  {Math.min(page * pageSize, sortedItems.length)} de {sortedItems.length} itens
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
            </CardContent>
          </Card>
        </>
      ) : (
        /* Empty State */
        <div className="bg-white border border-[#dbe4df] rounded-xl p-12 text-center max-w-lg mx-auto shadow-sm">
          <div className="w-12 h-12 rounded-xl bg-[#e8f1ec] text-[#176449] flex items-center justify-center mx-auto mb-3">
            <Ship className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-lg text-[#111916]">Nenhum Cruzamento Realizado</h3>
          <p className="text-xs text-[#5a6e65] mt-1 mb-4">
            Digite um nicho ou produto na barra acima para cruzar os campeões do atacado chinês (Alibaba/AliExpress) com a concorrência do Mercado Livre Brasil.
          </p>
        </div>
      )}

      {/* 4. Detailed Inspection Sheet for Arbitrage Item */}
      <Sheet open={!!selectedItem} onOpenChange={(open) => !open && setSelectedItem(null)}>
        <SheetContent className="w-full sm:max-w-xl overflow-y-auto p-6 bg-white">
          {selectedItem && (
            <>
              <SheetHeader className="pb-4 border-b border-[#dbe4df] text-left">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className="text-xs font-semibold bg-[#e8f1ec] text-[#14523d] border-[#cbd8d1]">
                    {selectedItem.strategy_label}
                  </Badge>
                  <Badge variant="outline" className="text-[10px] font-mono text-gray-700 uppercase">
                    {selectedItem.source}
                  </Badge>
                  {selectedItem.is_verified && (
                    <Badge variant="outline" className="text-[10px] text-emerald-800 bg-emerald-50 border-emerald-200">
                      ✓ Fornecedor Auditado
                    </Badge>
                  )}
                </div>

                <SheetTitle className="text-base font-bold text-[#111916] leading-snug">
                  {selectedItem.china_title}
                </SheetTitle>

                <SheetDescription className="text-xs text-[#5a6e65] pt-1">
                  Fornecedor: <strong className="text-[#111916]">{selectedItem.supplier_name}</strong> · MOQ: {selectedItem.moq} unidades
                </SheetDescription>
              </SheetHeader>

              <div className="space-y-6 pt-4 text-xs">
                {/* Key Economics Trio */}
                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-[#f8faf9] p-3 rounded-lg border border-[#e2ede7] text-center">
                    <div className="text-[11px] text-[#5a6e65] mb-0.5">Custo Desembarcado</div>
                    <div className="text-xl font-bold text-gray-900 font-mono">
                      R$ {selectedItem.landed_cost_unit_brl.toFixed(2)}
                    </div>
                    <div className="text-[10px] text-gray-500 mt-0.5">unitário Brasil</div>
                  </div>

                  <div className="bg-[#f8faf9] p-3 rounded-lg border border-[#e2ede7] text-center">
                    <div className="text-[11px] text-[#5a6e65] mb-0.5">Preço Venda (ML)</div>
                    <div className="text-xl font-bold text-emerald-700 font-mono">
                      R$ {selectedItem.reference_sale_price_brl.toFixed(2)}
                    </div>
                    <div className="text-[10px] text-emerald-800 mt-0.5">
                      {selectedItem.ml_competitors_count > 0 ? "Média de mercado" : "Preço sugerido"}
                    </div>
                  </div>

                  <div className="bg-[#f8faf9] p-3 rounded-lg border border-[#e2ede7] text-center">
                    <div className="text-[11px] text-[#5a6e65] mb-0.5">Margem Líquida</div>
                    <div
                      className={`text-xl font-bold font-mono ${
                        selectedItem.net_margin_pct >= 35 ? "text-emerald-700" : "text-blue-700"
                      }`}
                    >
                      {selectedItem.net_margin_pct.toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-[#176449] font-medium font-mono">
                      +R$ {selectedItem.net_profit_brl.toFixed(2)}/un
                    </div>
                  </div>
                </div>

                {/* Financial Anatomy Breakdown */}
                <div>
                  <h4 className="font-semibold text-xs text-[#111916] uppercase tracking-wider flex items-center gap-1.5 mb-2">
                    <DollarSign className="w-3.5 h-3.5 text-[#176449]" /> Memória de Cálculo Tributário & Custos
                  </h4>
                  <div className="space-y-1.5 bg-[#f8faf9] p-3 rounded-lg border border-[#dbe4df]">
                    <div className="flex justify-between items-center py-1 border-b border-gray-200">
                      <span className="text-[#5a6e65]">1. Custo Fábrica China (FOB):</span>
                      <span className="font-mono font-medium text-[#111916]">
                        US$ {selectedItem.china_fob_usd.toFixed(2)} (R$ {selectedItem.china_fob_brl.toFixed(2)})
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-gray-200">
                      <span className="text-[#5a6e65]">2. Imposto de Importação (60%):</span>
                      <span className="font-mono font-medium text-[#111916]">
                        R$ {selectedItem.import_tax_unit_brl.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-gray-200">
                      <span className="text-[#5a6e65]">3. ICMS Estadual (Cálculo "Por Dentro"):</span>
                      <span className="font-mono font-medium text-[#111916]">
                        R$ {selectedItem.icms_unit_brl.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-gray-200">
                      <span className="text-[#5a6e65]">4. Frete Internacional Proporcional:</span>
                      <span className="font-mono font-medium text-[#111916]">
                        R$ {selectedItem.freight_unit_brl.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-gray-200">
                      <span className="text-[#5a6e65]">5. Tarifa Mercado Livre Estimada:</span>
                      <span className="font-mono font-medium text-[#111916]">
                        R$ {selectedItem.ml_fee_brl.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center pt-1.5 font-bold text-[#14523d]">
                      <span>Lucro Líquido Unitário Descontado:</span>
                      <span className="font-mono text-sm text-emerald-800">
                        R$ {selectedItem.net_profit_brl.toFixed(2)} (ROI: {selectedItem.roi_pct.toFixed(0)}%)
                      </span>
                    </div>
                  </div>
                </div>

                {/* Competition Snapshot */}
                <div>
                  <h4 className="font-semibold text-xs text-[#111916] uppercase tracking-wider flex items-center gap-1.5 mb-2">
                    <Store className="w-3.5 h-3.5 text-blue-600" /> Cenário Concorrencial no Mercado Livre
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2.5 bg-white border border-[#dbe4df] rounded-lg">
                      <span className="text-[#5a6e65] text-[11px]">Concorrentes Diretos</span>
                      <div className="font-bold text-sm text-[#111916] mt-0.5">
                        {selectedItem.ml_competitors_count === 0
                          ? "0 (Oceano Azul)"
                          : `${selectedItem.ml_competitors_count} anúncios`}
                      </div>
                    </div>
                    <div className="p-2.5 bg-white border border-[#dbe4df] rounded-lg">
                      <span className="text-[#5a6e65] text-[11px]">Presença Mercado Envios Full</span>
                      <div className="font-bold text-sm text-[#111916] mt-0.5">
                        {selectedItem.ml_full_share_pct.toFixed(0)}% dos concorrentes
                      </div>
                    </div>
                    {selectedItem.ml_competitors_count > 0 && (
                      <div className="col-span-2 p-2.5 bg-white border border-[#dbe4df] rounded-lg">
                        <span className="text-[#5a6e65] text-[11px]">Faixa de Preço Observada</span>
                        <div className="font-bold text-xs text-[#111916] mt-0.5 font-mono">
                          Mín: R$ {selectedItem.ml_min_price.toFixed(2)} · Méd: R$ {selectedItem.ml_avg_price.toFixed(2)} · Máx: R$ {selectedItem.ml_max_price.toFixed(2)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Strategic Evaluation */}
                {selectedItem.summary && (
                  <div>
                    <h4 className="font-semibold text-xs text-[#111916] uppercase tracking-wider flex items-center gap-1.5 mb-2">
                      <Award className="w-3.5 h-3.5 text-[#176449]" /> Parecer Executivo de Viabilidade
                    </h4>
                    <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg text-emerald-950 text-[11px] leading-relaxed">
                      {selectedItem.summary}
                    </div>
                  </div>
                )}

                {/* External Action Links */}
                <div className="pt-2 border-t border-gray-100 flex flex-wrap gap-2">
                  {selectedItem.china_url && (
                    <a
                      href={selectedItem.china_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-md bg-[#176449] px-3.5 py-2 text-xs font-medium text-white hover:bg-[#12523b] transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" /> Abrir Fábrica na China
                    </a>
                  )}
                  {selectedItem.ml_top_competitor_url && (
                    <a
                      href={selectedItem.ml_top_competitor_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-md bg-[#e8f1ec] text-[#14523d] border border-[#cbd8d1] px-3.5 py-2 text-xs font-medium hover:bg-[#d5e6dc] transition-colors"
                    >
                      <Store className="w-3.5 h-3.5" /> Ver Concorrente Líder no ML
                    </a>
                  )}
                  {selectedItem.ml_query && (
                    <a
                      href={`https://lista.mercadolivre.com.br/${encodeURIComponent(selectedItem.ml_query)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-md bg-white text-gray-700 border border-[#cbd8d1] px-3.5 py-2 text-xs font-medium hover:bg-gray-50 transition-colors"
                    >
                      <Search className="w-3.5 h-3.5 text-gray-500" /> Buscar Nicho no ML
                    </a>
                  )}
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}
