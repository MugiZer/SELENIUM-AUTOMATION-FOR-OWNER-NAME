import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import api from '../../services/api';
import './FileUpload.css';

interface FileUploadProps {
  onUploadSuccess: (data: any) => void;
  onError: (message: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess, onError }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    const file = acceptedFiles[0];
    if (!file.name.endsWith('.csv')) {
      onError('Please upload a CSV file');
      return;
    }

    setIsUploading(true);
    setProgress(0);

    try {
      // Simulate progress (in a real app, you'd use actual upload progress)
      const interval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + 10;
          if (newProgress >= 90) clearInterval(interval);
          return newProgress > 90 ? 90 : newProgress;
        });
      }, 200);

      const response = await api.uploadCsv(file);
      clearInterval(interval);
      
      if (response.success) {
        setProgress(100);
        onUploadSuccess(response.data);
      } else {
        throw new Error(response.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      onError(error instanceof Error ? error.message : 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  }, [onUploadSuccess, onError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    maxFiles: 1,
    disabled: isUploading,
  });

  return (
    <div className="file-upload-container">
      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''} ${isUploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        {isUploading ? (
          <div className="upload-progress">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
            <p>Uploading... {progress}%</p>
          </div>
        ) : (
          <div className="upload-prompt">
            <p>{isDragActive ? 'Drop the file here' : 'Drag & drop a CSV file here, or click to select'}</p>
            <p className="file-requirements">Only .csv files are accepted</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;
