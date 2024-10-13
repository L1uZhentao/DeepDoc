import React, { useState } from 'react';
import { useMutation } from 'react-query';
import axios from 'axios';
import { Box, Button, CircularProgress, Typography, LinearProgress, Alert, FormControlLabel, Switch, TextField } from '@mui/material';
import { CloudUpload as CloudUploadIcon, Download as DownloadIcon } from '@mui/icons-material';
import MarkdownPreview from '@uiw/react-markdown-preview';

enum DocumentType {
  pdf = 'pdf',
  docx = 'docx',
  csv = 'csv',
  html = 'html'
}

const App: React.FC = () => {

  const API_HOST = process.env.FASTAPI_HOST || '127.0.0.1';
  const API_PORT = process.env.FASTAPI_PORT || '8000';
  const API_BASE_URL = `http://${API_HOST}:${API_PORT}`;
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileInfo, setFileInfo] = useState<{ name: string; type: DocumentType; file_size: number; word_count:number, image_count:number } | { name: string; type: DocumentType; file_size: number; row_count:number, col_count:number } | null>(null); // State for file info
  const [markdownResult, setMarkdownResult] = useState<string | null>(null);
  const [completed, setCompleted] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null); // Track error messages
  const [isAdvanced, setIsAdvanced] = useState<boolean>(false); // Toggle between basic and advanced parsing
  const [recipientEmail, setRecipientEmail] = useState<string>(''); // Email for advanced parsing
  const [emailError, setEmailError] = useState<string | null>(null); // Email validation error
  const [isSentEmail, setIsSentEmail] = useState<boolean>(false); // Email sent status

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null); // Reset error on file change
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setSelectedFile(file);
    }
  }

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  const handleFileUploadMutation = useMutation(
    (formData: FormData) => {
      const url = `${API_BASE_URL}/upload?advanced=${isAdvanced}${isAdvanced ? `&receipient_email=${recipientEmail}` : ''}`;
      return axios.post(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000,  // 30 seconds timeout, adjust as necessary
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentageCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setCompleted(percentageCompleted);
          } else {
            setCompleted(-1);
          }
        },
      });
    },
    {
      onSuccess: (data) => {
        setMarkdownResult(data.data.markdown);
        setIsSentEmail(data.data.isSentEmail);
        if (data.data.file_info.type === 'CSV') { 
          setFileInfo({ name: data.data.file_info.name, type: DocumentType.csv, file_size: data.data.file_info.file_size, row_count: data.data.file_info.row_count, col_count: data.data.file_info.col_count });
        } else {
          setFileInfo({ name: data.data.file_info.name, type: data.data.file_info.type , file_size: data.data.file_info.file_size, word_count: data.data.file_info.word_count, image_count: data.data.file_info.image_count });
        }
        setErrorMessage(null); // Clear error if successful
      },
      onError: (error) => {
        if (axios.isAxiosError(error)) {
          if (error.response && error.response.status === 400) {
            setErrorMessage(error.response.data.detail); // Handle 400 error for unsupported file type
            setFileInfo(null); // Clear file info
          } else if (error.response && error.response.status === 500) {
            setErrorMessage("Parser Error: " + error.response.data.detail);
          } else if (error.response){
            setErrorMessage('An unexpected error occurred.' + error.response.data.detail);
          } else {
            setErrorMessage('An unexpected unknown error occurred.');
          }
        } else {
          setErrorMessage('An unexpected error occurred.');
        }
        setMarkdownResult(null); // Clear previous markdown result
        console.error('Error uploading file:', error);
      },
    }
  );

  const handleFileUpload = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) return;

    if (isAdvanced && !validateEmail(recipientEmail)) {
      setEmailError('Please enter a valid email address.');
      return;
    }

    setEmailError(null); // Clear email error if valid

    const formData = new FormData();
    formData.append('file', selectedFile);
    handleFileUploadMutation.mutate(formData);
  };

  const handleDownloadMarkdown = () => {
    if (!markdownResult) return;

    const blob = new Blob([markdownResult], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'converted_markdown.md';
    document.body.appendChild(link);
    link.click();

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
      DeepDoc: Convert Your File to Markdown
      </Typography>

      {errorMessage && (
      <Alert severity="error" sx={{ mb: 2 }}>
        {errorMessage}
      </Alert>
      )}

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
        <Box sx={{ mb: 2 }}>
        <Typography variant="body1" gutterBottom sx={{ color: '#555' }}>
          Selected file: <strong>{selectedFile.name}</strong>
        </Typography>
        </Box>
      )}

      <FormControlLabel
        control={<Switch checked={isAdvanced} onChange={() => setIsAdvanced(!isAdvanced)} />}
        label={isAdvanced ? "Advanced Parse" : "Basic Parse"}
      />

      {isAdvanced && (
        <TextField
          label="Recipient Email"
          type="email"
          fullWidth
          value={recipientEmail}
          onChange={(e) => setRecipientEmail(e.target.value)}
          error={!!emailError}
          helperText={emailError}
          sx={{ mb: 2 }}
        />
      )}

      <Button
        variant="contained"
        color="primary"
        type="submit"
        fullWidth
        disabled={handleFileUploadMutation.isLoading || !selectedFile}
        sx={{ backgroundColor: '#0288d1', '&:hover': { backgroundColor: '#0277bd' } }}
      >
        {handleFileUploadMutation.isLoading ? <CircularProgress size={24} sx={{ color: 'white' }} /> : 'Upload & Convert'}
      </Button>

      {!errorMessage && completed > 0 && (
        <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress variant="determinate" value={completed} />
        <Typography variant="body2" color="textSecondary">
          Upload Progress: {completed}%
        </Typography>
        </Box>
      )}
      </form>

      {fileInfo && (
      <Box
        sx={{
        mt: 2,
        p: 2,
        border: '1px solid #ddd',
        borderRadius: '8px',
        backgroundColor: '#fafafa',
        boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
        width: '100%',
        maxWidth: '800px',
        }}
      >
        <Typography variant="h5" sx={{ color: '#1976d2', mb: 1 }}>
        File Information
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Typography variant="body2" sx={{ color: '#555' }}>
          Size: <strong>{(fileInfo.file_size / 1024).toFixed(2)} KB</strong>
        </Typography>
        <Typography variant="body2" sx={{ color: '#555' }}>
          Type: <strong>{fileInfo.type}</strong>
        </Typography>
        {'row_count' in fileInfo ? (
          <>
          <Typography variant="body2" sx={{ color: '#555' }}>
            Rows: <strong>{fileInfo.row_count}</strong>
          </Typography>
          <Typography variant="body2" sx={{ color: '#555' }}>
            Columns: <strong>{fileInfo.col_count}</strong>
          </Typography>
          </>
        ) : (
          <>
          <Typography variant="body2" sx={{ color: '#555' }}>
            Word Count: <strong>{fileInfo.word_count}</strong>
          </Typography>
          <Typography variant="body2" sx={{ color: '#555' }}>
            Image Count: <strong>{fileInfo.image_count}</strong>
          </Typography>
          </>
        )}
        </Box>
      </Box>
      )}

      {markdownResult && !isSentEmail && (
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
        <Button
        variant="contained"
        color="primary"
        startIcon={<DownloadIcon />}
        onClick={handleDownloadMarkdown}
        sx={{ mt: 2 }}
        >
        Download
        </Button>
        <MarkdownPreview source={markdownResult} />
      </Box>
      )}
      {markdownResult && isSentEmail && (
        <Box
          sx={{
            mt: 4,
            width: '100%',
            maxWidth: '800px',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0px 3px 8px rgba(0, 0, 0, 0.1)',
            p: 3,
            textAlign: 'center',
          }}
        >
          <Typography variant="h5" gutterBottom sx={{ color: '#0288d1' }}>
            Email Notification
          </Typography>
          <Typography variant="body1" sx={{ color: '#555' }}>
            The result will be sent to your email when it is available.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default App;
