'use client';

import * as React from 'react';
import { styled } from '@mui/material/styles';
import Divider, { dividerClasses } from '@mui/material/Divider';
import Menu from '@mui/material/Menu';
import MuiMenuItem from '@mui/material/MenuItem';
import { paperClasses } from '@mui/material/Paper';
import { listClasses } from '@mui/material/List';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon, { listItemIconClasses } from '@mui/material/ListItemIcon';
import HomeRoundedIcon from '@mui/icons-material/HomeRounded';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import MoreVertRoundedIcon from '@mui/icons-material/MoreVertRounded';
import MenuButton from './MenuButton';
import { usePageTransition } from '../../hooks/usePageTransition';

const MenuItem = styled(MuiMenuItem)({
  margin: '2px 0',
});

interface OptionsMenuProps {
  onUserDataUpdate?: () => void;
}

export default function OptionsMenu({ onUserDataUpdate }: OptionsMenuProps) {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const { navigate } = usePageTransition();

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleHome = () => {
    navigate('/');
    handleClose();
  };

  const handleAbout = () => {
    // Could redirect to an about page or show info
    console.log('About Portfolio Enrichment');
    handleClose();
  };

  return (
    <React.Fragment>
      <MenuButton
        aria-label="Open menu"
        onClick={handleClick}
        sx={{ borderColor: 'transparent' }}
      >
        <MoreVertRoundedIcon />
      </MenuButton>
      <Menu
        anchorEl={anchorEl}
        id="menu"
        open={open}
        onClose={handleClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        sx={{
          [`& .${listClasses.root}`]: {
            padding: '4px',
          },
          [`& .${paperClasses.root}`]: {
            padding: 0,
          },
          [`& .${dividerClasses.root}`]: {
            margin: '4px -4px',
          },
        }}
      >
        <MenuItem onClick={handleHome}>
          <ListItemIcon>
            <HomeRoundedIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Home</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={handleAbout}
          sx={{
            [`& .${listItemIconClasses.root}`]: {
              ml: 'auto',
              minWidth: 0,
            },
          }}
        >
          <ListItemText>About</ListItemText>
          <ListItemIcon>
            <InfoRoundedIcon fontSize="small" />
          </ListItemIcon>
        </MenuItem>
      </Menu>
    </React.Fragment>
  );
}
