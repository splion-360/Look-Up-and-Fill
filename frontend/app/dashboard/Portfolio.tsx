'use client';

import { useState, useEffect } from 'react';
import type { } from '@mui/x-date-pickers/themeAugmentation';
import type { } from '@mui/x-charts/themeAugmentation';
import type { } from '@mui/x-tree-view/themeAugmentation';
import { alpha } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import InfinityLoader from './components/InfinityLoader';
import AppNavbar from './components/AppNavbar';
import Header from './components/Header';
import MainGrid from './components/MainGrid';
import AppTheme from '../shared-theme/AppTheme';
import ToastProvider from './components/ToastProvider';
import { usePageTransition } from '../hooks/usePageTransition';
import PageTransitionLoader from '../components/PageTransitionLoader';
import {
  chartsCustomizations,
  dataGridCustomizations,
  treeViewCustomizations,
} from './theme/customizations';

const xThemeComponents = {
  ...chartsCustomizations,
  ...dataGridCustomizations,
  ...treeViewCustomizations,
};

export default function Portfolio(props: { disableCustomTheme?: boolean }) {
  const selectedTab = 'upload'; // Always show upload
  const { isLoading } = usePageTransition();
  const handleTabChange = (tabId: string) => {
    // Only upload tab available
  };

  return (
    <PageTransitionLoader isLoading={isLoading} disableCustomTheme={props.disableCustomTheme}>
    <AppTheme {...props} themeComponents={xThemeComponents}>
      <ToastProvider>
        <CssBaseline enableColorScheme />
        <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
          <AppNavbar />
          
          {/* Header with controls */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
              p: 3,
              pr: 4,
              pt: { xs: 8, md: 3 },
            }}
          >
            <Header />
          </Box>

          {/* Main content - centered upload */}
          <Box
            component="main"
            sx={(theme) => ({
              flexGrow: 1,
              backgroundColor: theme.vars
                ? `rgba(${theme.vars.palette.background.defaultChannel} / 1)`
                : alpha(theme.palette.background.default, 1),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 4,
            })}
          >
            <Box sx={{ width: '100%', maxWidth: 800 }}>
              <MainGrid selectedTab={selectedTab} />
            </Box>
          </Box>
        </Box>
      </ToastProvider>
    </AppTheme>
    </PageTransitionLoader>
  );
}