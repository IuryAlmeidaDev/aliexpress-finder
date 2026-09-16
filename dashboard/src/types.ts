export interface Product {
  id: string
  title: string
  category: string
  type: string
  rank: number | null
  price: number | null
  reviews: number | null
  rating: number | null
  demand: number | null
  demandCoverage: number | null
  brand: number | null
  brandCoverage: number | null
  combined: number | null
  demandEvidence: string
  brandEvidence: string
  counterpoints: string
  url: string
  priority: boolean
  key: string
}

export interface RunReport {
  id: string
  date: string
  status: string
  mode: string
  filename: string
  products: Product[]
}

export interface DashboardDataResponse {
  runs: RunReport[]
  skipped: number
}

export interface ProductHistoryPoint {
  runId: string
  date: string
  rank: number | null
  demand: number | null
  brand: number | null
  combined: number | null
  priority: boolean
}
