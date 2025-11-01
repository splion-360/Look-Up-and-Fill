export interface PortfolioRow {
  id: number;
  name: string | null;
  symbol: string | null;
  price: number | null;
  shares: number | null;
  market: number | null;
  isEnriched?: boolean;
  lookupStatus?: 'pending' | 'success' | 'failed' | 'not_started';
  failureReason?: string;
}

export interface PortfolioData {
  rows: PortfolioRow[];
  totalRows: number;
  missingSymbols: number;
  fileName?: string;
}

