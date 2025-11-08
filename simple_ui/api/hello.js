// Simple API route handler that responds with a success message
export default function handler(req, res) {
  // Set cache headers for better performance
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate');
  
  // Return a successful response
  return res.status(200).json({ 
    status: 'success',
    message: 'API is working!',
    timestamp: new Date().toISOString()
  });
}

// Add error handling for unsupported HTTP methods
handler.options = (req, res) => {
  res.setHeader('Allow', ['GET']);
  return res.status(204).end();
};
