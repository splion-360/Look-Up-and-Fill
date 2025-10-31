'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Paper from '@mui/material/Paper';
import LinearProgress from '@mui/material/LinearProgress';
import SearchIcon from '@mui/icons-material/Search';
import DownloadIcon from '@mui/icons-material/Download';
import ViewListIcon from '@mui/icons-material/ViewList';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import PortfolioTable from './PortfolioTable';
import { placeholderPortfolioData } from '../data/placeholderData';
import { PortfolioRow, LookupProgress } from '../types/portfolio';

export default function PortfolioTableView() {
  const [portfolioData, setPortfolioData] = React.useState(placeholderPortfolioData.rows);
  const [viewMode, setViewMode] = React.useState<'all' | 'missing'>('all');
  const [lookupProgress, setLookupProgress] = React.useState<LookupProgress>({
    current: 0,
    total: 0,
    isProcessing: false,
    completedRows: [],
    failedRows: []
  });

  const missingSymbolsCount = portfolioData.filter(row => !row.symbol).length;
  const enrichedCount = portfolioData.filter(row => row.isEnriched).length;

  const handleViewModeChange = (event: React.MouseEvent<HTMLElement>, newViewMode: 'all' | 'missing') => {
    if (newViewMode !== null) {
      setViewMode(newViewMode);
    }
  };

  const handleLookupMissing = async () => {
    const missingRows = portfolioData.filter(row => !row.symbol);
    
    if (missingRows.length === 0) {
      return;
    }

    setLookupProgress({
      current: 0,
      total: missingRows.length,
      isProcessing: true,
      completedRows: [],
      failedRows: []
    });

    // Mock lookup process
    for (let i = 0; i < missingRows.length; i++) {
      const row = missingRows[i];
      
      // Update progress
      setLookupProgress(prev => ({
        ...prev,
        current: i + 1
      }));

      // Update row status to pending
      setPortfolioData(prev => prev.map(r => 
        r.id === row.id ? { ...r, lookupStatus: 'pending' as const } : r
      ));

      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 800));

      // Mock success/failure (80% success rate)
      const isSuccess = Math.random() > 0.2;
      
      if (isSuccess) {
        // Mock ticker symbols
        const mockSymbols: { [key: string]: string } = {
          'Microsoft Corporation': 'MSFT',
          'Berkshire Hathaway Inc. Class B': 'BRK.B',
          'Alphabet Inc. Class A': 'GOOGL',
          'Tesla Inc': 'TSLA',
          'Unknown Tech Co': 'UNK'
        };
        
        const symbol = mockSymbols[row.name] || 'UNK';
        
        setPortfolioData(prev => prev.map(r => 
          r.id === row.id ? { 
            ...r, 
            symbol, 
            isEnriched: true, 
            lookupStatus: 'success' as const 
          } : r
        ));

        setLookupProgress(prev => ({
          ...prev,
          completedRows: [...prev.completedRows, row.id]
        }));
      } else {
        setPortfolioData(prev => prev.map(r => 
          r.id === row.id ? { ...r, lookupStatus: 'failed' as const } : r
        ));

        setLookupProgress(prev => ({
          ...prev,
          failedRows: [...prev.failedRows, row.id]
        }));
      }
    }

    // Complete the process
    setLookupProgress(prev => ({
      ...prev,
      isProcessing: false
    }));
  };

  const handleDownload = () => {
    // Mock download - in real app this would call backend API
    const csvContent = [
      'Name,Symbol,Price,# of Shares,Market Value',
      ...portfolioData.map(row => 
        `"${row.name}","${row.symbol || ''}",${row.price},${row.shares},${row.marketValue}`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'enriched_portfolio.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={4}>
        {/* Header */}
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
            Portfolio Data
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {placeholderPortfolioData.fileName} • {portfolioData.length} rows total
          </Typography>
        </Box>

        {/* Stats & Controls */}
        <Paper sx={{ p: 3 }}>
          <Stack spacing={3}>
            <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
              <Chip 
                label={`${portfolioData.length} Total Rows`} 
                color="primary" 
                variant="outlined" 
              />
              <Chip 
                label={`${missingSymbolsCount} Missing Symbols`} 
                color={missingSymbolsCount > 0 ? 'warning' : 'success'} 
              />
              {enrichedCount > 0 && (
                <Chip 
                  label={`${enrichedCount} Enriched`} 
                  color="success" 
                />
              )}
            </Stack>

            <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between" flexWrap="wrap">
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={handleViewModeChange}
                size="small"
              >
                <ToggleButton value="all">
                  <ViewListIcon sx={{ mr: 1 }} />
                  All Rows ({portfolioData.length})
                </ToggleButton>
                <ToggleButton value="missing">
                  <VisibilityOffIcon sx={{ mr: 1 }} />
                  Missing Only ({missingSymbolsCount})
                </ToggleButton>
              </ToggleButtonGroup>

              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  startIcon={<SearchIcon />}
                  onClick={handleLookupMissing}
                  disabled={missingSymbolsCount === 0 || lookupProgress.isProcessing}
                >
                  {lookupProgress.isProcessing 
                    ? `Looking up... (${lookupProgress.current}/${lookupProgress.total})`
                    : `Lookup Missing (${missingSymbolsCount})`
                  }
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownload}
                >
                  Download CSV
                </Button>
              </Stack>
            </Stack>

            {/* Progress Bar */}
            {lookupProgress.isProcessing && (
              <Box>
                <Typography variant="body2" gutterBottom>
                  Processing {lookupProgress.current} of {lookupProgress.total} companies...
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(lookupProgress.current / lookupProgress.total) * 100}
                />
              </Box>
            )}
          </Stack>
        </Paper>

        {/* Data Table */}
        <Paper sx={{ p: 2 }}>
          <PortfolioTable data={portfolioData} viewMode={viewMode} />
        </Paper>
      </Stack>
    </Box>
  );
}