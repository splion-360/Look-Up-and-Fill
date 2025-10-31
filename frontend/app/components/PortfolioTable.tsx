'use client';

import * as React from 'react';
import { DataGrid, GridColDef, GridRenderCellParams, GridRowParams } from '@mui/x-data-grid';
import { PortfolioRow } from '../types/portfolio';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';

import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Tooltip from '@mui/material/Tooltip';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import SearchIcon from '@mui/icons-material/Search';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import RefreshIcon from '@mui/icons-material/Refresh';

import Button from '@mui/material/Button';

interface PortfolioTableProps {
  data: PortfolioRow[];
  viewMode: 'all' | 'missing';
  onLookupRow?: (rowId: number) => void;
}

export default function PortfolioTable({ data, viewMode, onLookupRow }: PortfolioTableProps) {
  const [expandedRows, setExpandedRows] = React.useState<Set<number>>(new Set());
  const [paginationModel, setPaginationModel] = React.useState({ page: 0, pageSize: 10 });

  // Cache filtered data to prevent jitter when switching views
  const [cachedData, setCachedData] = React.useState<{
    all: PortfolioRow[];
    missing: PortfolioRow[];
  }>({ all: [], missing: [] });

  // Update cache when data changes
  React.useEffect(() => {
    setCachedData({
      all: data,
      missing: data.filter(row => !row.symbol || !row.name)
    });
  }, [data]);

  // Use cached data for filtering to prevent jitter
  const filteredData = React.useMemo(() => {
    return viewMode === 'missing' ? cachedData.missing : cachedData.all;
  }, [viewMode, cachedData]);

  // Reset pagination to first page when view mode changes
  React.useEffect(() => {
    setPaginationModel(prev => ({ ...prev, page: 0 }));
  }, [viewMode]);

  const toggleRowExpansion = (rowId: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(rowId)) {
      newExpanded.delete(rowId);
    } else {
      newExpanded.add(rowId);
    }
    setExpandedRows(newExpanded);
  };

  const renderStatusCell = (params: GridRenderCellParams) => {
    const status = params.row.lookupStatus;
    const isEnriched = params.row.isEnriched;
    const failureReason = params.row.failureReason;
    const rowId = params.row.id;
    const isExpanded = expandedRows.has(rowId);
    const hasMissingSymbol = !params.row.symbol;
    const hasMissingName = !params.row.name;

    if (params.row.symbol && params.row.name && !isEnriched) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
          <Chip
            icon={<CheckCircleIcon sx={{ color: 'black' }} />}
            label="Complete"
            color="primary"
            size="small"
            sx={{
              fontSize: '0.75rem',
              height: 28,
              color: 'black',
              '& .MuiChip-label': {
                color: 'black',
              },
            }}
          />
        </Box>
      );
    }


    if (status === 'success' || isEnriched) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
          <Chip
            icon={<CheckCircleIcon />}
            label="Found"
            color="success"
            size="small"
            sx={{ fontSize: '0.75rem', height: 28 }}
          />
        </Box>
      );
    }

    // Not Found - lookup failed (RED)
    if (status === 'failed') {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, width: '100%' }}>
          <Tooltip title="Click for more details" arrow>
            <Chip
              icon={<ErrorIcon />}
              label="Not Found"
              color="error"
              size="small"
              onClick={failureReason ? () => toggleRowExpansion(rowId) : undefined}
              sx={{
                fontSize: '0.75rem',
                height: 28,
                cursor: failureReason ? 'pointer' : 'default',
                '&:hover': failureReason ? {
                  backgroundColor: 'error.dark',
                } : {},
              }}
            />
          </Tooltip>
        </Box>
      );
    }

    // Looking up - currently being processed
    if (status === 'pending') {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
          <Chip
            icon={<HourglassEmptyIcon />}
            label="Looking up..."
            color="info"
            size="small"
            sx={{ fontSize: '0.75rem', height: 28 }}
          />
        </Box>
      );
    }

    // Missing - no symbol or name, can be looked up (GREY)
    if (hasMissingSymbol || hasMissingName) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
          <Tooltip title="Click to lookup symbol" arrow>
            <Chip
              icon={<SearchIcon />}
              label="Missing"
              color="default"
              size="small"
              variant="outlined"
              onClick={() => onLookupRow?.(rowId)}
              sx={{
                fontSize: '0.75rem',
                height: 28,
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: 'action.hover',
                  borderColor: 'text.secondary',
                },
              }}
            />
          </Tooltip>
        </Box>
      );
    }

    // Default case (should not occur with new logic)
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
        <Chip
          icon={<RemoveCircleIcon />}
          label="Unknown"
          color="default"
          size="small"
          variant="outlined"
          sx={{ fontSize: '0.75rem', height: 28 }}
        />
      </Box>
    );
  };

  const renderSymbolCell = (params: GridRenderCellParams) => {
    const symbol = params.value;
    const isEnriched = params.row.isEnriched;

    if (!symbol) {
      return (
        <Typography sx={{ color: 'text.secondary', fontStyle: 'italic', fontSize: '0.875rem' }}>
          —
        </Typography>
      );
    }

    return (
      <Typography
        sx={{
          fontWeight: isEnriched ? 600 : 500,
          color: isEnriched ? 'primary.main' : 'text.primary',
          bgcolor: isEnriched ? 'primary.50' : 'transparent',
          px: isEnriched ? 1 : 0,
          py: isEnriched ? 0.25 : 0,
          borderRadius: isEnriched ? 1 : 0,
          fontSize: '0.875rem',
        }}
      >
        {symbol}
      </Typography>
    );
  };

  const renderNameCell = (params: GridRenderCellParams) => {
    const status = params.row.lookupStatus;
    const rowId = params.row.id;
    const showRetry = status === 'failed';

    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
        <Typography sx={{ fontSize: '0.875rem', fontWeight: 500, flex: 1 }}>
          {params.value || '-'}
        </Typography>
        {showRetry && (
          <Tooltip title="Retry lookup" arrow>
            <Button
              size="small"
              variant="outlined"
              onClick={() => onLookupRow?.(rowId)}
              sx={{
                minWidth: 'auto',
                px: 1,
                py: 0.25,
                fontSize: '0.7rem',
                height: 24,
              }}
              startIcon={<RefreshIcon sx={{ fontSize: '0.8rem' }} />}
            >
              Retry
            </Button>
          </Tooltip>
        )}
      </Box>
    );
  };

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Company Name',
      flex: 2,
      minWidth: 200,
      renderCell: renderNameCell,
      sortable: false,
    },
    {
      field: 'symbol',
      headerName: 'Symbol',
      width: 120,
      renderCell: renderSymbolCell,
      sortable: false,
    },
    {
      field: 'price',
      headerName: 'Price',
      width: 100,
      type: 'number',
      renderCell: (params) => (
        <Typography sx={{
          fontSize: '0.875rem',
          fontWeight: 500,
          color: params.value === null ? 'text.disabled' : 'inherit'
        }}>
          {params.value !== null ? `$${params.value.toFixed(2)}` : 'N/A'}
        </Typography>
      ),
      sortable: false,
    },
    {
      field: 'shares',
      headerName: 'Shares',
      width: 100,
      type: 'number',
      renderCell: (params) => (
        <Typography sx={{
          fontSize: '0.875rem',
          fontWeight: 500,
          color: params.value === null ? 'text.disabled' : 'inherit'
        }}>
          {params.value !== null ? params.value.toLocaleString() : 'N/A'}
        </Typography>
      ),
      sortable: false,
    },
    {
      field: 'market',
      headerName: 'Market Value',
      width: 140,
      type: 'number',
      renderCell: (params) => (
        <Typography sx={{
          fontSize: '0.875rem',
          fontWeight: 600,
          color: params.value === null ? 'text.disabled' : 'success.main'
        }}>
          {params.value !== null ? `$${params.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A'}
        </Typography>
      ),
      sortable: false,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 160,
      renderCell: renderStatusCell,
      sortable: false,
      headerAlign: 'center',
      align: 'center',
    },
  ];

  const getDetailPanelContent = React.useCallback(
    ({ row }: GridRowParams) => {
      if (row.lookupStatus === 'failed' && row.failureReason) {
        return (
          <Box sx={{ p: 2 }}>
            <Alert severity="error" sx={{ fontSize: '0.95rem' }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                Lookup Failed:
              </Typography>
              <Typography variant="body2">
                {row.failureReason}
              </Typography>
            </Alert>
          </Box>
        );
      }
      return null;
    },
    []
  );

  return (
    <Box sx={{ width: '100%' }}>
      <DataGrid
        rows={filteredData}
        columns={columns}
        getRowClassName={(params) => {
          const isEnriched = params.row.isEnriched;
          const baseClass = params.indexRelativeToCurrentPage % 2 === 0 ? 'even' : 'odd';
          return isEnriched ? `${baseClass} enriched-row` : baseClass;
        }}
        paginationModel={paginationModel}
        onPaginationModelChange={setPaginationModel}
        pageSizeOptions={[10]}
        rowHeight={48}
        getDetailPanelContent={getDetailPanelContent}
        isRowSelectable={() => false}
        disableColumnResize={true}
        sx={{
          '& .MuiDataGrid-root': {
            border: '1px solid',
            borderColor: 'divider',
          },
          '& .MuiDataGrid-cell': {
            borderBottom: '1px solid',
            borderRight: '1px solid',
            borderColor: 'divider',
            fontSize: '0.875rem',
            padding: '12px',
          },
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: 'primary.50',
            borderBottom: '2px solid',
            borderColor: 'primary.200',
            fontSize: '1rem',
            fontWeight: 600,
            '& .MuiDataGrid-columnHeaderTitle': {
              fontWeight: 600,
            },
            '& .MuiDataGrid-columnHeader': {
              borderRight: '1px solid',
              borderColor: 'divider',
            },
          },
          '& .MuiDataGrid-row': {
            borderBottom: '1px solid',
            borderColor: 'divider',
            '&:hover': {
              bgcolor: 'action.hover',
            },
          },
          '& .enriched-row': {
            bgcolor: 'success.50',
            '&:hover': {
              bgcolor: 'success.100',
            },
          },
          '& .MuiDataGrid-footerContainer': {
            borderTop: '2px solid',
            borderColor: 'primary.200',
            backgroundColor: 'background.paper',
            '& .MuiTablePagination-displayedRows': {
              fontSize: '0.875rem',
            },
            '& .MuiTablePagination-selectLabel': {
              display: 'none',
            },
            '& .MuiTablePagination-select': {
              display: 'none',
            },
            '& .MuiTablePagination-actions': {
              '& .MuiIconButton-root': {
                fontSize: '1rem',
              },
            },
          },
          '& .MuiDataGrid-detailPanel': {
            backgroundColor: 'background.default',
          },
        }}
        disableColumnFilter
        disableColumnMenu
      />
    </Box>
  );
}