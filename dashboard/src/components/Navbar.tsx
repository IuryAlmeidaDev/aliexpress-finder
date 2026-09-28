import React from "react"
import { Sparkles, Download, Upload, RefreshCw, LogOut, Calendar, Layers, Ship, TrendingUp, Sun, Moon } from "lucide-react"
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
  activeTab: "radar" | "arbitrage" | "trends"
  onTabChange: (tab: "radar" | "arbitrage" | "trends") => void
  theme?: "light" | "dark"
  onToggleTheme?: () => void
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
  theme = "light",
  onToggleTheme,
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
    <header className="sticky top-0 z-30 bg-white/95 dark:bg-[#0c1410]/95 backdrop-blur-md border-b border-[#dbe4df] dark:border-[#1d2e26] px-4 lg:px-8 py-2.5 transition-colors">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Left side: Logo & Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-[#176449] dark:bg-[#10b981] text-white shadow-sm shrink-0">
              <Sparkles className="w-4 h-4 text-emerald-200 dark:text-[#062e20]" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-base font-bold text-[#111916] dark:text-white tracking-tight">Radar de Marcas</h1>
                <Badge variant="outline" className="text-[10px] font-semibold bg-[#e8f1ec] dark:bg-[#152e22] text-[#176449] dark:text-[#34d399] border-[#cbd8d1] dark:border-[#1f4232]">
                  Intelligence
                </Badge>
              </div>
            </div>
          </div>

          {/* Module Switcher Pills */}
          <div className="inline-flex rounded-lg border border-[#cbd8d1] dark:border-[#22362b] p-0.5 bg-[#f0f4f2] dark:bg-[#13201a] text-xs shrink-0">
            <button
              onClick={() => onTabChange("radar")}
              className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                activeTab === "radar"
                  ? "bg-white dark:bg-[#1c2e24] text-[#176449] dark:text-[#34d399] shadow-xs font-semibold"
                  : "text-[#5a6e65] dark:text-[#8ea398] hover:text-[#111916] dark:hover:text-white"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Radar ML</span>
            </button>
            <button
              onClick={() => onTabChange("arbitrage")}
              className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                activeTab === "arbitrage"
                  ? "bg-white dark:bg-[#1c2e24] text-[#176449] dark:text-[#34d399] shadow-xs font-semibold"
                  : "text-[#5a6e65] dark:text-[#8ea398] hover:text-[#111916] dark:hover:text-white"
              }`}
            >
              <Ship className="w-3.5 h-3.5" />
              <span>Arbitragem China</span>
            </button>
            <button
              onClick={() => onTabChange("trends")}
              className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                activeTab === "trends"
                  ? "bg-white dark:bg-[#1c2e24] text-[#176449] dark:text-[#34d399] shadow-xs font-semibold"
                  : "text-[#5a6e65] dark:text-[#8ea398] hover:text-[#111916] dark:hover:text-white"
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Tendências</span>
            </button>
          </div>
        </div>

        {/* Right side: Actions, Select & Controls */}
        <div className="flex items-center gap-2 shrink-0 flex-nowrap overflow-x-auto pb-0.5 md:pb-0">
          {activeTab === "radar" && (
            <>
              {runs.length > 1 ? (
                <div className="flex items-center gap-1 bg-[#f0f4f2] dark:bg-[#13201a] p-1 rounded-lg border border-[#cbd8d1] dark:border-[#22362b] text-xs shrink-0">
                  <Calendar className="w-3.5 h-3.5 text-[#5a6e65] dark:text-[#8ea398] ml-1.5 shrink-0" />
                  <select
                    value={selectedRunId}
                    onChange={(e) => onSelectRun(e.target.value)}
                    className="bg-transparent text-xs font-medium text-[#111916] dark:text-zinc-200 focus:outline-none pr-1 py-0.5 cursor-pointer max-w-[190px] sm:max-w-xs truncate"
                  >
                    {runs.map((r, i) => (
                      <option key={r.id} value={r.id} className="dark:bg-[#13201a] dark:text-zinc-200">
                        Coleta #{i + 1} ({formatDate(r.date)}) - {r.products.length} itens
                      </option>
                    ))}
                  </select>
                </div>
              ) : currentRun ? (
                <div className="inline-flex items-center gap-1.5 text-xs text-[#5a6e65] dark:text-[#8ea398] bg-[#f0f4f2] dark:bg-[#13201a] px-2.5 py-1.5 rounded-lg border border-[#dbe4df] dark:border-[#22362b] shrink-0">
                  <Calendar className="w-3 h-3 text-[#176449] dark:text-[#10b981]" />
                  <span>{formatDate(currentRun.date)}</span>
                  <span className="text-gray-400">·</span>
                  <span className="font-semibold text-[#176449] dark:text-[#34d399]">{currentRun.products.length} itens</span>
                </div>
              ) : null}

              <Button
                variant="outline"
                size="sm"
                onClick={onOpenUpload}
                className="text-xs border-[#cbd8d1] dark:border-[#22362b] hover:bg-[#e8f1ec] dark:hover:bg-[#182820] text-[#14523d] dark:text-[#34d399] dark:bg-[#13201a] h-8 shrink-0"
              >
                <Upload className="w-3.5 h-3.5 mr-1 text-[#176449] dark:text-[#34d399]" />
                <span className="hidden sm:inline">Importar XLSX</span>
                <span className="sm:hidden">Importar</span>
              </Button>

              {currentRun && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownload}
                  className="text-xs border-[#cbd8d1] dark:border-[#22362b] hover:bg-gray-50 dark:hover:bg-[#182820] text-gray-700 dark:text-zinc-300 dark:bg-[#13201a] h-8 shrink-0"
                  title="Baixar planilha original da coleta"
                >
                  <Download className="w-3.5 h-3.5 mr-1" />
                  <span className="hidden sm:inline">Baixar XLSX</span>
                  <span className="sm:hidden">Baixar</span>
                </Button>
              )}
            </>
          )}

          {/* Grouped utility controls: Theme, Refresh, Logout */}
          <div className="flex items-center gap-1 border-l border-[#dbe4df] dark:border-[#22362b] pl-2 shrink-0">
            {/* Theme Toggle Button */}
            {onToggleTheme && (
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={onToggleTheme}
                className="text-gray-500 dark:text-zinc-400 hover:text-amber-500 dark:hover:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-950/30"
                title={theme === "dark" ? "Mudar para modo claro" : "Mudar para modo escuro"}
                aria-label="Alternar tema claro/escuro"
              >
                {theme === "dark" ? (
                  <Sun className="w-4 h-4 text-amber-400" />
                ) : (
                  <Moon className="w-4 h-4 text-slate-600" />
                )}
              </Button>
            )}

            {/* Refresh */}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={onRefresh}
              disabled={refreshing}
              className="text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white"
              title="Atualizar dados"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-[#176449] dark:text-[#34d399]" : ""}`} />
            </Button>

            {/* Logout */}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={onLogout}
              className="text-[#5a6e65] dark:text-zinc-400 hover:text-red-700 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30"
              title="Encerrar sessão"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}
