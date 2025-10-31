import * as React from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import NotificationsRoundedIcon from '@mui/icons-material/NotificationsRounded';
import CustomDatePicker from './CustomDatePicker';
import NavbarBreadcrumbs from './NavbarBreadcrumbs';
import MenuButton from './MenuButton';
import ColorModeIconDropdown from '../../shared-theme/ColorModeIconDropdown';


export default function Header() {
  return (
    <Stack
      direction="row"
      sx={{
        alignItems: 'center',
        justifyContent: 'flex-end',
      }}
      spacing={3}
    >
      <Box sx={{ '& .MuiButton-root': { fontSize: '1rem', px: 2, py: 1 } }}>
        <CustomDatePicker />
      </Box>
      <Box sx={{ '& .MuiIconButton-root': { fontSize: '1.5rem', width: 48, height: 48 } }}>
        <ColorModeIconDropdown />
      </Box>
    </Stack>
  );
}
