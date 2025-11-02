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
import InfinityLoader from '../../dashboard/components/InfinityLoader';
import SearchIcon from '@mui/icons-material/Search';
import DownloadIcon from '@mui/icons-material/Download';
import ViewListIcon from '@mui/icons-material/ViewList';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PortfolioTable from '../../components/PortfolioTable';
import ToastProvider from '../../dashboard/components/ToastProvider';
import toast from 'react-hot-toast';
import AppTheme from '../../shared-theme/AppTheme';
import { PortfolioRow } from '../../types/portfolio';
import { usePortfolioSession } from '../../hooks/usePortfolioSession';
import { usePageTransition } from '../../hooks/usePageTransition';
import PageTransitionLoader from '../../components/PageTransitionLoader';

export default function PortfolioTablePage() {
  const { sessionData, isLoading, hasValidSession } = usePortfolioSession();
  const { navigate } = usePageTransition();
  const [isNavigating, setIsNavigating] = React.useState(false);
  const [portfolioData, setPortfolioData] = React.useState<PortfolioRow[]>([]);
  const [dataLoaded, setDataLoaded] = React.useState(false);
  const [viewMode, setViewMode] = React.useState<'all' | 'missing'>('all');
  const [isProcessing, setIsProcessing] = React.useState(false);

  // Handle navigation with custom loading state
  const handleNavigation = (path: string) => {
    setIsNavigating(true);
    navigate(path);
  };

  React.useEffect(() => {
    if (sessionData && sessionData.csvData && !dataLoaded) {
      const portfolioRows = sessionData.csvData.map((row: any, index: number) => {
        const price = parseFloat(row.price) || null;
        const shares = parseInt(row.shares) || null;
        const market = parseFloat(row.market) || null;

        return {
          id: index + 1,
          name: row.name || row.Name || null,
          symbol: row.symbol || row.Symbol || null,
          price,
          shares,
          market,
          lookupStatus: 'not_started' as const
        };
      });

      setPortfolioData(portfolioRows);
      setDataLoaded(true);
    }
  }, [sessionData, dataLoaded]);

  // Redirect to upload page if no valid session
  React.useEffect(() => {
    if (!isLoading && !hasValidSession()) {
      navigate('/portfolio');
    }
  }, [isLoading, hasValidSession, navigate]);


  if (isLoading) {
    return <PageTransitionLoader />;
  }

  if (isNavigating) {
    return <PageTransitionLoader />;
  }

  if (!hasValidSession()) {
    return <PageTransitionLoader />;
  }

  const missingSymbolsCount = portfolioData.filter((row: PortfolioRow) => !row.symbol || !row.name).length;

  const handleViewModeChange = (event: React.MouseEvent<HTMLElement>, newViewMode: 'all' | 'missing') => {
    if (newViewMode !== null) {
      setViewMode(newViewMode);
    }
  };

  const handleLookupRow = async (rowId: number) => {
    const row = portfolioData.find(r => r.id === rowId);
    if (!row) return;

    setPortfolioData(prev => prev.map(r =>
      r.id === rowId ? { ...r, lookupStatus: 'pending' as const } : r
    ));

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/documents/lookup/single`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: [row] }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 429) {
          toast.error('Rate limit exceeded. Please wait before trying again.');
          setPortfolioData(prev => prev.map(r =>
            r.id === rowId ? { ...r, lookupStatus: 'failed' as const, failureReason: 'Rate limit exceeded' } : r
          ));
          return;
        }
        throw new Error(errorData.detail || 'Lookup failed');
      }

      const result = await response.json();
      const enrichedRow = result.data[0]; // Get the first (and only) enriched row
      setPortfolioData(prev => prev.map(r =>
        r.id === rowId ? { ...r, ...enrichedRow } : r
      ));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Lookup service unavailable';
      
      if (errorMessage.includes('Rate limit exceeded') || errorMessage.includes('429')) {
        toast.error('Rate limit exceeded. Please wait before trying again.');
      } else {
        toast.error(`Single lookup failed: ${errorMessage}`);
      }
      
      setPortfolioData(prev => prev.map(r =>
        r.id === rowId ? { ...r, lookupStatus: 'failed' as const, failureReason: errorMessage } : r
      ));
    }
  };

  const handleLookupMissing = async () => {
    const missingRows = portfolioData.filter((row: PortfolioRow) => !row.symbol || !row.name);

    if (missingRows.length === 0) {
      return;
    }

    setIsProcessing(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/documents/lookup/full`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: portfolioData }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 429) {
          toast.error('Rate limit exceeded. Please wait before trying again.');
          return;
        }
        throw new Error(errorData.detail || 'Lookup failed');
      }

      const result = await response.json();
      setPortfolioData(result.data);
    } catch (error) {
      console.error('Lookup failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'Lookup service unavailable';

      if (errorMessage.includes('Rate limit exceeded') || errorMessage.includes('429')) {
        toast.error('Rate limit exceeded. Please wait before trying again.');
      } else {
        toast.error(`Lookup failed: ${errorMessage}`);
      }

      setPortfolioData(prev => prev.map(r => {
        const isMissing = !r.symbol || !r.name;
        return isMissing ? { ...r, lookupStatus: 'failed' as const, failureReason: errorMessage } : r;
      }));
    }

    setIsProcessing(false);
  };

  const handleDownload = () => {
    const csvContent = [
      'Name,Symbol,Price,# of Shares,Market Value',
      ...portfolioData.map((row: PortfolioRow) => `"${row.name}","${row.symbol || ''}",${row.price},${row.shares},${row.market}`)
    ].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    const originalFileName = sessionData?.fileName || 'portfolio.csv';
    const fileNameWithoutExtension = originalFileName.replace(/\.csv$/i, '');
    a.download = `${fileNameWithoutExtension}_filled.csv`;
    
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
                    Document View
                  </Typography>
                  <Typography variant="h6" sx={{ color: 'text.secondary', fontSize: '1.2rem' }}>
                    {sessionData?.fileName} • {sessionData?.totalRows || portfolioData.length} rows total
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
                        disabled={missingSymbolsCount === 0 || isProcessing}
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
                        {isProcessing ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <InfinityLoader size={20} />
                            Looking up...
                          </Box>
                        ) : (
                          `Lookup All (${missingSymbolsCount})`
                        )}
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