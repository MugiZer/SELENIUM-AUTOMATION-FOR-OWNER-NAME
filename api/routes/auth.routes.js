import { Router } from 'express';
import { body } from 'express-validator';
import { validateRequest } from '../middleware/validation.js';
import { isAuthenticated } from '../middleware/auth.js';

const router = Router();

// Login route
router.post(
  '/login',
  [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 6 }),
  ],
  validateRequest,
  async (req, res) => {
    // Authentication logic here
    res.json({ success: true, token: 'sample-jwt-token' });
  }
);

// Get current user
router.get('/me', isAuthenticated, (req, res) => {
  res.json({
    success: true,
    user: {
      id: req.user?.id,
      email: req.user?.email,
      // Add other user fields as needed
    },
  });
});

export default router;
