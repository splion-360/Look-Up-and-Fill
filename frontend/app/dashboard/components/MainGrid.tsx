'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import PortfolioUpload from '../../components/PortfolioUpload';

interface MainGridProps {
  selectedTab?: string;
}

function PortfolioContent() {
  const handleUploadSuccess = () => {
    // Redirect to portfolio data page
    window.location.href = '/portfolio/table';
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 700 }}>
      <PortfolioUpload onUploadSuccess={handleUploadSuccess} />
    </Box>
  );
}

export default function MainGrid({ selectedTab = 'upload' }: MainGridProps) {
  return (
    <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
      <PortfolioContent />
    </Box>
  );
}
