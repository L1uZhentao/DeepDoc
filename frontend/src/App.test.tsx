import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  render(<App />);
  // check after fetching data from backend
  const linkElement = screen.getByText("DeepDoc");
  expect(linkElement).toBeInTheDocument();
});
