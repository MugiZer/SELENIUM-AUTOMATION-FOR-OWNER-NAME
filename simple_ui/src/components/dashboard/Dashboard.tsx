import React, { useState, useEffect } from 'react';
import { PropertyData } from '../../types';
import api from '../../services/api';
import FileUpload from '../upload/FileUpload';
import { Button, Typography, Box, CircularProgress, Alert, Paper } from '@mui/material';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const [data, setData] = useState<PropertyData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await api.getPropertyData();
        
        if (response.success && response.data) {
          setData(response.data);
        } else {
          setError(response.error || 'Failed to load data');
        }
      } catch (err) {
        setError('An error occurred while fetching data');
        console.error('Fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleDownload = async (filename: string) => {
    try {
      await api.downloadResults(filename);
    } catch (err) {
      setError('Failed to download file');
      console.error('Download error:', err);
    }
  };

  const handleFileProcessed = (fileData: any) => {
    setSelectedFile(fileData.filename);
    // Refresh data after successful upload
    if (fileData.processedRecords > 0) {
      const response = api.getPropertyData();
      if (response) {
        response.then((res) => {
          if (res.success && res.data) {
            setData(res.data);
          }
        });
      }
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box className="dashboard" sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Property Data Dashboard
      </Typography>
      
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          Upload CSV File
        </Typography>
        <FileUpload 
          onUploadSuccess={handleFileProcessed} 
          onError={setError} 
        />
      </Paper>

      {selectedFile && (
        <Box sx={{ mb: 3, textAlign: 'center' }}>
          <Button 
            variant="contained"
            color="primary"
            onClick={() => handleDownload(selectedFile)}
            sx={{ minWidth: 200 }}
          >
            Download Processed Data
          </Button>
        </Box>
      )}

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" component="h2" gutterBottom>
          Property Data
        </Typography>
        {data.length > 0 ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Civic Number</th>
                  <th>Street Name</th>
                  <th>Postal Code</th>
                  <th>Owner</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item, index) => (
                  <tr key={index}>
                    <td>{item.civic_number}</td>
                    <td>{item.street_name}</td>
                    <td>{item.postal_code}</td>
                    <td>{item.owner_names || 'N/A'}</td>
                    <td>
                      <span className={`status-badge ${item.status || 'pending'}`}>
                        {item.status || 'Pending'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
            <Typography>No property data available. Upload a CSV file to get started.</Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default Dashboard;
