import React from "react"
import { Package, TrendingUp, Award, ShieldAlert, Sparkles, AlertCircle } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Product } from "@/types"

interface KpiRailProps {
  products: Product[]
  runCount: number
}

export const KpiRail: React.FC<KpiRailProps> = ({ products, runCount }) => {
  const total = products.length

  const opportunitiesCount = products.filter((p) => p.priority).length
  const investigatingCount = total - opportunitiesCount

  const avgDemand = total
    ? Math.round((products.reduce((acc, p) => acc + (p.demand ?? 0), 0) / total) * 10) / 10
    : 0

  const avgDemandCoverage = total
    ? Math.round((products.reduce((acc, p) => acc + (p.demandCoverage ?? 0), 0) / total) * 10) / 10
    : 0

  const avgBrand = total
    ? Math.round((products.reduce((acc, p) => acc + (p.brand ?? 0), 0) / total) * 10) / 10
    : 0

  const avgBrandCoverage = total
    ? Math.round((products.reduce((acc, p) => acc + (p.brandCoverage ?? 0), 0) / total) * 10) / 10
    : 0

  const avgCombined = total
    ? Math.round((products.reduce((acc, p) => acc + (p.combined ?? 0), 0) / total) * 10) / 10
    : 0

  // Count items with restricted/missing data (USER_PRODUCT or missing review/price)
  const restrictedCount = products.filter((p) => p.price === null || p.reviews === null).length
  const restrictedPct = total ? Math.round((restrictedCount / total) * 100) : 0

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {/* 1. Total Monitorado */}
      <Card className="border-[#dbe4df] bg-white shadow-xs hover:border-[#cbd8d1] transition-all">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs text-[#5a6e65] mb-1">
            <span>Total Monitorado</span>
            <Package className="w-4 h-4 text-[#176449]" />
          </div>
          <div className="text-2xl font-bold text-[#111916]">{total}</div>
          <div className="text-[11px] text-[#5a6e65] mt-1 flex items-center gap-1">
            <span className="font-medium text-[#176449]">
              {runCount > 1 ? `${runCount} coletas históricas` : "Linha de base inicial"}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* 2. Oportunidades Promovidas */}
      <Card className="border-[#dbe4df] bg-white shadow-xs hover:border-[#cbd8d1] transition-all">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs text-[#5a6e65] mb-1">
            <span>Oportunidades</span>
            <Award className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-[#111916]">{opportunitiesCount}</div>
          <div className="text-[11px] text-[#5a6e65] mt-1 flex items-center justify-between">
            <span>Investigar:</span>
            <span className="font-medium text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded">
              {investigatingCount} itens
            </span>
          </div>
        </CardContent>
      </Card>

      {/* 3. Demanda Média */}
      <Card className="border-[#dbe4df] bg-white shadow-xs hover:border-[#cbd8d1] transition-all">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs text-[#5a6e65] mb-1">
            <span>Demanda Média</span>
            <TrendingUp className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-[#111916]">
            {avgDemand}
            <span className="text-xs font-normal text-[#5a6e65]">/100</span>
          </div>
          <div className="mt-1">
            <div className="flex justify-between text-[10px] text-[#5a6e65] mb-0.5">
              <span>Cobertura:</span>
              <span className="font-semibold text-blue-700">{avgDemandCoverage}%</span>
            </div>
            <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full" style={{ width: `${avgDemandCoverage}%` }} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 4. Potencial de Marca */}
      <Card className="border-[#dbe4df] bg-white shadow-xs hover:border-[#cbd8d1] transition-all">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs text-[#5a6e65] mb-1">
            <span>Potencial de Marca</span>
            <Sparkles className="w-4 h-4 text-[#176449]" />
          </div>
          <div className="text-2xl font-bold text-[#111916]">
            {avgBrand}
            <span className="text-xs font-normal text-[#5a6e65]">/100</span>
          </div>
          <div className="mt-1">
            <div className="flex justify-between text-[10px] text-[#5a6e65] mb-0.5">
              <span>Cobertura:</span>
              <span className="font-semibold text-[#176449]">{avgBrandCoverage}%</span>
            </div>
            <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-[#176449] rounded-full" style={{ width: `${avgBrandCoverage}%` }} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 5. Score Combinado */}
      <Card className="border-[#dbe4df] bg-white shadow-xs hover:border-[#cbd8d1] transition-all">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs text-[#5a6e65] mb-1">
            <span>Score Combinado</span>
            <Award className="w-4 h-4 text-[#176449]" />
          </div>
          <div className="text-2xl font-bold text-[#111916]">
            {avgCombined}
            <span className="text-xs font-normal text-[#5a6e65]">/100</span>
          </div>
          <div className="text-[11px] text-[#5a6e65] mt-1">
            Média ponderada geral
          </div>
        </CardContent>
      </Card>

      {/* 6. Restrições do ML */}
      <Card className="border-[#dbe4df] bg-white shadow-xs hover:border-[#cbd8d1] transition-all">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs text-[#5a6e65] mb-1">
            <span>Restrição ML</span>
            <ShieldAlert className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-900">{restrictedPct}%</div>
          <div className="text-[11px] text-[#5a6e65] mt-1 flex items-center gap-1" title="Produtos de outros vendedores sem detalhamento público de preço/reviews pelo Mercado Livre">
            <span className="truncate">Restrito a ranking</span>
            <AlertCircle className="w-3 h-3 text-amber-600 shrink-0" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
