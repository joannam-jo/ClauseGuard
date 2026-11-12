import React, { useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Skeleton } from '../components/ui/skeleton';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '../components/ui/resizable';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { PDFViewer } from '../components/PDFViewer';
import { AnalysisDashboard } from '../components/AnalysisDashboard';
import { useAnalysisStore } from '../store/analysisStore';
import { useAnalysis } from '../hooks/useAnalysis';
import { useAnalysisPageData } from '../hooks/useAnalysisPageData';

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function AnalyzingProgressScreen({ progress }) {
  const label =
    progress < 30
      ? 'Extracting text and detecting document type...'
      : progress < 60
      ? 'Analyzing clauses with ML models...'
      : progress < 90
      ? 'Generating risk assessment with AI...'
      : 'Finalizing analysis...';

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <div className="max-w-md w-full text-center space-y-6">
        <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
        <div>
          <h2 className="text-2xl font-semibold mb-2">Analyzing Document</h2>
          <p className="text-muted-foreground">
            Our AI is extracting clauses and evaluating risks. This may take 30–60 seconds.
          </p>
        </div>
        <Progress value={progress} className="h-2" />
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

function PageHeader({ document, onReanalyze, isAnalyzing, compact = false }) {
  const navigate = useNavigate();
  return (
    <div className="p-4 border-b bg-card flex items-center justify-between">
      <div className={`flex items-center ${compact ? 'gap-2' : 'gap-4'}`}>
        <Button variant="ghost" size="icon" onClick={() => navigate('/dashboard')}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1
            className={`font-semibold truncate ${compact ? 'text-sm max-w-[200px]' : 'max-w-[400px]'}`}
          >
            {document?.filename || 'Document'}
          </h1>
          <p className={`text-muted-foreground ${compact ? 'text-xs' : 'text-sm'}`}>
            {document?.document_type}
            {!compact && document?.page_count ? ` • ${document.page_count} pages` : ''}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onReanalyze(true)}
          disabled={isAnalyzing}
          data-testid="reanalyze-button"
        >
          <RefreshCw className="w-4 h-4" />
          {!compact && <span className="ml-2">Re-analyze</span>}
        </Button>
        {!compact && (
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>
        )}
      </div>
    </div>
  );
}

function PdfPanel({ loadingPdf, pdfUrl, selectedClause }) {
  if (loadingPdf) {
    return (
      <div className="flex items-center justify-center h-full">
        <Skeleton className="h-[600px] w-[450px]" />
      </div>
    );
  }
  return <PDFViewer pdfUrl={pdfUrl} selectedClause={selectedClause} />;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AnalysisPage() {
  const { documentId } = useParams();

  const {
    currentDocument,
    currentAnalysis,
    selectedClauseId,
    setSelectedClauseId,
    isAnalyzing: storeIsAnalyzing,
    chatMessages,
    clearChatMessages,
    chatLoading,
  } = useAnalysisStore();

  const { sendChatMessage } = useAnalysis();

  const { pdfUrl, loadingPdf, isMobile, isAnalyzing, analysisProgress, handleAnalyze } =
    useAnalysisPageData(documentId);

  const selectedClause = currentAnalysis?.clauses?.find(
    (c) => c.clause_id === selectedClauseId
  );

  const handleClauseSelect = useCallback(
    (clause) => setSelectedClauseId(clause.clause_id),
    [setSelectedClauseId]
  );

  const handleChatMessage = useCallback(
    (message) => sendChatMessage(documentId, message),
    [documentId, sendChatMessage]
  );

  // Show progress screen while analysis is running
  if (isAnalyzing || storeIsAnalyzing) {
    return <AnalyzingProgressScreen progress={analysisProgress} />;
  }

  const analysisDashboardProps = {
    analysis: currentAnalysis,
    document: currentDocument,
    loading: !currentAnalysis && !isAnalyzing,
    selectedClauseId,
    onClauseSelect: handleClauseSelect,
    chatMessages,
    onSendChatMessage: handleChatMessage,
    onClearChat: clearChatMessages,
    chatLoading,
  };

  // Mobile layout
  if (isMobile) {
    return (
      <div className="flex flex-col h-screen">
        <PageHeader
          document={currentDocument}
          onReanalyze={handleAnalyze}
          isAnalyzing={isAnalyzing}
          compact
        />
        <Tabs defaultValue="analysis" className="flex-1 flex flex-col">
          <TabsList className="mx-4 mt-2">
            <TabsTrigger value="document" className="flex-1">Document</TabsTrigger>
            <TabsTrigger value="analysis" className="flex-1">Analysis</TabsTrigger>
          </TabsList>
          <TabsContent value="document" className="flex-1 m-0">
            <PdfPanel loadingPdf={loadingPdf} pdfUrl={pdfUrl} selectedClause={selectedClause} />
          </TabsContent>
          <TabsContent value="analysis" className="flex-1 m-0 overflow-hidden">
            <AnalysisDashboard {...analysisDashboardProps} />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  // Desktop layout
  return (
    <div className="flex flex-col h-screen">
      <PageHeader
        document={currentDocument}
        onReanalyze={handleAnalyze}
        isAnalyzing={isAnalyzing}
      />
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        <ResizablePanel defaultSize={55} minSize={30}>
          <PdfPanel loadingPdf={loadingPdf} pdfUrl={pdfUrl} selectedClause={selectedClause} />
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={45} minSize={30}>
          <AnalysisDashboard {...analysisDashboardProps} />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
