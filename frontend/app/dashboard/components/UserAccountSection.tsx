'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Avatar from '@mui/material/Avatar';
import PersonIcon from '@mui/icons-material/Person';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import OptionsMenu from './OptionsMenu';

export default function UserAccountSection() {
  return (
    <Stack
      direction="row"
      sx={{
        p: 2,
        gap: 1,
        alignItems: 'center',
        borderTop: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Avatar
        sx={{
          width: 36,
          height: 36,
          bgcolor: 'primary.main',
          fontSize: 14,
          fontWeight: 600,
        }}
      >
        <TrendingUpIcon sx={{ fontSize: 20 }} />
      </Avatar>
      <Box sx={{ mr: 'auto', minWidth: 0, flex: 1 }}>
        <Typography
          variant="body2"
          sx={{
            fontWeight: 500,
            lineHeight: '16px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          Portfolio Tool
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: 'text.secondary',
            display: 'block',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          Ticker Enrichment
        </Typography>
      </Box>
      <OptionsMenu />
    </Stack>
  );
}