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
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts"
import { ArbitrageReport, ArbitrageItem } from "@/types"

interface ArbitrageViewProps {
  initialScans: ArbitrageReport[]
}

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

  // Filters
  const [strategyFilter, setStrategyFilter] = useState<string>("all")
  const [tableSearch, setTableSearch] = useState<string>("")
  const [selectedItem, setSelectedItem] = useState<ArbitrageItem | null>(null)

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
        const matchesSummary = item.summary.toLowerCase().includes(q)
        if (!matchesTitle && !matchesSupplier && !matchesSummary) return false
      }
      return true
    })
  }, [activeReport, strategyFilter, tableSearch])

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
          <div className="flex items-center justify-between border-b pb-1">
            <span className="font-bold text-[#176449]">{data.strategy_label}</span>
            <span className="font-mono text-[10px] text-gray-500">{data.source}</span>
          </div>
          <p className="font-medium text-[#111916] line-clamp-2">{data.china_title}</p>
          <div className="grid grid-cols-2 gap-2 pt-1">
            <div className="bg-[#f0f4f2] p-1.5 rounded">
              <span className="text-[10px] text-gray-500">Custo Desembarcado:</span>
              <div className="font-bold text-gray-900">R$ {data.landed_cost_unit_brl.toFixed(2)}</div>
            </div>
            <div className="bg-emerald-50 p-1.5 rounded">
              <span className="text-[10px] text-emerald-700">Preço Mercado Livre:</span>
              <div className="font-bold text-emerald-900">R$ {data.reference_sale_price_brl.toFixed(2)}</div>
            </div>
          </div>
          <div className="pt-1 flex items-center justify-between text-[11px] border-t text-[#5a6e65]">
            <span>Margem Líquida: <strong className="text-emerald-700">{data.net_margin_pct.toFixed(1)}%</strong></span>
            <span>Lucro: <strong className="text-emerald-700">R$ {data.net_profit_brl.toFixed(2)}</strong></span>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-6">
      {/* 1. Header Search & Scan Box */}
      <Card className="border-[#dbe4df] bg-white shadow-xs">
        <CardHeader className="pb-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-[#176449] text-white flex items-center justify-center text-xs">
                  <Ship className="w-4 h-4" />
                </div>
                <CardTitle className="text-base font-bold text-[#111916]">
                  Radar de Arbitragem: China Wholesale × Mercado Livre
                </CardTitle>
                <Badge className="bg-[#176449] text-white text-[10px]">
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
                  onChange={(e) => setSelectedScanId(e.target.value)}
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
                    className="h-8 text-xs border-[#cbd8d1]"
                    title="Baixar planilha Excel do cruzamento"
                  >
                    <Download className="w-3.5 h-3.5 mr-1" /> Baixar Excel
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
            <Alert variant="destructive" className="mt-3 text-xs py-2">
              <AlertTriangle className="w-4 h-4" />
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
                <div className="text-[11px] text-gray-500 mt-1 truncate">
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
            <Card className="border-purple-200 bg-purple-50/50 shadow-xs">
              <CardContent className="p-4">
                <div className="text-xs font-medium text-purple-800 flex items-center justify-between">
                  <span>Marca Própria</span>
                  <Sparkles className="w-4 h-4 text-purple-600" />
                </div>
                <div className="text-2xl font-bold text-purple-950 mt-0.5">{activeReport.private_label_count}</div>
                <div className="text-[11px] text-purple-700 mt-1">
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
                  <ScatterChart margin={{ top: 20, right: 30, bottom: 25, left: 10 }}>
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
                    <Scatter name="Produtos" data={scatterData} cursor="pointer">
                      {scatterData.map((entry, index) => {
                        let color = "#10b981" // emerald
                        if (entry.strategy === "OCEANO_AZUL") color = "#059669"
                        else if (entry.strategy === "ALTA_MARGEM") color = "#2563eb"
                        else if (entry.strategy === "MARCA_PROPRIA") color = "#9333ea"
                        else color = "#f97316"

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
              <div className="flex flex-wrap items-center justify-between text-[11px] text-[#5a6e65] mt-2 pt-2 border-t">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#059669]" /> Oceano Azul (0 concorrentes)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#2563eb]" /> Alta Margem (&gt;35%)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#9333ea]" /> Marca Própria
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#f97316]" /> Saturado
                  </span>
                </div>
                <span className="italic text-gray-400">Clique em qualquer produto para conferir detalhes</span>
              </div>
            </CardContent>
          </Card>

          {/* 3. Filterable Comparison Table */}
          <Card className="border-[#dbe4df] bg-white shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div>
                  <CardTitle className="text-base font-bold text-[#111916]">
                    Tabela Comparativa de Oportunidades
                  </CardTitle>
                  <CardDescription className="text-xs text-[#5a6e65] mt-0.5">
                    Exibindo {filteredItems.length} de {activeReport.items.length} produtos analisados.
                  </CardDescription>
                </div>

                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Filtrar por nome ou fornecedor..."
                    value={tableSearch}
                    onChange={(e) => setTableSearch(e.target.value)}
                    className="h-8 w-60 text-xs border-[#cbd8d1]"
                  />
                </div>
              </div>

              {/* Strategy filter pills */}
              <div className="flex flex-wrap gap-1.5 pt-2 border-t">
                {[
                  { key: "all", label: "Todos", count: activeReport.items.length },
                  { key: "OCEANO_AZUL", label: "Oceano Azul", count: activeReport.blue_ocean_count },
                  { key: "ALTA_MARGEM", label: "Alta Margem", count: activeReport.high_margin_count },
                  { key: "MARCA_PROPRIA", label: "Marca Própria", count: activeReport.private_label_count },
                  { key: "SATURADO", label: "Saturado", count: activeReport.saturated_count },
                ].map((pill) => (
                  <button
                    key={pill.key}
                    onClick={() => setStrategyFilter(pill.key)}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                      strategyFilter === pill.key
                        ? "bg-[#176449] text-white shadow-xs"
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
                    <tr className="bg-[#f8faf9] border-y border-[#dbe4df] text-[#5a6e65] font-semibold">
                      <th className="py-2.5 px-4 w-32">Estratégia</th>
                      <th className="py-2.5 px-4">Produto (China Wholesale)</th>
                      <th className="py-2.5 px-4 text-right w-24">FOB China</th>
                      <th className="py-2.5 px-4 text-right w-28">Custo Brasil</th>
                      <th className="py-2.5 px-4 text-right w-28">Preço ML</th>
                      <th className="py-2.5 px-4 text-right w-28">Margem Líq.</th>
                      <th className="py-2.5 px-4 text-center w-28">Concorrência</th>
                      <th className="py-2.5 px-4 text-right w-24">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#edf2ef]">
                    {filteredItems.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="py-8 text-center text-[#5a6e65]">
                          Nenhum produto encontrado com os filtros selecionados.
                        </td>
                      </tr>
                    ) : (
                      filteredItems.map((item, idx) => {
                        let badgeBg = "bg-gray-100 text-gray-800"
                        if (item.strategy === "OCEANO_AZUL") badgeBg = "bg-emerald-100 text-emerald-800 border-emerald-300"
                        else if (item.strategy === "ALTA_MARGEM") badgeBg = "bg-blue-100 text-blue-800 border-blue-300"
                        else if (item.strategy === "MARCA_PROPRIA") badgeBg = "bg-purple-100 text-purple-800 border-purple-300"
                        else if (item.strategy === "SATURADO") badgeBg = "bg-amber-100 text-amber-900 border-amber-300"

                        return (
                          <tr
                            key={idx}
                            className="hover:bg-[#f3f7f5] transition-colors"
                          >
                            {/* Strategy */}
                            <td className="py-3 px-4">
                              <Badge variant="outline" className={`text-[10px] font-semibold border ${badgeBg}`}>
                                {item.strategy_label}
                              </Badge>
                            </td>

                            {/* Title & Supplier */}
                            <td className="py-3 px-4 max-w-sm">
                              <div className="font-semibold text-[#111916] line-clamp-1" title={item.china_title}>
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
                              <div className="text-[10px] text-gray-500">R$ {item.china_fob_brl.toFixed(2)}</div>
                            </td>

                            {/* Landed Brasil */}
                            <td className="py-3 px-4 text-right">
                              <div className="font-semibold text-gray-900">R$ {item.landed_cost_unit_brl.toFixed(2)}</div>
                              <div className="text-[10px] text-gray-500">c/ II e ICMS</div>
                            </td>

                            {/* ML Price */}
                            <td className="py-3 px-4 text-right">
                              <div className="font-bold text-emerald-800">R$ {item.reference_sale_price_brl.toFixed(2)}</div>
                              <div className="text-[10px] text-gray-500">
                                {item.ml_competitors_count > 0 ? "Média ML" : "Sugerido"}
                              </div>
                            </td>

                            {/* Margin */}
                            <td className="py-3 px-4 text-right">
                              <div
                                className={`font-bold ${
                                  item.net_margin_pct >= 35
                                    ? "text-emerald-700"
                                    : item.net_margin_pct >= 20
                                    ? "text-blue-700"
                                    : "text-amber-700"
                                }`}
                              >
                                {item.net_margin_pct.toFixed(1)}%
                              </div>
                              <div className="text-[10px] text-gray-600 font-medium">
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
                              <div className="flex items-center justify-end gap-1.5">
                                {item.china_url && (
                                  <a
                                    href={item.china_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="p-1 rounded hover:bg-gray-100 text-gray-600 hover:text-gray-900"
                                    title="Abrir no fornecedor na China"
                                  >
                                    <ExternalLink className="w-3.5 h-3.5" />
                                  </a>
                                )}
                                {item.ml_top_competitor_url && (
                                  <a
                                    href={item.ml_top_competitor_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="p-1 rounded hover:bg-emerald-50 text-emerald-700 hover:text-emerald-900"
                                    title="Ver concorrente no Mercado Livre"
                                  >
                                    <Store className="w-3.5 h-3.5" />
                                  </a>
                                )}
                              </div>
                            </td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
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
    </div>
  )
}
