import { Router } from 'express';
import authRoutes from './auth.routes.js';
import propertyRoutes from './property.routes.js';
import uploadRoutes from './upload.routes.js';
import healthRoutes from './health.routes.js';

const router = Router();

// API Routes
router.use('/auth', authRoutes);
router.use('/api/properties', propertyRoutes);
router.use('/api/upload', uploadRoutes);
router.use('/health', healthRoutes);

// 404 handler for /api/* routes
router.use('/api/*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found',
    path: req.originalUrl,
    method: req.method,
  });
});

export default router;
