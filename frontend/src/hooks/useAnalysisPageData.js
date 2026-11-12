/**
 * useAnalysisPageData
 * Handles all data-loading concerns for the AnalysisPage:
 *  - fetching the PDF blob URL
 *  - loading or triggering an analysis
 *  - tracking mobile breakpoint
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { uploadApi } from '../services/api';
import { useAnalysisStore } from '../store/analysisStore';
import { useAnalysis } from './useAnalysis';
import { toast } from 'sonner';

export function useAnalysisPageData(documentId) {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loadingPdf, setLoadingPdf] = useState(true);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 1024);

  const initialLoadDone = useRef(false);
  const pdfUrlRef = useRef(null);

  const { isAnalyzing, analysisProgress } = useAnalysisStore();
  const { analyze, getAnalysis } = useAnalysis();

  // Responsive breakpoint tracking
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 1024);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Trigger analysis (re-exported so pages can call it directly)
  const handleAnalyze = useCallback(
    async (force = false) => {
      if (!documentId) return;
      try {
        await analyze(documentId, force);
        toast.success('Analysis complete!');
      } catch (err) {
        toast.error(err.message || 'Analysis failed');
      }
    },
    [documentId, analyze]
  );

  // Initial data load: PDF + existing-or-new analysis
  useEffect(() => {
    if (!documentId || initialLoadDone.current) return;
    initialLoadDone.current = true;

    const loadData = async () => {
      // 1. Fetch PDF blob
      setLoadingPdf(true);
      try {
        const response = await uploadApi.getFile(documentId);
        const url = URL.createObjectURL(response.data);
        pdfUrlRef.current = url;
        setPdfUrl(url);
      } catch (err) {
        console.error('Failed to load PDF:', err);
        toast.error('Failed to load PDF');
      } finally {
        setLoadingPdf(false);
      }

      // 2. Load or trigger analysis
      const existing = await getAnalysis(documentId);
      if (!existing) {
        await handleAnalyze(false);
      }
    };

    loadData();

    // Revoke object URL on cleanup
    return () => {
      if (pdfUrlRef.current) {
        URL.revokeObjectURL(pdfUrlRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  return { pdfUrl, loadingPdf, isMobile, isAnalyzing, analysisProgress, handleAnalyze };
}
