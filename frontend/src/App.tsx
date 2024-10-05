import React, { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import axios from 'axios';
import { Box, Button, CircularProgress, Typography, LinearProgress } from '@mui/material';
import { CloudUpload as CloudUploadIcon, Download as DownloadIcon } from '@mui/icons-material';
import MarkdownPreview from '@uiw/react-markdown-preview';

const App: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [markdownResult, setMarkdownResult] = useState<string | null>(null);
  const [completed, setCompleted] = useState<number>(0);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleFileUploadMutation = useMutation(
    (formData: FormData) =>
      axios.post('http://127.0.0.1:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 10000,  // 10 seconds timeout, adjust as necessary
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentageCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setCompleted(percentageCompleted);
          } else {
            setCompleted(-1);
          }
        },
      }),
    {
      onSuccess: (data) => {
        setMarkdownResult(data.data.markdown);
      },
      onError: (error) => {
        console.error('Error uploading file:', error);
      },
    }
  );

  const handleFileUpload = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    handleFileUploadMutation.mutate(formData);
  };

  const handleDownloadMarkdown = () => {
    if (!markdownResult) return;

    // Create a Blob with markdown content
    const blob = new Blob([markdownResult], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);

    // Create an anchor element and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = 'converted_markdown.md';
    document.body.appendChild(link);
    link.click();

    // Cleanup the URL and remove the anchor element
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: 2,
        backgroundColor: '#f0f2f5',
      }}
    >
      <Typography variant="h4" gutterBottom sx={{ color: '#1976d2' }}>
        Convert Your File to Markdown
      </Typography>

      <form onSubmit={handleFileUpload} style={{ width: '100%', maxWidth: '400px', textAlign: 'center' }}>
        <input
          accept=".pdf,.docx,.csv,.html"
          style={{ display: 'none' }}
          id="file-upload"
          type="file"
          onChange={handleFileChange}
        />
        <label htmlFor="file-upload">
          <Button
            variant="contained"
            component="span"
            fullWidth
            startIcon={<CloudUploadIcon />}
            sx={{
              backgroundColor: '#1976d2',
              color: 'white',
              '&:hover': { backgroundColor: '#1565c0' },
              mb: 2,
            }}
          >
            Choose File
          </Button>
        </label>

        {selectedFile && (
          <Typography variant="body1" gutterBottom sx={{ color: '#555' }}>
            Selected file: <strong>{selectedFile.name}</strong>
          </Typography>
        )}

        <Button
          variant="contained"
          color="primary"
          type="submit"
          fullWidth
          disabled={handleFileUploadMutation.isLoading || !selectedFile}
          sx={{ backgroundColor: '#0288d1', '&:hover': { backgroundColor: '#0277bd' } }}
        >
          {handleFileUploadMutation.isLoading ? <CircularProgress size={24} sx={{ color: 'white' }} /> : 'Upload'}
        </Button>

        {completed > 0 && (
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress variant="determinate" value={completed} />
            <Typography variant="body2" color="textSecondary">
              Upload Progress: {completed}%
            </Typography>
          </Box>
        )}
      </form>

      {markdownResult && (
        <Box
          sx={{
            mt: 4,
            width: '100%',
            maxWidth: '800px',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0px 3px 8px rgba(0, 0, 0, 0.1)',
            p: 3,
          }}
        >
          <Typography variant="h5" gutterBottom sx={{ color: '#0288d1' }}>
            Markdown Preview
          </Typography>
          <MarkdownPreview source={markdownResult} />

          <Button
            variant="contained"
            color="secondary"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadMarkdown}
            sx={{ mt: 2 }}
          >
            Download Markdown
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default App;
