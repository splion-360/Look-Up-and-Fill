'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Paper from '@mui/material/Paper';
import LinearProgress from '@mui/material/LinearProgress';
import SearchIcon from '@mui/icons-material/Search';
import DownloadIcon from '@mui/icons-material/Download';
import ViewListIcon from '@mui/icons-material/ViewList';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PortfolioTable from '../../components/PortfolioTable';
import ToastProvider from '../../dashboard/components/ToastProvider';
import AppTheme from '../../shared-theme/AppTheme';
import { placeholderPortfolioData } from '../../data/placeholderData';
import { LookupProgress } from '../../types/portfolio';
import { usePortfolioSession } from '../../hooks/usePortfolioSession';
import { usePageTransition } from '../../hooks/usePageTransition';
import PageTransitionLoader from '../../components/PageTransitionLoader';

export default function PortfolioTablePage() {
  const { sessionData, isLoading, hasValidSession } = usePortfolioSession();
  const { navigate } = usePageTransition();
  const [isNavigating, setIsNavigating] = React.useState(false);
  const [portfolioData, setPortfolioData] = React.useState(placeholderPortfolioData.rows);
  const [viewMode, setViewMode] = React.useState<'all' | 'missing'>('all');
  const [lookupProgress, setLookupProgress] = React.useState<LookupProgress>({
    current: 0,
    total: 0,
    isProcessing: false,
    completedRows: [],
    failedRows: []
  });

  // Handle navigation with custom loading state
  const handleNavigation = (path: string) => {
    setIsNavigating(true);
    navigate(path);
  };

  // Redirect to upload page if no valid session
  React.useEffect(() => {
    if (!isLoading && !hasValidSession()) {
      navigate('/portfolio');
    }
  }, [isLoading, hasValidSession, navigate]);

  // Only show loader for session loading or when manually navigating away (Back to Home)
  if (isLoading) {
    return <PageTransitionLoader />;
  }

  // Show loader only when manually navigating away (Back to Home button)
  if (isNavigating) {
    return <PageTransitionLoader />;
  }

  if (!hasValidSession()) {
    return <PageTransitionLoader />;
  }

  const missingSymbolsCount = portfolioData.filter(row => !row.symbol).length;

  const handleViewModeChange = (event: React.MouseEvent<HTMLElement>, newViewMode: 'all' | 'missing') => {
    if (newViewMode !== null) {
      setViewMode(newViewMode);
    }
  };

  const handleLookupRow = async (rowId: number) => {
    const row = portfolioData.find(r => r.id === rowId);
    if (!row) return;

    // Update row status to pending
    setPortfolioData(prev => prev.map(r =>
      r.id === rowId ? { ...r, lookupStatus: 'pending' as const } : r
    ));

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));

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
        r.id === rowId ? {
          ...r,
          symbol,
          isEnriched: true,
          lookupStatus: 'success' as const
        } : r
      ));
    } else {
      // Mock failure reasons
      const failureReasons = [
        'Company not found in financial databases',
        'Multiple ticker matches found, manual review required',
        'Delisted or inactive company',
        'Insufficient company information provided',
        'API rate limit exceeded, try again later'
      ];
      const randomReason = failureReasons[Math.floor(Math.random() * failureReasons.length)];

      setPortfolioData(prev => prev.map(r =>
        r.id === rowId ? {
          ...r,
          lookupStatus: 'failed' as const,
          failureReason: randomReason
        } : r
      ));
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

    // Mock lookup process for all missing rows
    for (let i = 0; i < missingRows.length; i++) {
      const row = missingRows[i];

      // Update progress
      setLookupProgress(prev => ({
        ...prev,
        current: i + 1
      }));

      await handleLookupRow(row.id);
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
    <AppTheme>
      <ToastProvider>
        <Box
          sx={[
            {
              minHeight: '100vh',
              py: 4,
            },
            (theme) => ({
              '&::before': {
                content: '""',
                display: 'block',
                position: 'fixed',
                zIndex: -1,
                inset: 0,
                backgroundImage:
                  'radial-gradient(ellipse at 50% 50%, hsl(210, 100%, 97%), hsl(0, 0%, 100%))',
                backgroundRepeat: 'no-repeat',
                ...theme.applyStyles('dark', {
                  backgroundImage:
                    'radial-gradient(at 50% 50%, hsla(210, 100%, 16%, 0.5), hsl(220, 30%, 5%))',
                }),
              },
            }),
          ]}
        >
          <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
            <Stack spacing={5}>
              {/* Header */}
              <Box>
                <Button
                  startIcon={<ArrowBackIcon />}
                  onClick={() => handleNavigation('/')}
                  sx={{ mb: 2 }}
                >
                  Back to Home
                </Button>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography
                    variant="h3"
                    component="h1"
                    gutterBottom
                    sx={{ fontWeight: 'bold', color: 'primary.main', mb: 2 }}
                  >
                    Portfolio Data Analysis
                  </Typography>
                  <Typography variant="h6" sx={{ color: 'text.secondary', fontSize: '1.2rem' }}>
                    {sessionData?.fileName} • {portfolioData.length} rows total
                  </Typography>
                </Box>
              </Box>

              {/* Stats & Controls */}
              <Paper sx={{ p: 3 }}>
                <Stack spacing={3}>

                  <Stack direction="row" spacing={3} alignItems="center" justifyContent="space-between" flexWrap="wrap">
                    <ToggleButtonGroup
                      value={viewMode}
                      exclusive
                      onChange={handleViewModeChange}
                      size="medium"
                      sx={{
                        '& .MuiToggleButton-root': {
                          fontSize: '1rem',
                          py: 1.5,
                          px: 3,
                          fontWeight: 500,
                        }
                      }}
                    >
                      <ToggleButton value="all">
                        <ViewListIcon sx={{ mr: 1.5 }} />
                        All Rows ({portfolioData.length})
                      </ToggleButton>
                      <ToggleButton value="missing">
                        <VisibilityOffIcon sx={{ mr: 1.5 }} />
                        Missing ({missingSymbolsCount})
                      </ToggleButton>
                    </ToggleButtonGroup>

                    <Stack direction="row" spacing={3}>
                      <Button
                        variant="contained"
                        size="large"
                        startIcon={<SearchIcon />}
                        onClick={handleLookupMissing}
                        disabled={missingSymbolsCount === 0 || lookupProgress.isProcessing}
                        sx={{
                          fontSize: '1rem',
                          py: 1.5,
                          px: 3,
                          fontWeight: 600,
                          '&.Mui-disabled': {
                            backgroundColor: 'grey.400',
                            color: 'grey.600',
                          }
                        }}
                      >
                        {lookupProgress.isProcessing
                          ? `Looking up... (${lookupProgress.current}/${lookupProgress.total})`
                          : `Lookup All (${missingSymbolsCount})`
                        }
                      </Button>
                      <Button
                        variant="outlined"
                        size="large"
                        startIcon={<DownloadIcon />}
                        onClick={handleDownload}
                        sx={{
                          fontSize: '1rem',
                          py: 1.5,
                          px: 3,
                          fontWeight: 600,
                        }}
                      >
                        Download CSV
                      </Button>
                    </Stack>
                  </Stack>

                  {/* Progress Bar */}
                  {lookupProgress.isProcessing && (
                    <Box>
                      <Typography variant="body1" gutterBottom sx={{ fontSize: '1rem', fontWeight: 500 }}>
                        Processing {lookupProgress.current} of {lookupProgress.total} companies...
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={(lookupProgress.current / lookupProgress.total) * 100}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                  )}
                </Stack>
              </Paper>

              {/* Data Table */}
              <Paper sx={{ p: 3, borderRadius: 3, boxShadow: 3 }}>
                <PortfolioTable data={portfolioData} viewMode={viewMode} onLookupRow={handleLookupRow} />
              </Paper>
            </Stack>
          </Container>
        </Box>
      </ToastProvider>
    </AppTheme>
  );
}