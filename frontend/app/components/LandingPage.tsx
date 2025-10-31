'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CssBaseline from '@mui/material/CssBaseline';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import ElectricBoltIcon from '@mui/icons-material/ElectricBolt';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SearchIcon from '@mui/icons-material/Search';
import DownloadIcon from '@mui/icons-material/Download';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import AppTheme from '../shared-theme/AppTheme';
import ColorModeSelect from '../shared-theme/ColorModeSelect';
import InfinityLoader from '../dashboard/components/InfinityLoader';
import { usePageTransition } from '../hooks/usePageTransition';


const items = [
  {
    icon: <CloudUploadIcon sx={{ color: 'text.secondary' }} />,
    title: 'Upload documents for processing',
    description:
      'Upload your portfolio CSV files with missing ticker symbols',
  },
  {
    icon: <SearchIcon sx={{ color: 'text.secondary' }} />,
    title: 'Lookup for symbols',
    description:
      'Our services automatically match company names to accurate ticker symbols',
  },
  {
    icon: <AnalyticsIcon sx={{ color: 'text.secondary' }} />,
    title: 'Data Analysis',
    description:
      'Enrich your portfolio with complete ticker information & validate existing data',
  },
  {
    icon: <DownloadIcon sx={{ color: 'text.secondary' }} />,
    title: 'Export as CSV',
    description:
      'Download your data with all missing ticker symbols populated',
  },
];

function Content() {
  return (
    <Stack
      sx={{ flexDirection: 'column', alignSelf: 'center', gap: 5, maxWidth: 550 }}
    >
      <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 3 }}>
        <img
          src="/mascot.svg"
          alt="Look up and Fill"
          width={80}
          height={80}
          style={{
            display: 'block'
          }}
        />
        <Typography variant="h2" component="h1" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          Look up & Fill
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 3 }}>
        <AccountTreeIcon sx={{ fontSize: '2.5rem', color: 'secondary.main' }} />
        <Typography variant="h3" component="h2" sx={{ fontWeight: 'normal', color: 'secondary.main' }}>
          Workflow
        </Typography>
      </Box>

      {items.map((item, index) => (
        <Stack key={index} direction="row" sx={{ gap: 3 }}>
          <Box sx={{ '& svg': { fontSize: '2.5rem' } }}>
            {item.icon}
          </Box>
          <div>
            <Typography gutterBottom sx={{ fontWeight: 'medium', fontSize: '1.3rem' }}>
              {item.title}
            </Typography>
            <Typography variant="h6" sx={{ color: 'text.secondary', fontSize: '1.1rem' }}>
              {item.description}
            </Typography>
          </div>
        </Stack>
      ))}
    </Stack>
  );
}

interface LandingCardProps {
  onNavigate: (destination: string) => void;
}

function LandingCard({ onNavigate }: LandingCardProps) {
  const handleGetStarted = () => {
    onNavigate('/portfolio');
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 15 }}>
      <Button
        variant="contained"
        size="large"
        onClick={handleGetStarted}
        startIcon={<ElectricBoltIcon />}
        sx={{
          py: 4,
          px: 6,
          fontSize: '1.4rem',
          fontWeight: 600,
          borderRadius: 3,
        }}
      >
        Start Enriching
      </Button>
    </Box>
  );
}

export default function LandingPage(props: { disableCustomTheme?: boolean }) {
  const { isLoading, navigate } = usePageTransition();

  if (isLoading) {
    return (
      <AppTheme {...props}>
        <CssBaseline enableColorScheme />
        <Stack
          direction="column"
          component="main"
          sx={[
            {
              justifyContent: 'center',
              alignItems: 'center',
              height: '100vh',
              minHeight: '100%',
            },
            (theme) => ({
              '&::before': {
                content: '""',
                display: 'block',
                position: 'absolute',
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
          <InfinityLoader size={80} />
        </Stack>
      </AppTheme>
    );
  }

  return (
    <AppTheme {...props}>
      <CssBaseline enableColorScheme />
      <ColorModeSelect sx={{ position: 'fixed', top: '1rem', right: '1rem' }} />
      <Stack
        direction="column"
        component="main"
        sx={[
          {
            justifyContent: 'center',
            height: 'calc((1 - var(--template-frame-height, 0)) * 100%)',
            marginTop: 'max(40px - var(--template-frame-height, 0px), 0px)',
            minHeight: '100%',
          },
          (theme) => ({
            '&::before': {
              content: '""',
              display: 'block',
              position: 'absolute',
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
        <Stack
          direction={{ xs: 'column-reverse', md: 'row' }}
          sx={{
            justifyContent: 'center',
            gap: { xs: 6, sm: 12 },
            p: 2,
            mx: 'auto',
          }}
        >
          <Stack
            direction={{ xs: 'column-reverse', md: 'row' }}
            sx={{
              justifyContent: 'center',
              gap: { xs: 6, sm: 12 },
              p: { xs: 2, sm: 4 },
              m: 'auto',
            }}
          >
            <Content />
            <LandingCard onNavigate={navigate} />
          </Stack>
        </Stack>
      </Stack>
    </AppTheme>
  );
}