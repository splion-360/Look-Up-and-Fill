import { PortfolioData } from '../types/portfolio';

export const placeholderPortfolioData: PortfolioData = {
  rows: [
    {
      id: 1,
      name: "Apple Inc.",
      symbol: "AAPL",
      price: 189.89,
      shares: 10,
      marketValue: 1898.90,
      lookupStatus: 'not_started'
    },
    {
      id: 2,
      name: "Microsoft Corporation",
      symbol: null,
      price: 326.12,
      shares: 5,
      marketValue: 1630.60,
      lookupStatus: 'not_started'
    },
    {
      id: 3,
      name: "Berkshire Hathaway Inc. Class B",
      symbol: null,
      price: 362.55,
      shares: 2,
      marketValue: 725.10,
      lookupStatus: 'not_started'
    },
    {
      id: 4,
      name: "Amazon.com Inc.",
      symbol: "AMZN",
      price: 130.25,
      shares: 8,
      marketValue: 1042.00,
      lookupStatus: 'not_started'
    },
    {
      id: 5,
      name: "Alphabet Inc. Class A",
      symbol: null,
      price: 139.14,
      shares: 6,
      marketValue: 834.84,
      lookupStatus: 'not_started'
    },
    {
      id: 6,
      name: "Tesla Inc",
      symbol: null,
      price: 255.25,
      shares: 3,
      marketValue: 765.75,
      lookupStatus: 'not_started'
    },
    {
      id: 7,
      name: "NVIDIA Corporation",
      symbol: "NVDA",
      price: 470.11,
      shares: 4,
      marketValue: 1880.44,
      lookupStatus: 'not_started'
    },
    {
      id: 8,
      name: "Unknown Tech Co",
      symbol: null,
      price: 12.00,
      shares: 100,
      marketValue: 1200.00,
      lookupStatus: 'not_started'
    }
  ],
  totalRows: 8,
  missingSymbols: 5,
  fileName: "sample_portfolio.csv"
};