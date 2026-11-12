import { useState, useCallback } from 'react';
import { uploadApi } from '../services/api';
import { useAnalysisStore } from '../store/analysisStore';

export function useUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  
  const setCurrentDocument = useAnalysisStore((state) => state.setCurrentDocument);

  const upload = useCallback(async (file) => {
    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      const response = await uploadApi.upload(file, (percent) => {
        setProgress(percent);
      });

      if (response.data.success) {
        setCurrentDocument(response.data.document);
        return response.data;
      } else {
        throw new Error('Upload failed');
      }
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Upload failed';
      setError(message);
      throw new Error(message);
    } finally {
      setUploading(false);
    }
  }, [setCurrentDocument]);

  const reset = useCallback(() => {
    setUploading(false);
    setProgress(0);
    setError(null);
  }, []);

  return {
    upload,
    uploading,
    progress,
    error,
    reset,
  };
}
