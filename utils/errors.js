// Base error class
export class AppError extends Error {
  constructor(message, statusCode = 500, details = null) {
    super(message);
    this.statusCode = statusCode;
    this.details = details;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

// 400 Bad Request
export class BadRequestError extends AppError {
  constructor(message = 'Bad Request', details = null) {
    super(message, 400, details);
  }
}

// 401 Unauthorized
export class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized', details = null) {
    super(message, 401, details);
  }
}

// 403 Forbidden
export class ForbiddenError extends AppError {
  constructor(message = 'Forbidden', details = null) {
    super(message, 403, details);
  }
}

// 404 Not Found
export class NotFoundError extends AppError {
  constructor(message = 'Resource not found', details = null) {
    super(message, 404, details);
  }
}

// 409 Conflict
export class ConflictError extends AppError {
  constructor(message = 'Conflict', details = null) {
    super(message, 409, details);
  }
}

// Error handling middleware
export const errorHandler = (err, req, res, next) => {
  // Default to 500 if status code not set
  const statusCode = err.statusCode || 500;
  
  // Log the error for debugging
  console.error(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl}`, {
    error: err.message,
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
    details: err.details,
  });

  // Don't leak error details in production
  const response = {
    success: false,
    error: err.message || 'Internal Server Error',
  };

  // Include error details if available and in development
  if (process.env.NODE_ENV === 'development' && err.details) {
    response.details = err.details;
  }

  // Include validation errors if available
  if (err.errors) {
    response.errors = err.errors;
  }

  res.status(statusCode).json(response);
};

// 404 handler
export const notFoundHandler = (req, res) => {
  throw new NotFoundError(`Route ${req.originalUrl} not found`);
};
