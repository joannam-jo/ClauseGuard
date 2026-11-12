import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { ScrollArea } from '../components/ui/scroll-area';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { RiskScoreGauge } from './RiskScoreGauge';
import { ClauseRiskCard } from './ClauseRiskCard';
import { ClauseSummaryTable } from './ClauseSummaryTable';
import { ChatInterface } from './ChatInterface';
import { FileText, AlertTriangle, CheckCircle, ListChecks, HelpCircle, Lightbulb } from 'lucide-react';

export function AnalysisDashboard({
  analysis,
  document,
  loading = false,
  selectedClauseId,
  onClauseSelect,
  chatMessages,
  onSendChatMessage,
  onClearChat,
  chatLoading,
}) {
  if (loading) {
    return (
      <div className="p-4 space-y-4" data-testid="analysis-right-panel">
        <div className="flex items-center gap-4">
          <Skeleton className="h-[150px] w-[200px] rounded-xl" />
          <div className="space-y-2 flex-1">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </div>
        <Skeleton className="h-[300px] w-full rounded-xl" />
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex items-center justify-center h-full" data-testid="analysis-right-panel">
        <div className="text-center text-muted-foreground">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No analysis available</p>
          <p className="text-sm mt-1">Upload and analyze a document to see results</p>
        </div>
      </div>
    );
  }

  const recommendationColor = {
    'Safe to Sign': 'text-green-500',
    'Sign': 'text-green-500',
    'Negotiate Terms': 'text-amber-500',
    'Negotiate': 'text-amber-500',
    'Walk Away': 'text-red-500',
    'Consider Alternatives': 'text-red-500',
  };

  return (
    <div className="flex flex-col h-full" data-testid="analysis-right-panel">
      {/* Header with Risk Score */}
      <div className="p-4 border-b bg-card">
        <div className="flex items-start gap-4">
          <RiskScoreGauge score={analysis.overall_risk_score} size={160} />
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant={analysis.overall_rating === 'Good' ? 'secondary' : analysis.overall_rating === 'Bad' ? 'destructive' : 'warning'}>
                {analysis.overall_rating}
              </Badge>
              <span className="text-sm text-muted-foreground">{document?.document_type}</span>
            </div>
            <p className={`text-lg font-semibold ${recommendationColor[analysis.recommendation] || 'text-foreground'}`}>
              {analysis.recommendation}
            </p>
            {analysis.summary && (
              <p className="text-sm text-muted-foreground line-clamp-3">
                {analysis.summary}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Tabs for different views */}
      <Tabs defaultValue="clauses" className="flex-1 flex flex-col">
        <TabsList className="mx-4 mt-4">
          <TabsTrigger value="clauses" className="flex-1">
            Clauses ({analysis.clauses?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="table" className="flex-1">
            Summary Table
          </TabsTrigger>
          <TabsTrigger value="chat" className="flex-1">
            Chat
          </TabsTrigger>
          <TabsTrigger value="checklist" className="flex-1">
            Checklist
          </TabsTrigger>
        </TabsList>

        {/* Clauses Tab */}
        <TabsContent value="clauses" className="flex-1 mt-0">
          <ScrollArea className="h-[calc(100vh-380px)] px-4 pt-4" data-testid="clauses-risk-list">
            <div className="space-y-3 pb-4">
              {analysis.clauses?.length > 0 ? (
                analysis.clauses.map((clause) => (
                  <ClauseRiskCard
                    key={clause.clause_id}
                    clause={clause}
                    isSelected={selectedClauseId === clause.clause_id}
                    onSelect={() => onClauseSelect?.(clause)}
                    onAskInChat={(c) => {
                      onSendChatMessage?.(`Tell me more about this clause: "${c.title}"`);
                    }}
                  />
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No clauses detected</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Summary Table Tab */}
        <TabsContent value="table" className="flex-1 mt-0 px-4 pt-4">
          <ClauseSummaryTable
            clauses={analysis.clauses || []}
            onClauseSelect={onClauseSelect}
            selectedClauseId={selectedClauseId}
          />
        </TabsContent>

        {/* Chat Tab */}
        <TabsContent value="chat" className="flex-1 mt-0 px-4 pt-4 pb-4">
          <div className="h-[calc(100vh-420px)]">
            <ChatInterface
              messages={chatMessages}
              onSendMessage={onSendChatMessage}
              loading={chatLoading}
              onClear={onClearChat}
            />
          </div>
        </TabsContent>

        {/* Checklist Tab */}
        <TabsContent value="checklist" className="flex-1 mt-0">
          <ScrollArea className="h-[calc(100vh-380px)] px-4 pt-4">
            <div className="space-y-4 pb-4">
              {/* Before Signing Checklist */}
              {analysis.checklist?.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-2">
                      <ListChecks className="w-5 h-5 text-primary" />
                      <CardTitle className="text-base">Before Signing Checklist</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {analysis.checklist.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {/* Questions to Ask */}
              {analysis.questions_for_lender?.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-2">
                      <HelpCircle className="w-5 h-5 text-amber-500" />
                      <CardTitle className="text-base">Questions to Ask the Lender</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {analysis.questions_for_lender.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <span className="font-mono text-muted-foreground">{i + 1}.</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {/* Alternatives */}
              {analysis.alternatives_if_refused?.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="w-5 h-5 text-blue-500" />
                      <CardTitle className="text-base">If They Refuse to Negotiate</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {analysis.alternatives_if_refused.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <span className="font-mono text-muted-foreground">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}
