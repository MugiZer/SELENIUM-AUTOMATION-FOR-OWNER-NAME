const express = require('express');
const path = require('path');
const cors = require('cors');
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Serve static files from the UI build
app.use(express.static(path.join(__dirname, 'ui/dist')));

// API routes will go here
app.get('/api/status', (req, res) => {
  res.json({ status: 'Server is running' });
});

// All other requests go to the React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'ui/dist/index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`API available at http://localhost:${PORT}/api/status`);
});
