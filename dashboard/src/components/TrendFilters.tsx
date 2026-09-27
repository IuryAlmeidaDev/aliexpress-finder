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
  activeStrategy, onStrategyChange, activeCategory, onCategoryChange,
  searchQuery, onSearchChange, categories, counts,
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
                ? "bg-[#176449] text-white shadow-xs"
                : "bg-[#f0f4f2] text-[#3b5249] hover:bg-[#e0e8e3]"
            }`}
          >
            <span>{p.icon}</span>
            {p.label}
            {counts[p.key] !== undefined && (
              <span className="ml-1 rounded-full bg-white/20 px-1.5 text-[10px]">
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
          className="rounded-md border border-[#cbd8d1] bg-white px-2 py-1 text-xs"
        >
          <option value="">Todas as categorias</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <Input
          placeholder="Buscar produto..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-8 w-48 text-xs"
        />
      </div>
    </div>
  )
}
