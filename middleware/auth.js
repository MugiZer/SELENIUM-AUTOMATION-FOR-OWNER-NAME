import { UnauthorizedError } from '../utils/errors.js';

export const isAuthenticated = (req, res, next) => {
  // Check if user is authenticated
  // In a real app, verify JWT token or session
  if (req.session?.userId) {
    // Add user to request object for use in route handlers
    req.user = {
      id: req.session.userId,
      // Add other user properties as needed
    };
    return next();
  }
  
  // If not authenticated, return 401 Unauthorized
  throw new UnauthorizedError('Authentication required');
};

export const hasRole = (roles = []) => {
  return (req, res, next) => {
    if (!req.user) {
      throw new UnauthorizedError('Authentication required');
    }
    
    if (roles.length && !roles.includes(req.user.role)) {
      throw new ForbiddenError('Insufficient permissions');
    }
    
    next();
  };
};
