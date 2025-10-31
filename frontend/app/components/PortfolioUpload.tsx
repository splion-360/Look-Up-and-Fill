'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import InfinityLoader from '../dashboard/components/InfinityLoader';
import Alert from '@mui/material/Alert';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import TableChartIcon from '@mui/icons-material/TableChart';
import { useToast } from '../dashboard/components/ToastProvider';
import { usePageTransition } from '../hooks/usePageTransition';

interface PortfolioUploadProps {
  onUploadSuccess?: (data: any) => void;
}

export default function PortfolioUpload({ onUploadSuccess }: PortfolioUploadProps) {
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [dragOver, setDragOver] = React.useState(false);
  const { showToast } = useToast();
  const { navigate } = usePageTransition();
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const validateFile = (file: File) => {
    const isCSV = file.type === 'text/csv' || file.name.toLowerCase().endsWith('.csv');
    
    if (!isCSV) {
      setError('Please select a CSV file only');
      return false;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      setError('File size must be less than 10MB');
      return false;
    }

    setError('');
    return true;
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (validateFile(file)) {
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);

    const files = event.dataTransfer.files;
    const file = files[0];

    if (file && validateFile(file)) {
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a CSV file');
      return;
    }

    const startTime = Date.now();
    setUploading(true);
    setError('');

    try {
      // Mock upload for now - replace with actual API call later
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock successful response
      const mockResponse = {
        success: true,
        fileName: selectedFile.name,
        totalRows: 8,
        missingSymbols: 5
      };

      showToast('Portfolio uploaded successfully!', 'success');

      // Reset form
      setSelectedFile(null);
      setError('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Navigate to table view
      navigate('/portfolio/table');

      if (onUploadSuccess) {
        onUploadSuccess(mockResponse);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setError(errorMessage);
      showToast(`Upload failed: ${errorMessage}`, 'error');
    } finally {
      const elapsedTime = Date.now() - startTime;
      const minDuration = 2000;
      
      if (elapsedTime < minDuration) {
        setTimeout(() => setUploading(false), minDuration - elapsedTime);
      } else {
        setUploading(false);
      }
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Paper sx={{ p: 4, borderRadius: 3, elevation: 4, bgcolor: 'background.paper' }}>
      <Stack spacing={4}>
        <Box textAlign="center">
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: 'text.primary', mb: 2 }}>
            Upload Portfolio CSV
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ fontSize: '1.1rem', maxWidth: 600, mx: 'auto' }}>
            Upload your portfolio CSV file to enrich missing ticker symbols using AI-powered financial APIs
          </Typography>
        </Box>

        <Box>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
            disabled={uploading}
          />

          {!selectedFile ? (
            <Button
              variant="outlined"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              startIcon={<CloudUploadIcon />}
              sx={{
                height: 140,
                width: '100%',
                borderStyle: 'dashed',
                borderWidth: 2,
                borderRadius: 3,
                borderColor: dragOver ? 'primary.main' : 'grey.400',
                color: dragOver ? 'primary.main' : 'text.primary',
                bgcolor: dragOver ? 'primary.50' : 'grey.50',
                flexDirection: 'column',
                gap: 1,
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'primary.50',
                  color: 'primary.main',
                  transform: 'translateY(-2px)',
                  boxShadow: 2,
                }
              }}
              disabled={uploading}
            >
              <Typography variant="h6" sx={{ fontWeight: 500, mb: 1 }}>
                {dragOver ? 'Drop CSV file here' : 'Click to select CSV file or drag & drop'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.95rem' }}>
                Maximum file size: 10MB • CSV format only
              </Typography>
            </Button>
          ) : (
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                bgcolor: 'background.default',
                borderRadius: 2,
                border: '1px solid',
                borderColor: 'divider'
              }}
            >
              <TableChartIcon color="primary" sx={{ fontSize: 32 }} />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 500, fontSize: '1.1rem' }}>
                  {selectedFile.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.9rem' }}>
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </Typography>
              </Box>
              <Button
                size="medium"
                onClick={handleRemoveFile}
                disabled={uploading}
                sx={{ fontSize: '0.9rem' }}
              >
                Remove
              </Button>
            </Paper>
          )}
        </Box>

        {error && (
          <Alert severity="error">
            {error}
          </Alert>
        )}

        {uploading && (
          <Box>
            <Typography variant="h6" gutterBottom sx={{ fontSize: '1.1rem' }}>
              Processing portfolio file...
            </Typography>
            <InfinityLoader />
          </Box>
        )}

        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          startIcon={<CloudUploadIcon />}
          size="large"
          sx={{
            alignSelf: 'center',
            textTransform: 'none',
            fontWeight: 600,
            borderRadius: 3,
            px: 6,
            py: 2,
            fontSize: '1.1rem',
            boxShadow: 3,
            '&:hover': {
              boxShadow: 6,
              transform: 'translateY(-2px)',
            },
            '&:disabled': {
              opacity: 0.6,
            },
            transition: 'all 0.3s ease',
          }}
        >
          {uploading ? 'Processing...' : 'Upload & Process'}
        </Button>
      </Stack>
    </Paper>
  );
}