import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload as UploadIcon, FileText, X, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { useUpload } from '../hooks/useUpload';

export function Upload({ onUploadComplete }) {
  const { upload, uploading, progress, error, reset } = useUpload();
  const [file, setFile] = useState(null);
  const [uploadComplete, setUploadComplete] = useState(false);

  const onDrop = useCallback(async (acceptedFiles) => {
    const selectedFile = acceptedFiles[0];
    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      return;
    }

    setFile(selectedFile);
    setUploadComplete(false);

    try {
      const result = await upload(selectedFile);
      setUploadComplete(true);
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (err) {
      console.error('Upload error:', err);
    }
  }, [upload, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  const handleReset = () => {
    setFile(null);
    setUploadComplete(false);
    reset();
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardContent className="p-6">
        {!file ? (
          <div
            {...getRootProps()}
            data-testid="pdf-upload-dropzone"
            className={`dropzone cursor-pointer flex flex-col items-center justify-center min-h-[200px] ${
              isDragActive ? 'dropzone-active' : ''
            }`}
          >
            <input {...getInputProps()} data-testid="pdf-upload-input" />
            <UploadIcon className="w-12 h-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {isDragActive ? 'Drop your PDF here' : 'Upload Finance Agreement'}
            </h3>
            <p className="text-sm text-muted-foreground text-center mb-4">
              Drag and drop a PDF file, or click to browse
            </p>
            <Button variant="secondary" data-testid="pdf-upload-browse-button">
              Browse Files
            </Button>
            <p className="text-xs text-muted-foreground mt-4">
              Supported: PDF files up to 50MB
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium text-sm" data-testid="pdf-upload-filename">
                    {file.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              {!uploading && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleReset}
                  data-testid="pdf-upload-reset"
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>

            {uploading && (
              <div className="space-y-2">
                <Progress value={progress} data-testid="pdf-upload-progress" />
                <p className="text-xs text-muted-foreground text-center">
                  {progress < 100 ? `Uploading... ${progress}%` : 'Processing document...'}
                </p>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 p-3 bg-destructive/10 rounded-lg text-destructive text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <p>{error}</p>
              </div>
            )}

            {uploadComplete && !error && (
              <div className="flex items-center gap-2 p-3 bg-green-500/10 rounded-lg text-green-600 dark:text-green-400 text-sm">
                <CheckCircle className="w-4 h-4 flex-shrink-0" />
                <p>Document uploaded successfully! Ready for analysis.</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
