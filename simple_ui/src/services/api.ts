import { PropertyData, ApiResponse, UploadResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';

const api = {
  async uploadCsv(file: File): Promise<ApiResponse<UploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to upload file');
      }

      return await response.json();
    } catch (error) {
      console.error('Upload error:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to upload file' 
      };
    }
  },

  async getPropertyData(): Promise<ApiResponse<PropertyData[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/properties`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch property data');
      }

      return await response.json();
    } catch (error) {
      console.error('Fetch error:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to fetch data' 
      };
    }
  },

  async downloadResults(filename: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/download/${filename}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to download file');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  },
};

export default api;
