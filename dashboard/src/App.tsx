import React, { useState, useEffect, useCallback } from "react"
import { Navbar } from "@/components/Navbar"
import { KpiRail } from "@/components/KpiRail"
import { OpportunityMatrix } from "@/components/OpportunityMatrix"
import { TrendChart } from "@/components/TrendChart"
import { CategoryChart } from "@/components/CategoryChart"
import { ProductTable } from "@/components/ProductTable"
import { ProductDrawer } from "@/components/ProductDrawer"
import { UploadModal } from "@/components/UploadModal"
import { AuthGate } from "@/components/AuthGate"
import { ArbitrageView } from "@/components/ArbitrageView"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { RunReport, Product, DashboardDataResponse, ArbitrageReport } from "@/types"
import { AlertCircle, RefreshCw, BarChart2, ScatterChart, Layers } from "lucide-react"

export const App: React.FC = () => {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null)
  const [activeTab, setActiveTab] = useState<"radar" | "arbitrage">("radar")
  const [runs, setRuns] = useState<RunReport[]>([])
  const [arbitrageScans, setArbitrageScans] = useState<ArbitrageReport[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string>("")
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>("")
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false)
  const [uploadOpen, setUploadOpen] = useState<boolean>(false)
  const [loading, setLoading] = useState<boolean>(true)
  const [refreshing, setRefreshing] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Check auth
  const checkSession = useCallback(async () => {
    try {
      const res = await fetch("/radar/api/session")
      if (res.ok) {
        const data = await res.json()
        setAuthenticated(data.authenticated)
        return data.authenticated
      }
      setAuthenticated(false)
      return false
    } catch {
      setAuthenticated(false)
      return false
    }
  }, [])

  // Fetch radar and arbitrage data
  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const [radarRes, arbRes] = await Promise.all([
        fetch("/radar/api/data"),
        fetch("/radar/api/arbitrage"),
      ])

      if (radarRes.status === 401) {
        setAuthenticated(false)
        return
      }
      if (!radarRes.ok) {
        throw new Error("Não foi possível carregar os dados do Radar.")
      }

      const data: DashboardDataResponse = await radarRes.json()
      setRuns(data.runs || [])

      if (arbRes.ok) {
        const arbData = await arbRes.json()
        setArbitrageScans(arbData.scans || [])
      }

      // Default select the latest run
      if (data.runs && data.runs.length > 0) {
        setSelectedRunId((prev) => {
          if (prev && data.runs.some((r) => r.id === prev)) return prev
          return data.runs[data.runs.length - 1].id
        })
      }
    } catch (err: any) {
      setError(err.message || "Erro desconhecido ao consultar os dados.")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    const init = async () => {
      const isAuth = await checkSession()
      if (isAuth) {
        await fetchData()
      } else {
        setLoading(false)
      }
    }
    init()
  }, [checkSession, fetchData])

  // Polling every 60 seconds
  useEffect(() => {
    if (!authenticated) return
    const interval = setInterval(() => {
      fetchData(true)
    }, 60000)
    return () => clearInterval(interval)
  }, [authenticated, fetchData])

  const handleLogout = async () => {
    try {
      await fetch("/radar/api/logout", { method: "POST" })
    } finally {
      setAuthenticated(false)
      setRuns([])
      setArbitrageScans([])
    }
  }

  const handleSelectProduct = (product: Product) => {
    setSelectedProduct(product)
    setDrawerOpen(true)
  }

  const handleCloseDrawer = () => {
    setDrawerOpen(false)
  }

  if (authenticated === false) {
    return (
      <AuthGate
        onSuccess={() => {
          setAuthenticated(true)
          fetchData()
        }}
      />
    )
  }

  const currentRun = runs.find((r) => r.id === selectedRunId) || runs[runs.length - 1]
  const currentProducts = currentRun ? currentRun.products : []

  return (
    <div className="min-h-screen bg-[#f8faf9] text-[#111916] pb-16">
      {/* Top Navbar */}
      <Navbar
        runs={runs}
        selectedRunId={selectedRunId}
        onSelectRun={setSelectedRunId}
        onOpenUpload={() => setUploadOpen(true)}
        onRefresh={() => fetchData(true)}
        onLogout={handleLogout}
        refreshing={refreshing}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 lg:px-8 pt-6 space-y-6">
        {/* Loading state */}
        {loading && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full rounded-xl bg-gray-200" />
              ))}
            </div>
            <Skeleton className="h-[360px] w-full rounded-xl bg-gray-200" />
            <Skeleton className="h-[300px] w-full rounded-xl bg-gray-200" />
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <Alert variant="destructive" className="bg-red-50 border-red-200 text-red-900">
            <AlertCircle className="w-4 h-4" />
            <AlertTitle className="font-semibold text-sm">Falha na conexão</AlertTitle>
            <AlertDescription className="text-xs flex items-center justify-between">
              <span>{error}</span>
              <Button
                variant="outline"
                size="xs"
                onClick={() => fetchData()}
                className="bg-white text-red-900 border-red-300"
              >
                Tentar novamente
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* TAB 1: RADAR MERCADO LIVRE */}
        {!loading && activeTab === "radar" && (
          <>
            {runs.length === 0 ? (
              <div className="bg-white border border-[#dbe4df] rounded-xl p-12 text-center max-w-lg mx-auto mt-12 shadow-sm">
                <div className="w-12 h-12 rounded-xl bg-[#e8f1ec] text-[#176449] flex items-center justify-center mx-auto mb-3">
                  <Layers className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-lg text-[#111916]">Nenhuma Coleta Disponível</h3>
                <p className="text-xs text-[#5a6e65] mt-1 mb-6">
                  Ainda não há relatórios XLSX registrados. Você pode importar uma planilha manualmente
                  ou aguardar o agendamento semanal do coletor no VPS.
                </p>
                <Button
                  onClick={() => setUploadOpen(true)}
                  className="bg-[#176449] hover:bg-[#12523b] text-white text-xs"
                >
                  Importar Primeiro Relatório XLSX
                </Button>
              </div>
            ) : (
              <>
                {/* 1. Executive KPIs */}
                <KpiRail products={currentProducts} runCount={runs.length} />

                {/* 2. Visual Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2">
                    <OpportunityMatrix
                      products={currentProducts}
                      onSelectProduct={handleSelectProduct}
                    />
                  </div>
                  <div className="lg:col-span-1 space-y-6">
                    <CategoryChart
                      products={currentProducts}
                      selectedCategory={selectedCategory}
                      onSelectCategory={setSelectedCategory}
                    />
                  </div>
                </div>

                {/* 3. Temporal Evolution / Distribution */}
                <TrendChart runs={runs} currentProducts={currentProducts} />

                {/* 4. Complete Filterable Table */}
                <ProductTable
                  products={currentProducts}
                  onSelectProduct={handleSelectProduct}
                  selectedCategory={selectedCategory}
                  onSelectCategory={setSelectedCategory}
                />
              </>
            )}
          </>
        )}

        {/* TAB 2: ARBITRAGEM CHINA × MERCADO LIVRE */}
        {!loading && activeTab === "arbitrage" && (
          <ArbitrageView initialScans={arbitrageScans} />
        )}
      </main>

      {/* Modals & Drawers */}
      <ProductDrawer
        product={selectedProduct}
        runs={runs}
        open={drawerOpen}
        onClose={handleCloseDrawer}
      />

      <UploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSuccess={() => {
          fetchData(true)
        }}
      />
    </div>
  )
}
