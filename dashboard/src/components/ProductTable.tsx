import React, { useState, useMemo } from "react"
import {
  Search,
  ArrowUpDown,
  Filter,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Award,
  Sparkles,
  SlidersHorizontal,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Product } from "@/types"
import { formatCategoryName } from "@/lib/categories"

interface ProductTableProps {
  products: Product[]
  onSelectProduct: (product: Product) => void
  selectedCategory: string
  onSelectCategory: (cat: string) => void
}

type SortField = "rank" | "combined" | "demand" | "brand" | "title"

export const ProductTable: React.FC<ProductTableProps> = ({
  products,
  onSelectProduct,
  selectedCategory,
  onSelectCategory,
}) => {
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<"all" | "priority" | "investigating">("all")
  const [minDemand, setMinDemand] = useState<number>(0)
  const [minBrand, setMinBrand] = useState<number>(0)
  const [showAdvancedFilters, setShowAdvancedFilters] = useState<boolean>(false)
  const [sortField, setSortField] = useState<SortField>("rank")
  const [sortAsc, setSortAsc] = useState(true)
  const [page, setPage] = useState(1)
  const pageSize = 20

  const categories = useMemo(() => {
    const set = new Set<string>()
    products.forEach((p) => {
      const name = formatCategoryName(p.category)
      if (name) set.add(name)
    })
    return Array.from(set).sort()
  }, [products])

  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      const catName = formatCategoryName(p.category)

      // Search
      if (search.trim()) {
        const q = search.toLowerCase()
        const matchesTitle = p.title.toLowerCase().includes(q)
        const matchesId = p.id.toLowerCase().includes(q)
        const matchesCat = (p.category || "").toLowerCase().includes(q) || catName.toLowerCase().includes(q)
        const matchesEvidence = (p.demandEvidence + " " + p.brandEvidence + " " + p.counterpoints)
          .toLowerCase()
          .includes(q)
        if (!matchesTitle && !matchesId && !matchesCat && !matchesEvidence) return false
      }

      // Status
      if (statusFilter === "priority" && !p.priority) return false
      if (statusFilter === "investigating" && p.priority) return false

      // Category
      if (selectedCategory && catName !== selectedCategory) return false

      // Min demand & brand
      if (minDemand > 0 && (p.demand ?? 0) < minDemand) return false
      if (minBrand > 0 && (p.brand ?? 0) < minBrand) return false

      return true
    })
  }, [products, search, statusFilter, selectedCategory, minDemand, minBrand])

  const sortedProducts = useMemo(() => {
    return [...filteredProducts].sort((a, b) => {
      let valA: any = 0
      let valB: any = 0

      if (sortField === "rank") {
        valA = a.rank ?? 9999
        valB = b.rank ?? 9999
      } else if (sortField === "combined") {
        valA = a.combined ?? 0
        valB = b.combined ?? 0
      } else if (sortField === "demand") {
        valA = a.demand ?? 0
        valB = b.demand ?? 0
      } else if (sortField === "brand") {
        valA = a.brand ?? 0
        valB = b.brand ?? 0
      } else if (sortField === "title") {
        return sortAsc ? a.title.localeCompare(b.title) : b.title.localeCompare(a.title)
      }

      if (sortAsc) {
        return valA > valB ? 1 : -1
      } else {
        return valA < valB ? 1 : -1
      }
    })
  }, [filteredProducts, sortField, sortAsc])

  const totalPages = Math.ceil(sortedProducts.length / pageSize) || 1
  const paginatedProducts = useMemo(() => {
    const start = (page - 1) * pageSize
    return sortedProducts.slice(start, start + pageSize)
  }, [sortedProducts, page])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(field === "rank" || field === "title")
    }
  }

  const priorityCount = products.filter((p) => p.priority).length
  const investigatingCount = products.length - priorityCount

  return (
    <Card className="border-[#dbe4df] dark:border-[#22362b] bg-white dark:bg-[#13201a] shadow-xs transition-colors">
      <CardHeader className="pb-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-bold text-[#111916] dark:text-white">
                Tabela de Produtos Monitorados
              </CardTitle>
              <Badge variant="outline" className="text-xs bg-[#e8f1ec] dark:bg-[#152e22] text-[#14523d] dark:text-[#34d399] border-[#cbd8d1] dark:border-[#1f4232]">
                {sortedProducts.length} de {products.length} itens
              </Badge>
            </div>
            <CardDescription className="text-xs text-[#5a6e65] dark:text-[#8ea398] mt-0.5">
              Explore o ranking completo, evidências coletadas e hipóteses de diferenciação.
            </CardDescription>
          </div>

          {/* Search bar */}
          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-zinc-500" />
            <Input
              placeholder="Buscar por produto, ID ou categoria..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
              className="pl-9 text-xs h-9 border-[#cbd8d1] dark:border-[#22362b] dark:bg-[#0c1410] dark:text-zinc-100 dark:placeholder-zinc-500"
            />
          </div>
        </div>

        {/* Filter controls */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-gray-100 dark:border-[#1d2e26]">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Status pills */}
            <div className="inline-flex rounded-lg border border-[#cbd8d1] dark:border-[#22362b] p-0.5 bg-[#f0f4f2] dark:bg-[#0c1410]">
              <button
                onClick={() => {
                  setStatusFilter("all")
                  setPage(1)
                }}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  statusFilter === "all"
                    ? "bg-white dark:bg-[#1c2e24] text-[#111916] dark:text-white shadow-xs font-semibold"
                    : "text-[#5a6e65] dark:text-[#8ea398]"
                }`}
              >
                Todos ({products.length})
              </button>
              <button
                onClick={() => {
                  setStatusFilter("priority")
                  setPage(1)
                }}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  statusFilter === "priority"
                    ? "bg-[#176449] dark:bg-[#10b981] text-white shadow-xs font-semibold"
                    : "text-[#5a6e65] dark:text-[#8ea398]"
                }`}
              >
                Oportunidades ({priorityCount})
              </button>
              <button
                onClick={() => {
                  setStatusFilter("investigating")
                  setPage(1)
                }}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  statusFilter === "investigating"
                    ? "bg-amber-700 dark:bg-amber-600 text-white shadow-xs font-semibold"
                    : "text-[#5a6e65] dark:text-[#8ea398]"
                }`}
              >
                Investigar ({investigatingCount})
              </button>
            </div>

            {/* Category selector */}
            {categories.length > 1 && (
              <select
                value={selectedCategory}
                onChange={(e) => {
                  onSelectCategory(e.target.value)
                  setPage(1)
                }}
                className="h-8 rounded-md border border-[#cbd8d1] dark:border-[#22362b] bg-white dark:bg-[#0c1410] px-2 text-xs text-[#111916] dark:text-zinc-200 focus:outline-none cursor-pointer max-w-[210px] truncate"
              >
                <option value="" className="dark:bg-[#0c1410]">Todas Categorias ({categories.length})</option>
                {categories.map((c) => (
                  <option key={c} value={c} className="dark:bg-[#0c1410]">
                    {c}
                  </option>
                ))}
              </select>
            )}

            {/* Advanced score filters toggle */}
            <Button
              variant="outline"
              size="xs"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className={`h-8 text-xs border-[#cbd8d1] dark:border-[#22362b] flex items-center gap-1.5 ${
                showAdvancedFilters || minDemand > 0 || minBrand > 0
                  ? "bg-[#e8f1ec] dark:bg-[#152e22] text-[#14523d] dark:text-[#34d399] border-[#176449] dark:border-[#24523b]"
                  : "text-[#5a6e65] dark:text-[#8ea398] dark:bg-[#0c1410]"
              }`}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Filtros de Score</span>
              {(minDemand > 0 || minBrand > 0) && (
                <span className="w-2 h-2 rounded-full bg-[#176449] dark:bg-[#10b981]" />
              )}
            </Button>
          </div>

          {/* Quick Clear filters */}
          {(search || statusFilter !== "all" || selectedCategory || minDemand > 0 || minBrand > 0) && (
            <Button
              variant="ghost"
              size="xs"
              onClick={() => {
                setSearch("")
                setStatusFilter("all")
                onSelectCategory("")
                setMinDemand(0)
                setMinBrand(0)
                setPage(1)
              }}
              className="text-xs text-[#176449] dark:text-[#34d399] hover:bg-[#e8f1ec] dark:hover:bg-[#152e22]"
            >
              Limpar filtros
            </Button>
          )}
        </div>

        {/* Advanced Score Filters Panel */}
        {showAdvancedFilters && (
          <div className="mt-3 p-3 bg-[#f8faf9] dark:bg-[#0c1410] rounded-lg border border-[#dbe4df] dark:border-[#1d2e26] grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <div className="flex justify-between items-center mb-1 text-[#5a6e65] dark:text-[#8ea398]">
                <span className="font-medium text-[#111916] dark:text-zinc-200">Demanda Mínima:</span>
                <span className="font-bold text-blue-700 dark:text-blue-400">{minDemand} / 100</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={minDemand}
                onChange={(e) => {
                  setMinDemand(Number(e.target.value))
                  setPage(1)
                }}
                className="w-full accent-blue-600 cursor-pointer"
              />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1 text-[#5a6e65] dark:text-[#8ea398]">
                <span className="font-medium text-[#111916] dark:text-zinc-200">Potencial de Marca Mínimo:</span>
                <span className="font-bold text-[#176449] dark:text-[#34d399]">{minBrand} / 100</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={minBrand}
                onChange={(e) => {
                  setMinBrand(Number(e.target.value))
                  setPage(1)
                }}
                className="w-full accent-[#176449] dark:accent-[#10b981] cursor-pointer"
              />
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#f8faf9] dark:bg-[#0c1410] border-y border-[#dbe4df] dark:border-[#1d2e26] text-[#5a6e65] dark:text-[#8ea398] font-semibold select-none">
                <th
                  onClick={() => handleSort("rank")}
                  className="py-2.5 px-4 cursor-pointer hover:text-[#111916] dark:hover:text-white transition-colors w-16"
                >
                  <div className="flex items-center gap-1">
                    # <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort("title")}
                  className="py-2.5 px-4 cursor-pointer hover:text-[#111916] dark:hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-1">
                    Produto & Identificador <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-2.5 px-4">Categoria</th>
                <th
                  onClick={() => handleSort("demand")}
                  className="py-2.5 px-4 cursor-pointer hover:text-[#111916] dark:hover:text-white transition-colors w-32"
                >
                  <div className="flex items-center gap-1">
                    Demanda <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort("brand")}
                  className="py-2.5 px-4 cursor-pointer hover:text-[#111916] dark:hover:text-white transition-colors w-32"
                >
                  <div className="flex items-center gap-1">
                    Potencial Marca <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort("combined")}
                  className="py-2.5 px-4 cursor-pointer hover:text-[#111916] dark:hover:text-white transition-colors w-24 text-center"
                >
                  <div className="flex items-center justify-center gap-1">
                    Score <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-2.5 px-4 text-center w-28">Status</th>
                <th className="py-2.5 px-4 text-right w-24">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#edf2ef] dark:divide-[#1a2d23]">
              {paginatedProducts.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-[#5a6e65] dark:text-[#8ea398]">
                    Nenhum produto encontrado com os filtros selecionados.
                  </td>
                </tr>
              ) : (
                paginatedProducts.map((p) => {
                  const catName = formatCategoryName(p.category)
                  return (
                    <tr
                      key={p.key}
                      onClick={() => onSelectProduct(p)}
                      className="hover:bg-[#f3f7f5] dark:hover:bg-[#15241d] transition-colors cursor-pointer group"
                    >
                      {/* Rank */}
                      <td className="py-3 px-4 font-bold text-[#111916] dark:text-white">
                        <span
                          className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold ${
                            p.rank === 1
                              ? "bg-amber-400 text-amber-950 shadow-xs"
                              : p.rank === 2
                              ? "bg-slate-300 dark:bg-slate-600 text-slate-900 dark:text-slate-100"
                              : p.rank === 3
                              ? "bg-amber-700 text-amber-50"
                              : "text-[#5a6e65] dark:text-zinc-400 bg-gray-100 dark:bg-[#0c1410]"
                          }`}
                        >
                          {p.rank ?? "?"}
                        </span>
                      </td>

                      {/* Product & Details */}
                      <td className="py-3 px-4 max-w-md">
                        <div className="font-semibold text-[#111916] dark:text-zinc-100 line-clamp-1 group-hover:text-[#176449] dark:group-hover:text-[#34d399] transition-colors">
                          {p.title}
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-[10px] text-[#5a6e65] dark:text-[#8ea398]">
                          <span className="font-mono bg-gray-100 dark:bg-[#0c1410] px-1.5 py-0.2 rounded text-gray-700 dark:text-zinc-300">
                            {p.id}
                          </span>
                          <Badge variant="outline" className="text-[9px] py-0 px-1 border-gray-200 dark:border-[#22362b] dark:text-zinc-400">
                            {p.type}
                          </Badge>
                          {p.price !== null ? (
                            <span className="text-emerald-700 dark:text-emerald-400 font-medium">
                              R$ {p.price.toFixed(2)}
                            </span>
                          ) : (
                            <span className="text-amber-700 dark:text-amber-400 flex items-center gap-0.5">
                              <ShieldAlert className="w-2.5 h-2.5" /> Restrito ML
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Category */}
                      <td className="py-3 px-4 text-[#5a6e65] dark:text-[#8ea398]">
                        <span className="bg-[#f0f4f2] dark:bg-[#0c1410] text-gray-800 dark:text-zinc-200 px-2 py-0.5 rounded text-[11px] font-medium border border-transparent dark:border-[#22362b]">
                          {catName}
                        </span>
                      </td>

                      {/* Demand */}
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-between text-[11px] mb-1">
                          <span className="font-bold text-blue-700 dark:text-blue-400">{p.demand ?? 0}</span>
                          <span className="text-[10px] text-[#5a6e65] dark:text-[#8ea398]">({p.demandCoverage ?? 0}%)</span>
                        </div>
                        <div className="w-full h-1.5 bg-gray-100 dark:bg-[#1a2d23] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-600 dark:bg-sky-500 rounded-full"
                            style={{ width: `${p.demand ?? 0}%` }}
                          />
                        </div>
                      </td>

                      {/* Brand Potential */}
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-between text-[11px] mb-1">
                          <span className="font-bold text-[#176449] dark:text-[#34d399]">{p.brand ?? 0}</span>
                          <span className="text-[10px] text-[#5a6e65] dark:text-[#8ea398]">({p.brandCoverage ?? 0}%)</span>
                        </div>
                        <div className="w-full h-1.5 bg-gray-100 dark:bg-[#1a2d23] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-[#176449] dark:bg-[#10b981] rounded-full"
                            style={{ width: `${p.brand ?? 0}%` }}
                          />
                        </div>
                      </td>

                      {/* Combined Score */}
                      <td className="py-3 px-4 text-center">
                        <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full font-bold text-xs bg-[#e8f1ec] dark:bg-[#152e22] text-[#14523d] dark:text-[#34d399] border border-[#cbd8d1] dark:border-[#1f4232] font-mono">
                          {p.combined ?? 0}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4 text-center">
                        {p.priority ? (
                          <Badge className="bg-emerald-600 dark:bg-emerald-700 hover:bg-emerald-700 text-white text-[10px]">
                            Oportunidade
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800/60 text-[10px]">
                            Investigar
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
                            onSelectProduct(p)
                          }}
                          className="text-[#176449] dark:text-[#34d399] hover:bg-[#e8f1ec] dark:hover:bg-[#152e22] font-medium"
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
        <div className="flex items-center justify-between px-4 py-3 border-t border-[#dbe4df] dark:border-[#1d2e26] bg-[#f8faf9] dark:bg-[#0c1410] text-xs text-[#5a6e65] dark:text-[#8ea398]">
          <div>
            Mostrando {sortedProducts.length === 0 ? 0 : (page - 1) * pageSize + 1} a{" "}
            {Math.min(page * pageSize, sortedProducts.length)} de {sortedProducts.length} itens
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="icon-xs"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="h-7 w-7 dark:border-[#22362b] dark:bg-[#13201a] dark:text-zinc-300"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </Button>
            <span className="px-2 font-medium text-[#111916] dark:text-zinc-200">
              Página {page} de {totalPages}
            </span>
            <Button
              variant="outline"
              size="icon-xs"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="h-7 w-7 dark:border-[#22362b] dark:bg-[#13201a] dark:text-zinc-300"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
