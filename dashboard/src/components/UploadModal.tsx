import React, { useState, useRef } from "react"
import { Upload, X, CheckCircle2, AlertCircle, FileSpreadsheet, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"

interface UploadModalProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

export const UploadModal: React.FC<UploadModalProps> = ({ open, onClose, onSuccess }) => {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<{ duplicate?: boolean; id?: string; error?: string } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  if (!open) return null

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => {
    setDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const selected = e.dataTransfer.files[0]
      if (selected.name.endsWith(".xlsx")) {
        setFile(selected)
        setResult(null)
      } else {
        setResult({ error: "Por favor selecione um arquivo de planilha no formato .xlsx" })
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = e.target.files[0]
      if (selected.name.endsWith(".xlsx")) {
        setFile(selected)
        setResult(null)
      } else {
        setResult({ error: "Por favor selecione um arquivo de planilha no formato .xlsx" })
      }
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setResult(null)

    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await fetch("/radar/api/upload", {
        method: "POST",
        body: formData,
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || "Erro ao processar arquivo.")
      }

      setResult({ duplicate: data.duplicate, id: data.id })
      if (!data.duplicate) {
        setTimeout(() => {
          onSuccess()
          onClose()
        }, 1500)
      }
    } catch (err: any) {
      setResult({ error: err.message || "Falha no envio do relatório." })
    } finally {
      setUploading(false)
    }
  }

  const resetAndClose = () => {
    setFile(null)
    setResult(null)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      <div className="bg-white dark:bg-[#0c1410] rounded-xl max-w-md w-full p-6 shadow-2xl border border-[#cbd8d1] dark:border-[#22362b] relative animate-in fade-in zoom-in-95 text-[#111916] dark:text-zinc-100">
        <button
          onClick={resetAndClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 dark:hover:text-zinc-200"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-[#e8f1ec] dark:bg-[#152e22] text-[#176449] dark:text-[#34d399] flex items-center justify-center">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-[#111916] dark:text-white">Importar Relatório XLSX</h3>
            <p className="text-xs text-[#5a6e65] dark:text-[#8ea398]">Alimente o radar com relatórios de coletas do Mercado Livre</p>
          </div>
        </div>

        {/* Results notification */}
        {result?.error && (
          <Alert variant="destructive" className="mb-4 text-xs py-2 bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/60 text-red-900 dark:text-red-200">
            <AlertCircle className="w-4 h-4" />
            <AlertTitle className="text-xs font-semibold">Não foi possível importar</AlertTitle>
            <AlertDescription className="text-xs">{result.error}</AlertDescription>
          </Alert>
        )}

        {result && !result.error && (
          <Alert className="mb-4 text-xs py-2 bg-emerald-50 dark:bg-[#11271d] border-emerald-200 dark:border-[#1f4232] text-emerald-900 dark:text-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <AlertTitle className="text-xs font-semibold">
              {result.duplicate ? "Relatório Já Existente" : "Coleta Importada com Sucesso!"}
            </AlertTitle>
            <AlertDescription className="text-xs text-emerald-800 dark:text-emerald-300">
              {result.duplicate
                ? `Esta coleta (ID: ${result.id}) já foi registrada e está disponível nos filtros.`
                : "Os dados foram integrados e os gráficos alimentados com os novos produtos."}
            </AlertDescription>
          </Alert>
        )}

        {/* Drop zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
            dragging
              ? "border-[#176449] dark:border-[#34d399] bg-emerald-50/50 dark:bg-emerald-950/30"
              : "border-[#cbd8d1] dark:border-[#22362b] hover:border-[#176449] dark:hover:border-[#34d399] bg-[#f8faf9] dark:bg-[#13201a]"
          }`}
        >
          <input
            type="file"
            ref={inputRef}
            onChange={handleFileChange}
            accept=".xlsx"
            className="hidden"
          />
          <FileSpreadsheet className="w-10 h-10 text-[#176449] dark:text-[#34d399] mx-auto mb-2 opacity-80" />
          <p className="text-xs font-medium text-[#111916] dark:text-zinc-100">
            {file ? file.name : "Clique para selecionar ou arraste o arquivo XLSX aqui"}
          </p>
          <p className="text-[11px] text-[#5a6e65] dark:text-[#8ea398] mt-1">
            Compatível com relatórios do Radar (máximo 10 MB)
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex items-center justify-end gap-2 mt-5">
          <Button
            variant="outline"
            size="sm"
            onClick={resetAndClose}
            className="text-xs border-[#cbd8d1] dark:border-[#22362b] dark:bg-[#13201a] dark:text-zinc-300"
          >
            Fechar
          </Button>
          <Button
            size="sm"
            onClick={handleUpload}
            disabled={!file || uploading}
            className="text-xs bg-[#176449] dark:bg-[#10b981] hover:bg-[#12523b] dark:hover:bg-[#059669] text-white"
          >
            {uploading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> Processando...
              </>
            ) : (
              <>
                <Upload className="w-3.5 h-3.5 mr-1.5" /> Enviar Relatório
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
