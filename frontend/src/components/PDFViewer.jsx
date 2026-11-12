import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ZoomIn, ZoomOut, ChevronLeft, ChevronRight, Search, Maximize } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { ScrollArea } from '../components/ui/scroll-area';
import { Skeleton } from '../components/ui/skeleton';

// Set up the worker - use unpkg as a more reliable CDN
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export function PDFViewer({ pdfUrl, selectedClause, onPageChange }) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [searchText, setSearchText] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (selectedClause?.page_number && selectedClause.page_number !== pageNumber) {
      setPageNumber(selectedClause.page_number);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedClause]);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  };

  const onDocumentLoadError = (err) => {
    console.error('PDF load error:', err);
    setError('Failed to load PDF');
    setLoading(false);
  };

  const goToPrevPage = () => {
    if (pageNumber > 1) {
      const newPage = pageNumber - 1;
      setPageNumber(newPage);
      onPageChange?.(newPage);
    }
  };

  const goToNextPage = () => {
    if (pageNumber < numPages) {
      const newPage = pageNumber + 1;
      setPageNumber(newPage);
      onPageChange?.(newPage);
    }
  };

  const zoomIn = () => setScale((s) => Math.min(s + 0.2, 2.5));
  const zoomOut = () => setScale((s) => Math.max(s - 0.2, 0.5));
  const fitWidth = () => setScale(1.0);

  if (!pdfUrl) {
    return (
      <div className="flex items-center justify-center h-full bg-muted/30 rounded-lg" data-testid="analysis-pdf-panel">
        <p className="text-muted-foreground">No document loaded</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full" data-testid="analysis-pdf-panel">
      {/* PDF Controls */}
      <div className="flex items-center justify-between p-3 border-b bg-card">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-sm font-mono">
            {pageNumber} / {numPages || '?'}
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={goToNextPage}
            disabled={pageNumber >= numPages}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-8 h-8 w-40"
              data-testid="pdf-search-input"
            />
          </div>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={zoomOut}
            data-testid="pdf-zoom-out-button"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-xs font-mono w-12 text-center">
            {Math.round(scale * 100)}%
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={zoomIn}
            data-testid="pdf-zoom-in-button"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={fitWidth}>
            <Maximize className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* PDF Content */}
      <ScrollArea className="flex-1 bg-muted/20">
        <div className="flex justify-center p-4">
          {loading && (
            <div className="space-y-4">
              <Skeleton className="h-[600px] w-[450px]" />
            </div>
          )}
          
          {error && (
            <div className="text-destructive text-center p-8">
              <p>{error}</p>
              <Button variant="outline" className="mt-4" onClick={() => setLoading(true)}>
                Retry
              </Button>
            </div>
          )}

          <Document
            file={pdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={null}
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              renderAnnotationLayer={true}
              renderTextLayer={true}
              className="shadow-lg"
            />
          </Document>
        </div>
      </ScrollArea>

      {/* Selected clause indicator */}
      {selectedClause && (
        <div className="p-2 border-t bg-accent/50">
          <p className="text-xs font-mono text-accent-foreground truncate">
            Selected: {selectedClause.title || 'Clause'}
          </p>
        </div>
      )}
    </div>
  );
}
