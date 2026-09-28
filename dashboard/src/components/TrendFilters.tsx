import React from "react"
import { Input } from "@/components/ui/input"

interface Props {
  activeStrategy: string
  onStrategyChange: (s: string) => void
  activeCategory: string
  onCategoryChange: (c: string) => void
  searchQuery: string
  onSearchChange: (q: string) => void
  categories: string[]
  counts: Record<string, number>
}

const STRATEGY_PILLS = [
  { key: "", label: "Todos", icon: "📊" },
  { key: "OCEANO_AZUL", label: "Oceano Azul", icon: "🔥" },
  { key: "TENDENCIA", label: "Tendência", icon: "🚀" },
  { key: "EMERGENTE", label: "Emergente", icon: "📈" },
  { key: "SATURADO", label: "Saturado", icon: "⚠️" },
]

export const TrendFilters: React.FC<Props> = ({
  activeStrategy,
  onStrategyChange,
  activeCategory,
  onCategoryChange,
  searchQuery,
  onSearchChange,
  categories,
  counts,
}) => {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap gap-1.5">
        {STRATEGY_PILLS.map((p) => (
          <button
            key={p.key}
            onClick={() => onStrategyChange(p.key)}
            className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition-all ${
              activeStrategy === p.key
                ? "bg-[#176449] dark:bg-[#10b981] text-white shadow-xs font-semibold"
                : "bg-[#f0f4f2] dark:bg-[#13201a] text-[#3b5249] dark:text-[#8ea398] hover:bg-[#e0e8e3] dark:hover:bg-[#1b2c23] border border-transparent dark:border-[#22362b]"
            }`}
          >
            <span>{p.icon}</span>
            {p.label}
            {counts[p.key] !== undefined && (
              <span className="ml-1 rounded-full bg-white/25 dark:bg-black/30 px-1.5 text-[10px]">
                {counts[p.key]}
              </span>
            )}
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <select
          value={activeCategory}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="rounded-md border border-[#cbd8d1] dark:border-[#22362b] bg-white dark:bg-[#0c1410] px-2 py-1 text-xs text-[#111916] dark:text-zinc-200 focus:outline-none cursor-pointer max-w-[200px] truncate"
        >
          <option value="" className="dark:bg-[#0c1410]">Todas as categorias</option>
          {categories.map((c) => (
            <option key={c} value={c} className="dark:bg-[#0c1410]">{c}</option>
          ))}
        </select>
        <Input
          placeholder="Buscar produto..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-8 w-48 text-xs border-[#cbd8d1] dark:border-[#22362b] dark:bg-[#0c1410] dark:text-white dark:placeholder-zinc-500"
        />
      </div>
    </div>
  )
}
