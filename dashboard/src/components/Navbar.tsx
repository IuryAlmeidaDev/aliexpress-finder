import React from "react"
import { Sparkles, Download, Upload, RefreshCw, LogOut, Calendar, Layers, Ship } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { RunReport } from "@/types"

interface NavbarProps {
  runs: RunReport[]
  selectedRunId: string
  onSelectRun: (id: string) => void
  onOpenUpload: () => void
  onRefresh: () => void
  onLogout: () => void
  refreshing: boolean
  activeTab: "radar" | "arbitrage"
  onTabChange: (tab: "radar" | "arbitrage") => void
}

export const Navbar: React.FC<NavbarProps> = ({
  runs,
  selectedRunId,
  onSelectRun,
  onOpenUpload,
  onRefresh,
  onLogout,
  refreshing,
  activeTab,
  onTabChange,
}) => {
  const currentRun = runs.find((r) => r.id === selectedRunId) || runs[runs.length - 1]

  const formatDate = (isoString?: string) => {
    if (!isoString) return ""
    try {
      const d = new Date(isoString)
      return d.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    } catch {
      return isoString
    }
  }

  const handleDownload = () => {
    if (!currentRun) return
    window.open(`/radar/api/reports/${currentRun.id}`, "_blank")
  }

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-[#dbe4df] px-4 lg:px-8 py-2.5 transition-all">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Left side: Logo & Navigation Tabs */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-[#176449] text-white shadow-sm shrink-0">
              <Sparkles className="w-4 h-4 text-emerald-200" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-base font-bold text-[#111916] tracking-tight">Radar de Marcas</h1>
                <Badge variant="outline" className="text-[10px] font-semibold bg-[#e8f1ec] text-[#176449] border-[#cbd8d1]">
                  Intelligence
                </Badge>
              </div>
            </div>
          </div>

          {/* Module Switcher Pills */}
          <div className="inline-flex rounded-lg border border-[#cbd8d1] p-0.5 bg-[#f0f4f2] text-xs">
            <button
              onClick={() => onTabChange("radar")}
              className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                activeTab === "radar"
                  ? "bg-white text-[#176449] shadow-xs font-semibold"
                  : "text-[#5a6e65] hover:text-[#111916]"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Radar Mercado Livre
            </button>
            <button
              onClick={() => onTabChange("arbitrage")}
              className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                activeTab === "arbitrage"
                  ? "bg-[#176449] text-white shadow-xs font-semibold"
                  : "text-[#5a6e65] hover:text-[#111916]"
              }`}
            >
              <Ship className="w-3.5 h-3.5" />
              Arbitragem China × ML
            </button>
          </div>
        </div>

        {/* Right side: Actions & Run selector */}
        <div className="flex flex-wrap items-center gap-2">
          {activeTab === "radar" && (
            <>
              {runs.length > 1 ? (
                <div className="flex items-center gap-1 bg-[#f0f4f2] p-1 rounded-lg border border-[#cbd8d1] text-xs">
                  <Calendar className="w-3.5 h-3.5 text-[#5a6e65] ml-1.5" />
                  <select
                    value={selectedRunId}
                    onChange={(e) => onSelectRun(e.target.value)}
                    className="bg-transparent text-xs font-medium text-[#111916] focus:outline-none pr-2 py-1 cursor-pointer"
                  >
                    {runs.map((r, i) => (
                      <option key={r.id} value={r.id}>
                        Coleta #{i + 1} ({formatDate(r.date)}) - {r.products.length} itens
                      </option>
                    ))}
                  </select>
                </div>
              ) : currentRun ? (
                <div className="inline-flex items-center gap-1.5 text-xs text-[#5a6e65] bg-[#f0f4f2] px-2.5 py-1.5 rounded-lg border border-[#dbe4df]">
                  <Calendar className="w-3 h-3 text-[#176449]" />
                  <span>{formatDate(currentRun.date)}</span>
                  <span className="text-gray-400">·</span>
                  <span className="font-semibold text-[#176449]">{currentRun.products.length} itens</span>
                </div>
              ) : null}

              <Button
                variant="outline"
                size="sm"
                onClick={onOpenUpload}
                className="text-xs border-[#cbd8d1] hover:bg-[#e8f1ec] text-[#14523d] h-8"
              >
                <Upload className="w-3.5 h-3.5 mr-1 text-[#176449]" />
                Importar XLSX
              </Button>

              {currentRun && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownload}
                  className="text-xs border-[#cbd8d1] hover:bg-gray-50 text-gray-700 h-8"
                  title="Baixar planilha original da coleta"
                >
                  <Download className="w-3.5 h-3.5 mr-1" />
                  Baixar XLSX
                </Button>
              )}
            </>
          )}

          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onRefresh}
            disabled={refreshing}
            className="text-gray-500 hover:text-gray-900"
            title="Atualizar dados"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-[#176449]" : ""}`} />
          </Button>

          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onLogout}
            className="text-gray-400 hover:text-red-600 hover:bg-red-50"
            title="Encerrar sessão"
          >
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}
