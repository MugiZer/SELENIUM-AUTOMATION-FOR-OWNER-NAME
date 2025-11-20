import jwt from 'jsonwebtoken';

export const isAuthenticated = (req, res, next) => {
  try {
    // 1. Get token from header
    const token = req.headers.authorization?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({
        success: false,
        error: 'No token provided'
      });
    }

    // 2. Verify token
    // Use environment variable or fallback for development
    const secret = process.env.JWT_SECRET || 'dev-secret-key-change-me';
    const decoded = jwt.verify(token, secret);
    
    // 3. Attach user to request
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({
      success: false,
      error: 'Invalid or expired token'
    });
  }
};
