import { Router } from 'express';
import multer from 'multer';
import { isAuthenticated } from '../middleware/auth.js';

const router = Router();

// Configure multer for file uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/csv',
    ];
    
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Only CSV files are allowed'));
    }
  },
});

// File upload endpoint
router.post(
  '/',
  isAuthenticated,
  upload.single('file'),
  async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({
          success: false,
          error: 'No file uploaded or invalid file type',
        });
      }

      // Process the file (req.file.buffer contains the file data)
      // In a real app, you would process the CSV file here
      
      res.json({
        success: true,
        message: 'File uploaded successfully',
        filename: req.file.originalname,
        size: req.file.size,
        mimetype: req.file.mimetype,
      });
    } catch (error) {
      console.error('Upload error:', error);
      res.status(500).json({
        success: false,
        error: error.message || 'Error processing file',
      });
    }
  }
);

export default router;
