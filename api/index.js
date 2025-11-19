import express from 'express';
import cors from 'cors';
import 'dotenv/config';
import routes from '../routes/index.js';

const app = express();

// ============ MIDDLEWARE ============

// Enable CORS with proper configuration
app.use(cors({
  origin: process.env.VERCEL_ENV === 'production'
    ? process.env.VERCEL_URL || true  // Allow all origins in production for now
    : process.env.CORS_ORIGIN || 'http://localhost:3000',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  credentials: true,
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Security headers middleware
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  next();
});

// Parse JSON and URL-encoded bodies with size limits
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// ============ ROUTES ============
// CRITICAL: Routes mounted at "/" because Vercel STRIPS the "/api" prefix
// Example: Frontend calls /api/health
//          Vercel function receives: GET /health
//          routes are at /, so router.use('/health', ...) will match
app.use('/', routes);

// ============ 404 HANDLER ============
// Catches any request that didn't match routes
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found',
    path: req.originalUrl,
    method: req.method
  });
});

// ============ ERROR HANDLER ============
// Catches any errors thrown in routes
app.use((err, req, res, next) => {
  console.error('[API Error]', err);
  const statusCode = err.statusCode || 500;
  const message = process.env.NODE_ENV === 'production'
    ? 'Internal Server Error'
    : err.message || 'Something went wrong!';

  res.status(statusCode).json({
    success: false,
    error: message,
    ...(process.env.NODE_ENV !== 'production' && { stack: err.stack })
  });
});

// Export the Express API for Vercel
export default app;

// Only start the server if not in a Vercel environment
if (!process.env.VERCEL) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  });
}
