import { PropertyData, ApiResponse, UploadResponse } from '../types';

// Use the environment variable or fallback to development server
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';

// Helper function to handle API responses
async function handleResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));
  
  if (!response.ok) {
    const error = (data && data.error) || response.statusText;
    return Promise.reject(error);
  }
  
  return data as T;
}

const api = {
  async uploadCsv(file: File): Promise<ApiResponse<UploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    return handleResponse<ApiResponse<UploadResponse>>(response);
  },

  async getPropertyData(): Promise<ApiResponse<PropertyData[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/properties`, {
        credentials: 'include',
      });
      return await handleResponse<ApiResponse<PropertyData[]>>(response);
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
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }
};

export default api;
