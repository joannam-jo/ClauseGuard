import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAnalysisStore = create(
  persist(
    (set, get) => ({
      // Current document state
      currentDocument: null,
      currentAnalysis: null,
      isAnalyzing: false,
      analysisProgress: 0,
      
      // Document list
      documents: [],
      documentsLoading: false,
      
      // Selected clause
      selectedClauseId: null,
      
      // Chat state
      chatMessages: [],
      chatLoading: false,
      
      // Actions
      setCurrentDocument: (doc) => set({ currentDocument: doc }),
      setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
      setIsAnalyzing: (status) => set({ isAnalyzing: status }),
      setAnalysisProgress: (progress) => set({ analysisProgress: progress }),
      
      setDocuments: (docs) => set({ documents: docs }),
      setDocumentsLoading: (loading) => set({ documentsLoading: loading }),
      
      setSelectedClauseId: (id) => set({ selectedClauseId: id }),
      
      addChatMessage: (message) =>
        set((state) => ({ chatMessages: [...state.chatMessages, message] })),
      clearChatMessages: () => set({ chatMessages: [] }),
      setChatLoading: (loading) => set({ chatLoading: loading }),
      
      // Reset all state
      reset: () =>
        set({
          currentDocument: null,
          currentAnalysis: null,
          isAnalyzing: false,
          analysisProgress: 0,
          selectedClauseId: null,
          chatMessages: [],
          chatLoading: false,
        }),
    }),
    {
      name: 'analysis-store',
      partialize: (state) => ({
        // Only persist these fields
        documents: state.documents,
      }),
    }
  )
);

export const useThemeStore = create(
  persist(
    (set) => ({
      theme: 'light',
      toggleTheme: () =>
        set((state) => {
          const newTheme = state.theme === 'light' ? 'dark' : 'light';
          document.documentElement.classList.toggle('dark', newTheme === 'dark');
          return { theme: newTheme };
        }),
      setTheme: (theme) => {
        document.documentElement.classList.toggle('dark', theme === 'dark');
        set({ theme });
      },
    }),
    {
      name: 'theme-store',
    }
  )
);

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      logout: () => {
        set({ user: null, isAuthenticated: false });
      },
      clearUser: () => {
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
