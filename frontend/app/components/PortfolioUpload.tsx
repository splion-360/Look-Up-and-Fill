'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Alert from '@mui/material/Alert';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import TableChartIcon from '@mui/icons-material/TableChart';
import { useToast } from '../dashboard/components/ToastProvider';
import { useRouter } from 'next/navigation';
import { usePortfolioSession } from '../hooks/usePortfolioSession';

interface PortfolioUploadProps {
  onUploadSuccess?: (data: { success: boolean; fileName: string; totalRows: number; missingSymbols: number }) => void;
}

export default function PortfolioUpload({ onUploadSuccess }: PortfolioUploadProps) {
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const [uploadSuccess, setUploadSuccess] = React.useState(false);
  const [error, setError] = React.useState('');
  const [dragOver, setDragOver] = React.useState(false);
  const { showToast } = useToast();
  const router = useRouter();
  const { createSession } = usePortfolioSession();
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const validateFile = (file: File) => {
    const isCorrect = file.type === 'text/csv' || file.name.toLowerCase().endsWith('.csv') || file.name.toLowerCase().endsWith('.xslx');

    if (!isCorrect) {
      setError('Please upload a CSV / XSLX file only');
      return false;
    }

    if (file.size > 100 * 1024 * 1024) {
      setError('File size must be less than 100MB');
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
      setUploadSuccess(false);
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
      setUploadSuccess(false);
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
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();

      const missingSymbols = Object.values(result.missing_data).reduce((sum: number, count: any) => sum + count, 0);
      createSession({
        fileName: selectedFile.name,
        totalRows: result.total_rows,
        missingSymbols: missingSymbols,
        csvData: result.data
      });

      setUploadSuccess(true);

      setTimeout(() => {
        router.push('/portfolio/table');
      }, 500);

      if (onUploadSuccess) {
        onUploadSuccess({
          success: true,
          fileName: selectedFile.name,
          totalRows: result.total_rows,
          missingSymbols: missingSymbols
        });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setError(errorMessage);
      setUploadSuccess(false);
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
    <Paper sx={{ p: 3 }}>
      <Stack spacing={3}>

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
                height: 200,
                width: '100%',
                borderStyle: 'dashed',
                borderWidth: 2,
                borderColor: dragOver ? 'primary.main' : 'divider',
                color: dragOver ? 'primary.main' : 'text.secondary',
                bgcolor: dragOver ? 'primary.50' : 'background.default',
                flexDirection: 'column',
                gap: 2,
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'primary.50',
                  color: 'primary.main',
                }
              }}
              disabled={uploading}
            >
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                {dragOver ? 'Drop CSV file here' : 'Click to select CSV file or drag & drop'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Maximum file size: 100MB • CSV/XLSX only
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
              }}
            >
              <TableChartIcon color="primary" />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {selectedFile.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </Typography>
              </Box>
              <Button
                onClick={handleRemoveFile}
                disabled={uploading}
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

        {uploading && !uploadSuccess && (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom>
              Processing portfolio file...
            </Typography>
          </Box>
        )}

        {uploadSuccess && (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom sx={{ color: 'success.main', fontWeight: 500 }}>
              Upload successful, redirecting...
            </Typography>
          </Box>
        )}

        {!uploadSuccess && (
          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            startIcon={<CloudUploadIcon />}
            size="large"
            sx={{
              alignSelf: 'center',
              '&.Mui-disabled': {
                backgroundColor: 'grey.400',
                color: 'grey.600',
              }
            }}
          >
            {uploading ? 'Processing...' : 'Upload & Process'}
          </Button>
        )}
      </Stack>
    </Paper>
  );
}