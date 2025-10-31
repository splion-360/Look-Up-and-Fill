'use client';

import * as React from 'react';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

const menuItems = [
  { text: 'Upload Portfolio', icon: <CloudUploadIcon />, id: 'upload' },
];

interface MenuContentProps {
  selectedTab?: string;
  onTabChange?: (tabId: string) => void;
}

export default function MenuContent({ selectedTab = 'upload', onTabChange }: MenuContentProps) {
  const handleTabClick = (tabId: string) => {
    if (onTabChange) {
      onTabChange(tabId);
    }
  };

  return (
    <Stack sx={{ flexGrow: 1, p: 2 }}>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.id} disablePadding sx={{ display: 'block', mb: 1 }}>
            <ListItemButton 
              selected={selectedTab === item.id}
              onClick={() => handleTabClick(item.id)}
              sx={{
                borderRadius: 2,
                py: 1.5,
                px: 2,
                '&.Mui-selected': {
                  bgcolor: 'primary.50',
                  color: 'primary.main',
                  '&:hover': {
                    bgcolor: 'primary.100',
                  },
                },
                '&:hover': {
                  bgcolor: 'action.hover',
                },
              }}
            >
              <ListItemIcon 
                sx={{ 
                  color: 'inherit',
                  minWidth: 40,
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '1rem',
                  fontWeight: 500,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Stack>
  );
}
