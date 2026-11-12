import { useState, useCallback, useRef } from 'react';
import { analyzeApi, chatApi } from '../services/api';
import { useAnalysisStore } from '../store/analysisStore';

export function useAnalysis() {
  const [error, setError] = useState(null);
  // Use ref to avoid stale closure issues with chatMessages
  const chatMessagesRef = useRef([]);
  
  const {
    currentDocument,
    currentAnalysis,
    isAnalyzing,
    setCurrentAnalysis,
    setIsAnalyzing,
    setAnalysisProgress,
    chatMessages,
    addChatMessage,
    clearChatMessages,
    chatLoading,
    setChatLoading,
  } = useAnalysisStore();

  // Keep ref in sync
  chatMessagesRef.current = chatMessages;

  const analyze = useCallback(async (documentId, forceReanalyze = false) => {
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setError(null);

    let progressInterval = null;
    try {
      // Simulate progress updates
      progressInterval = setInterval(() => {
        setAnalysisProgress((prev) => Math.min(prev + 5, 90));
      }, 2000);

      const response = await analyzeApi.analyze(documentId, forceReanalyze);

      clearInterval(progressInterval);
      setAnalysisProgress(100);

      if (response.data.success) {
        setCurrentAnalysis(response.data.analysis);
        return response.data;
      } else {
        throw new Error('Analysis failed');
      }
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Analysis failed';
      setError(message);
      throw new Error(message);
    } finally {
      if (progressInterval) clearInterval(progressInterval);
      setIsAnalyzing(false);
    }
  }, [setCurrentAnalysis, setIsAnalyzing, setAnalysisProgress]);

  const getAnalysis = useCallback(async (documentId) => {
    setError(null);
    try {
      const response = await analyzeApi.getAnalysis(documentId);
      if (response.data.success) {
        setCurrentAnalysis(response.data.analysis);
        return response.data;
      }
      return null;
    } catch (err) {
      // Not found is okay - means we need to analyze
      if (err.response?.status !== 404) {
        setError(err.message);
      }
      return null;
    }
  }, [setCurrentAnalysis]);

  const sendChatMessage = useCallback(async (documentId, message) => {
    setChatLoading(true);
    setError(null);

    // Add user message immediately
    addChatMessage({ role: 'user', content: message });

    try {
      // Use ref to get current messages to avoid stale closure
      const history = chatMessagesRef.current.map((m) => ({ role: m.role, content: m.content }));
      const response = await chatApi.send(documentId, message, history);

      if (response.data.success) {
        addChatMessage({ role: 'assistant', content: response.data.response });
        return response.data.response;
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to send message';
      addChatMessage({ role: 'assistant', content: `Error: ${errorMsg}` });
      setError(errorMsg);
    } finally {
      setChatLoading(false);
    }
  }, [addChatMessage, setChatLoading]);

  return {
    currentDocument,
    currentAnalysis,
    isAnalyzing,
    analyze,
    getAnalysis,
    chatMessages,
    sendChatMessage,
    clearChatMessages,
    chatLoading,
    error,
  };
}
