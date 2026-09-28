import React from "react"
import { Sparkles, Shield, Cpu, ExternalLink, Activity } from "lucide-react"

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-[#dbe4df] dark:border-[#1d2e26] bg-white/80 dark:bg-[#0c1410]/90 backdrop-blur-md py-6 px-4 lg:px-8 mt-12 transition-colors">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-[#5a6e65] dark:text-[#8ea398]">
        {/* Brand info */}
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-[#176449] dark:bg-[#10b981] flex items-center justify-center text-white shrink-0 shadow-xs">
            <Sparkles className="w-3.5 h-3.5 text-emerald-100 dark:text-[#062e20]" />
          </div>
          <div>
            <div className="font-bold text-[#111916] dark:text-white flex items-center gap-1.5">
              <span>Radar de Marcas</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#e8f1ec] dark:bg-[#152e22] text-[#176449] dark:text-[#34d399] border border-[#cbd8d1] dark:border-[#1f4232]">
                v2.4
              </span>
            </div>
            <p className="text-[11px] text-[#5a6e65] dark:text-[#8ea398]">
              Inteligência de Mercado · Arbitragem China × Mercado Livre · Tendências
            </p>
          </div>
        </div>

        {/* VPS & Engine Status */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium text-[#111916] dark:text-zinc-200">VPS Oracle GRU</span>
            <span className="text-gray-400 dark:text-zinc-600">·</span>
            <span>Serviço Online</span>
          </div>
          <div className="flex items-center gap-1 text-[#5a6e65] dark:text-[#8ea398]">
            <Activity className="w-3 h-3 text-[#176449] dark:text-[#10b981]" />
            <span>Coleta Semanal Segundas 07:07</span>
          </div>
        </div>

        {/* Security & Copyright */}
        <div className="flex items-center gap-2 text-[11px] text-gray-500 dark:text-zinc-500">
          <Shield className="w-3.5 h-3.5 text-[#176449] dark:text-emerald-400" />
          <span>Ambiente Seguro & Autenticado</span>
        </div>
      </div>
    </footer>
  )
}
