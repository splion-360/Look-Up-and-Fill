export interface PortfolioRow {
  id: number;
  name: string;
  symbol: string | null;  // null = missing ticker
  price: number;
  shares: number;
  marketValue: number;
  isEnriched?: boolean;   // for highlighting newly added data
  lookupStatus?: 'pending' | 'success' | 'failed' | 'not_started';
  failureReason?: string; // reason for failed lookup
}

export interface PortfolioData {
  rows: PortfolioRow[];
  totalRows: number;
  missingSymbols: number;
  fileName?: string;
}

export interface LookupProgress {
  current: number;
  total: number;
  isProcessing: boolean;
  completedRows: number[];
  failedRows: number[];
}