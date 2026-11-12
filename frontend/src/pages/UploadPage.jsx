import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload } from '../components/Upload';
import { ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAnalysisStore } from '../store/analysisStore';

export default function UploadPage() {
  const navigate = useNavigate();
  const setCurrentDocument = useAnalysisStore((state) => state.setCurrentDocument);

  const handleUploadComplete = (result) => {
    if (result.success && result.document) {
      setCurrentDocument(result.document);
      // Navigate to analysis page
      navigate(`/analysis/${result.document.document_id}`);
    }
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Button variant="ghost" className="mb-4" onClick={() => navigate('/')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
          <h1 className="text-3xl font-semibold mb-2">Upload Agreement</h1>
          <p className="text-muted-foreground">
            Upload your finance agreement PDF for AI-powered analysis. We support loan agreements,
            lease contracts, and credit card terms.
          </p>
        </div>

        {/* Upload Component */}
        <Upload onUploadComplete={handleUploadComplete} />

        {/* Info Section */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-muted/50 rounded-lg">
            <h3 className="font-semibold mb-2">Supported Formats</h3>
            <p className="text-sm text-muted-foreground">
              PDF files up to 50MB. Text must be selectable (not scanned images).
            </p>
          </div>
          <div className="p-4 bg-muted/50 rounded-lg">
            <h3 className="font-semibold mb-2">Document Types</h3>
            <p className="text-sm text-muted-foreground">
              Loan agreements, lease contracts, credit card agreements, and similar documents.
            </p>
          </div>
          <div className="p-4 bg-muted/50 rounded-lg">
            <h3 className="font-semibold mb-2">Privacy</h3>
            <p className="text-sm text-muted-foreground">
              Documents are processed securely. Delete your data anytime from the dashboard.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
