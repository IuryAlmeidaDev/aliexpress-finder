import React from "react"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Product, RunReport } from "@/types"
import {
  ExternalLink,
  Award,
  TrendingUp,
  Sparkles,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  History,
  Tag,
  ShoppingBag,
} from "lucide-react"

interface ProductDrawerProps {
  product: Product | null
  runs: RunReport[]
  open: boolean
  onClose: () => void
}

export const ProductDrawer: React.FC<ProductDrawerProps> = ({
  product,
  runs,
  open,
  onClose,
}) => {
  if (!product) return null

  // Parse evidence lists (separated by '|')
  const parseList = (text?: string) => {
    if (!text) return []
    return text
      .split("|")
      .map((s) => s.trim())
      .filter(Boolean)
  }

  const demandItems = parseList(product.demandEvidence)
  const brandItems = parseList(product.brandEvidence)
  const counterpointItems = parseList(product.counterpoints)

  // Find product occurrences across all runs
  const productHistory = runs
    .map((run) => {
      const match = run.products.find((p) => p.key === product.key)
      if (!match) return null
      return {
        runId: run.id,
        date: run.date,
        rank: match.rank,
        demand: match.demand,
        brand: match.brand,
        combined: match.combined,
        priority: match.priority,
      }
    })
    .filter(Boolean)

  const formatDate = (isoString: string) => {
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

  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto p-6 bg-white">
        <SheetHeader className="pb-4 border-b border-[#dbe4df] text-left">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`inline-flex items-center justify-center px-2 py-0.5 rounded text-xs font-bold ${
                product.rank === 1
                  ? "bg-amber-400 text-amber-950"
                  : product.rank === 2
                  ? "bg-slate-300 text-slate-900"
                  : product.rank === 3
                  ? "bg-amber-700 text-amber-50"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              Rank #{product.rank ?? "?"}
            </span>
            <Badge variant="outline" className="text-xs bg-[#f0f4f2] text-gray-800 border-gray-200">
              {product.category || "Geral"}
            </Badge>
            <Badge variant="outline" className="text-[10px] font-mono text-gray-600">
              {product.type}
            </Badge>
          </div>

          <SheetTitle className="text-base font-bold text-[#111916] leading-snug">
            {product.title}
          </SheetTitle>

          <SheetDescription className="text-xs text-[#5a6e65] flex items-center justify-between gap-2 pt-1">
            <span className="font-mono">ID: {product.id}</span>
            {product.url ? (
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[#176449] hover:underline font-medium"
              >
                Ver no Mercado Livre <ExternalLink className="w-3 h-3" />
              </a>
            ) : (
              <span className="text-amber-700 flex items-center gap-1 text-[11px]">
                <ShieldAlert className="w-3 h-3" /> Link direto restrito pelo ML
              </span>
            )}
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 pt-4 text-xs">
          {/* Status Alert Banner */}
          {product.priority ? (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900 flex items-start gap-2">
              <Award className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Oportunidade Promovida!</span>
                <p className="text-[11px] text-emerald-800 mt-0.5">
                  Crescimento de demanda e viabilidade de marca própria confirmados.
                </p>
              </div>
            </div>
          ) : (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 flex items-start gap-2">
              <History className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Em Investigação (Linha de Base)</span>
                <p className="text-[11px] text-amber-800 mt-0.5">
                  Produto registrado na linha de base. As próximas coletas semanais verificarão
                  o crescimento contínuo para promover a oportunidade.
                </p>
              </div>
            </div>
          )}

          {/* Key Metrics Trio */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-[#f8faf9] p-3 rounded-lg border border-[#e2ede7] text-center">
              <div className="text-[11px] text-[#5a6e65] mb-0.5">Demanda</div>
              <div className="text-xl font-bold text-blue-700">{product.demand ?? 0}</div>
              <div className="text-[10px] text-[#5a6e65] mt-0.5">
                Cob: <strong>{product.demandCoverage ?? 0}%</strong>
              </div>
            </div>

            <div className="bg-[#f8faf9] p-3 rounded-lg border border-[#e2ede7] text-center">
              <div className="text-[11px] text-[#5a6e65] mb-0.5">Potencial Marca</div>
              <div className="text-xl font-bold text-[#176449]">{product.brand ?? 0}</div>
              <div className="text-[10px] text-[#5a6e65] mt-0.5">
                Cob: <strong>{product.brandCoverage ?? 0}%</strong>
              </div>
            </div>

            <div className="bg-[#f8faf9] p-3 rounded-lg border border-[#e2ede7] text-center">
              <div className="text-[11px] text-[#5a6e65] mb-0.5">Score Combinado</div>
              <div className="text-xl font-bold text-purple-700">{product.combined ?? 0}</div>
              <div className="text-[10px] text-purple-600 mt-0.5 font-medium">Prioridade</div>
            </div>
          </div>

          {/* Preço & Avaliações (quando disponíveis) */}
          <div className="p-3 bg-white rounded-lg border border-[#dbe4df] flex items-center justify-between">
            <div>
              <span className="text-gray-500 text-[11px]">Preço Observado</span>
              <div className="font-semibold text-sm text-[#111916]">
                {product.price !== null ? `R$ ${product.price.toFixed(2)}` : "Restrito a ranking"}
              </div>
            </div>
            <div>
              <span className="text-gray-500 text-[11px]">Avaliações</span>
              <div className="font-semibold text-sm text-[#111916]">
                {product.reviews !== null ? `${product.reviews} avaliações` : "Não público"}
              </div>
            </div>
            <div>
              <span className="text-gray-500 text-[11px]">Nota Média</span>
              <div className="font-semibold text-sm text-[#111916]">
                {product.rating !== null ? `★ ${product.rating.toFixed(1)}` : "N/D"}
              </div>
            </div>
          </div>

          {/* Section 1: Evidências de Demanda */}
          <div>
            <h4 className="font-semibold text-xs text-[#111916] uppercase tracking-wider flex items-center gap-1.5 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-blue-600" /> Evidências de Demanda
            </h4>
            {demandItems.length > 0 ? (
              <ul className="space-y-1.5">
                {demandItems.map((item, idx) => (
                  <li
                    key={idx}
                    className="p-2 bg-blue-50/50 rounded border border-blue-100 flex items-start gap-2 text-[11px] text-blue-950"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400 italic">Sem evidências textuais registradas.</p>
            )}
          </div>

          {/* Section 2: Hipóteses de Diferenciação de Marca */}
          <div>
            <h4 className="font-semibold text-xs text-[#111916] uppercase tracking-wider flex items-center gap-1.5 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-[#176449]" /> Hipóteses de Diferenciação de Marca
            </h4>
            {brandItems.length > 0 ? (
              <ul className="space-y-1.5">
                {brandItems.map((item, idx) => (
                  <li
                    key={idx}
                    className="p-2 bg-emerald-50/50 rounded border border-emerald-100 flex items-start gap-2 text-[11px] text-emerald-950"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#176449] shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400 italic">Sem hipóteses registradas.</p>
            )}
          </div>

          {/* Section 3: Contrapontos e Riscos */}
          <div>
            <h4 className="font-semibold text-xs text-[#111916] uppercase tracking-wider flex items-center gap-1.5 mb-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> Contrapontos e Riscos Concorrenciais
            </h4>
            {counterpointItems.length > 0 ? (
              <ul className="space-y-1.5">
                {counterpointItems.map((item, idx) => (
                  <li
                    key={idx}
                    className="p-2 bg-amber-50/50 rounded border border-amber-100 flex items-start gap-2 text-[11px] text-amber-950"
                  >
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400 italic">Nenhum contraponto impeditivo identificado.</p>
            )}
          </div>

          {/* Section 4: Histórico de Coletas */}
          {productHistory.length > 0 && (
            <div className="pt-2 border-t border-gray-100">
              <h4 className="font-semibold text-xs text-[#111916] uppercase tracking-wider flex items-center gap-1.5 mb-2">
                <History className="w-3.5 h-3.5 text-[#5a6e65]" /> Histórico deste Produto nas Coletas
              </h4>
              <div className="space-y-1.5">
                {productHistory.map((h: any, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-200 text-[11px]"
                  >
                    <span className="text-gray-600">{formatDate(h.date)}</span>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-[#111916]">Rank #{h.rank ?? "?"}</span>
                      <span className="text-blue-700 font-medium">Dem: {h.demand ?? 0}</span>
                      <span className="text-[#176449] font-medium">Marca: {h.brand ?? 0}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
