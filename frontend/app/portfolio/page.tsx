'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Paper from '@mui/material/Paper';
import PortfolioUpload from '../components/PortfolioUpload';
import ToastProvider from '../dashboard/components/ToastProvider';
import AppTheme from '../shared-theme/AppTheme';

export default function PortfolioUploadPage() {
  return (
    <AppTheme>
      <ToastProvider>
        {/* Header with gradient background */}
        <Box
          sx={{
            background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
            color: 'white',
            py: 6,
            mb: 4,
          }}
        >
          <Container maxWidth="md">
            <Box textAlign="center">
              <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
                Upload Portfolio
              </Typography>
              <Typography variant="h6" sx={{ opacity: 0.9, maxWidth: 600, mx: 'auto' }}>
                Upload your portfolio CSV file and we'll automatically find missing ticker symbols using financial APIs
              </Typography>
            </Box>
          </Container>
        </Box>

        <Container maxWidth="md" sx={{ py: 4 }}>
        <Stack spacing={4}>

          {/* Instructions */}
          <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Expected CSV Format:
            </Typography>
            <Typography variant="body2" component="div" sx={{ fontFamily: 'monospace' }}>
              Name, Symbol, Price, # of Shares, Market Value<br/>
              Apple Inc., AAPL, 189.89, 10, 1898.90<br/>
              Microsoft Corporation, , 326.12, 5, 1630.60<br/>
              Berkshire Hathaway Inc. Class B, , 362.55, 2, 725.10
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Missing symbols (empty Symbol column) will be automatically looked up using company names
            </Typography>
          </Paper>

          {/* Upload Component */}
          <PortfolioUpload />

          {/* Features */}
          <Box>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, textAlign: 'center' }}>
              What happens next?
            </Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={3}>
              <Paper sx={{ p: 3, flex: 1, textAlign: 'center' }}>
                <Typography variant="h6" color="primary" gutterBottom>
                  1. Parse & Validate
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Your CSV is parsed and validated for the correct format
                </Typography>
              </Paper>
              <Paper sx={{ p: 3, flex: 1, textAlign: 'center' }}>
                <Typography variant="h6" color="primary" gutterBottom>
                  2. Identify Missing
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  We identify rows with missing ticker symbols
                </Typography>
              </Paper>
              <Paper sx={{ p: 3, flex: 1, textAlign: 'center' }}>
                <Typography variant="h6" color="primary" gutterBottom>
                  3. Lookup & Enrich
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Missing symbols are looked up using financial APIs
                </Typography>
              </Paper>
            </Stack>
          </Box>
        </Stack>
        </Container>
      </ToastProvider>
    </AppTheme>
  );
}