import React, { useState } from "react"
import { ShieldAlert, KeyRound, Eye, EyeOff, ArrowRight } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

interface AuthGateProps {
  onSuccess: () => void
}

export const AuthGate: React.FC<AuthGateProps> = ({ onSuccess }) => {
  const [key, setKey] = useState("")
  const [showKey, setShowKey] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!key.trim()) return

    setLoading(true)
    setError(null)

    try {
      const res = await fetch("/radar/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: key.trim() }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || "Chave de acesso inválida.")
      }

      onSuccess()
    } catch (err: any) {
      setError(err.message || "Erro ao conectar com o servidor.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#f8faf9] dark:bg-[#080d0a] transition-colors">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#176449] dark:bg-[#10b981] text-white mb-3 shadow-md">
            <KeyRound className="w-6 h-6 text-emerald-100 dark:text-[#062e20]" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[#111916] dark:text-white">Radar de Marcas</h1>
          <p className="text-sm text-[#5a6e65] dark:text-[#8ea398] mt-1">Inteligência de Mercado & Descoberta no Mercado Livre</p>
        </div>

        <Card className="border border-[#dbe4df] dark:border-[#1d2e26] shadow-sm bg-white dark:bg-[#0c1410]">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg text-[#111916] dark:text-white">Chave de Acesso</CardTitle>
            <CardDescription className="text-xs text-[#5a6e65] dark:text-[#8ea398]">
              Insira sua chave de acesso segura configurada no servidor (RADAR_DASHBOARD_KEY) para visualizar as estatísticas.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4 py-2 text-xs bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/60 text-red-900 dark:text-red-200">
                <ShieldAlert className="h-4 w-4" />
                <AlertTitle className="font-semibold text-xs">Falha de autenticação</AlertTitle>
                <AlertDescription className="text-xs">{error}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <Input
                  type={showKey ? "text" : "password"}
                  placeholder="Insira sua chave de acesso..."
                  value={key}
                  onChange={(e) => setKey(e.target.value)}
                  className="pr-10 text-sm h-10 border-[#cbd8d1] dark:border-[#22362b] dark:bg-[#13201a] dark:text-white focus:border-[#176449] dark:focus:border-[#10b981]"
                  autoFocus
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-zinc-200 transition-colors"
                  tabIndex={-1}
                >
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              <Button
                type="submit"
                disabled={loading || !key.trim()}
                className="w-full bg-[#176449] dark:bg-[#10b981] hover:bg-[#12523b] dark:hover:bg-[#059669] text-white font-medium h-10"
              >
                {loading ? (
                  "Autenticando..."
                ) : (
                  <span className="inline-flex items-center gap-2">
                    Acessar Radar <ArrowRight className="w-4 h-4" />
                  </span>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-[#5a6e65] dark:text-[#8ea398] mt-6">
          Ambiente protegido · Os relatórios XLSX são processados diretamente no servidor
        </p>
      </div>
    </div>
  )
}
