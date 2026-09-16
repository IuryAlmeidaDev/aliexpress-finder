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

export interface ArbitrageItem {
  source: string
  china_id: string
  china_title: string
  china_url: string
  china_fob_usd: number
  china_fob_brl: number
  moq: number
  supplier_name: string
  is_verified: boolean
  has_trade_assurance: boolean
  china_sales?: number | null
  china_rating?: number | null
  import_tax_unit_brl: number
  icms_unit_brl: number
  freight_unit_brl: number
  landed_cost_unit_brl: number
  ml_query: string
  ml_competitors_count: number
  ml_min_price: number
  ml_avg_price: number
  ml_max_price: number
  ml_full_share_pct: number
  ml_top_competitor_url: string
  ml_top_competitor_title: string
  ml_avg_rating?: number | null
  reference_sale_price_brl: number
  ml_fee_brl: number
  net_profit_brl: number
  net_margin_pct: number
  roi_pct: number
  strategy: string
  strategy_label: string
  summary: string
}

export interface ArbitrageReport {
  id?: string
  date?: string
  filename?: string
  query: string
  source: string
  usd_rate: number
  total_scanned: number
  blue_ocean_count: number
  high_margin_count: number
  private_label_count: number
  saturated_count: number
  items: ArbitrageItem[]
}
