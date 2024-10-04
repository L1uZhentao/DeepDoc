import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, AppBar, Toolbar } from '@mui/material';

const App: React.FC = () => {
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    fetch('http://localhost:8000/') // Make sure this URL matches your backend
      .then(response => response.json())
      .then(data => setMessage(data.message))
      .catch(error => console.error('Error fetching data from backend:', error));
  }, []);

  return (
    <div>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Document Processing App
          </Typography>
        </Toolbar>
      </AppBar>

      <Container>
        <Box sx={{ my: 4, textAlign: 'center' }}>
          <Typography variant="h4" gutterBottom>
            DeepDoc
          </Typography>
          <Typography variant="body1">
            {message ? message : 'Fetching message from backend...'}
          </Typography>
        </Box>
      </Container>
    </div>
  );
};

export default App;
