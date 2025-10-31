'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PortfolioUpload from '../components/PortfolioUpload';
import ToastProvider from '../dashboard/components/ToastProvider';
import AppTheme from '../shared-theme/AppTheme';
import PageTransitionLoader from '../components/PageTransitionLoader';
import { usePageTransition } from '../hooks/usePageTransition';
import { useRouter } from 'next/navigation';

export default function PortfolioUploadPage() {
  const { navigate } = usePageTransition();
  const router = useRouter();
  const [isNavigating, setIsNavigating] = React.useState(false);

  // Handle navigation with transition (for Back to Home)
  const handleNavigationWithTransition = (path: string) => {
    setIsNavigating(true);
    navigate(path);
  };

  // Handle navigation without transition (direct navigation)
  const handleDirectNavigation = (path: string) => {
    router.push(path);
  };

  if (isNavigating) {
    return <PageTransitionLoader />;
  }
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
                  onClick={() => handleNavigationWithTransition('/')}
                  sx={{ mb: 2 }}
                >
                  Back to Home
                </Button>
                <Box sx={{ textAlign: 'center', py: 10 }}>
                  <Typography
                    variant="h3"
                    component="h1"
                    gutterBottom
                    sx={{ fontWeight: 'bold', color: 'primary.main', mb: 2 }}
                  >
                    Upload Portfolio
                  </Typography>
                  <Typography variant="h6" sx={{ color: 'text.secondary', fontSize: '1.2rem' }}>
                    Upload your portfolio CSV file and we&apos;ll automatically find missing ticker symbols
                  </Typography>
                </Box>
              </Box>



              {/* Upload Component */}
              <PortfolioUpload />

              {/* Features */}
              {/* <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, textAlign: 'center' }}>
                  What happens next?
                </Typography>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={3}>
                  <Box sx={{ p: 2, flex: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="primary" gutterBottom>
                      1. Parse & Validate
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Your CSV is parsed and validated for the correct format
                    </Typography>
                  </Box>
                  <Box sx={{ p: 2, flex: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="primary" gutterBottom>
                      2. Identify Missing
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      We identify rows with missing ticker symbols
                    </Typography>
                  </Box>
                  <Box sx={{ p: 2, flex: 1, textAlign: 'center' }}>
                    <Typography variant="h6" color="primary" gutterBottom>
                      3. Lookup & Enrich
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Missing symbols are looked up using financial APIs
                    </Typography>
                  </Box>
                </Stack>
              </Paper> */}
            </Stack>
          </Container>
        </Box>
      </ToastProvider>
    </AppTheme>
  );
}