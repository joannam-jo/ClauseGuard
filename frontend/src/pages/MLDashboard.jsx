import React, { useState, useEffect } from 'react';
import { Brain, RefreshCw, BarChart3, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { mlApi } from '../services/api';
import { toast } from 'sonner';

export default function MLDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const response = await mlApi.getMetrics();
      if (response.data.success) {
        setMetrics(response.data);
      }
    } catch (err) {
      toast.error('Failed to load ML metrics');
    } finally {
      setLoading(false);
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    try {
      const response = await mlApi.train();
      if (response.data.success) {
        toast.success('Models trained successfully!');
        await loadMetrics();
      }
    } catch (err) {
      toast.error('Training failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setTraining(false);
    }
  };

  const formatAccuracy = (value) => {
    if (typeof value === 'number') {
      return `${(value * 100).toFixed(1)}%`;
    }
    return 'N/A';
  };

  const ModelCard = ({ name, status, description }) => {
    const model = status || {};
    const isTrainedProp = model.is_trained;
    const modelMetrics = model.metrics || {};

    return (
      <Card data-testid={`ml-model-card-${name}`}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-primary" />
              <CardTitle className="text-base">{name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</CardTitle>
            </div>
            <Badge variant={isTrainedProp ? 'secondary' : 'destructive'}>
              {isTrainedProp ? 'Trained' : 'Not Trained'}
            </Badge>
          </div>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          {isTrainedProp && modelMetrics ? (
            <div className="space-y-3">
              {modelMetrics.accuracy !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Accuracy</span>
                  <span className="font-mono font-medium">
                    {formatAccuracy(modelMetrics.accuracy)}
                  </span>
                </div>
              )}
              {modelMetrics.cv_mean !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Cross-Validation Mean</span>
                  <span className="font-mono font-medium">
                    {formatAccuracy(modelMetrics.cv_mean)}
                  </span>
                </div>
              )}
              {modelMetrics.rmse !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">RMSE</span>
                  <span className="font-mono font-medium">
                    {modelMetrics.rmse.toFixed(3)}
                  </span>
                </div>
              )}
              {modelMetrics.r2 !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">R² Score</span>
                  <span className="font-mono font-medium">
                    {modelMetrics.r2.toFixed(3)}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Training Size</span>
                <span className="font-mono font-medium">
                  {modelMetrics.train_size || 'N/A'} samples
                </span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              Model not trained yet. Click "Train Models" to begin.
            </p>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  const modelStatus = metrics?.model_status || {};

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-semibold mb-2 flex items-center gap-3">
              <Brain className="w-8 h-8 text-primary" />
              ML Models Dashboard
            </h1>
            <p className="text-muted-foreground">
              Monitor and train machine learning models for clause analysis
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={loadMetrics} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={handleTrain} disabled={training}>
              {training ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Training...
                </>
              ) : (
                <>
                  <Brain className="w-4 h-4 mr-2" />
                  Train Models
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Training Data Info */}
        {metrics?.training_metrics?.training_data_sizes && (
          <Card className="mb-8">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Training Data Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(metrics.training_metrics.training_data_sizes).map(([model, size]) => (
                  <div key={model} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <span className="text-sm">{model.replace('_', ' ')}</span>
                    <Badge variant="secondary">{size} samples</Badge>
                  </div>
                ))}
              </div>
              {metrics.training_metrics.timestamp && (
                <p className="text-xs text-muted-foreground mt-4">
                  Last trained: {new Date(metrics.training_metrics.timestamp).toLocaleString()}
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Model Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ModelCard
            name="clause_classifier"
            status={modelStatus.clause_classifier}
            description="Classifies clauses as harmful or beneficial using Naive Bayes"
          />
          <ModelCard
            name="risk_scorer"
            status={modelStatus.risk_scorer}
            description="Predicts document risk score (0-10) using Random Forest regression"
          />
          <ModelCard
            name="document_classifier"
            status={modelStatus.document_classifier}
            description="Classifies document type (loan, lease, credit card) using SVM"
          />
        </div>

        {/* Technical Details */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="text-base">Technical Details</CardTitle>
            <CardDescription>ML pipeline architecture for the Finance Agreement Analyzer</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-sm">
              <div>
                <h4 className="font-semibold mb-2">Pipeline Overview</h4>
                <ol className="list-decimal pl-5 space-y-1 text-muted-foreground">
                  <li>PDF Upload → PyMuPDF text extraction (multi-page)</li>
                  <li>Document type auto-detection (loan/lease/credit card)</li>
                  <li>Sentence-aware chunking (1000 chars, 200 overlap)</li>
                  <li>all-MiniLM-L6-v2 embeddings (384-dim)</li>
                  <li>ChromaDB persistent vector storage</li>
                  <li>RAG retrieval (top-5 similar chunks)</li>
                  <li>OpenAI GPT-4 analysis with streaming</li>
                </ol>
              </div>
              <div>
                <h4 className="font-semibold mb-2">ML Models</h4>
                <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                  <li><strong>Clause Classifier:</strong> TF-IDF + Multinomial Naive Bayes (n-grams 1-3)</li>
                  <li><strong>Risk Scorer:</strong> TF-IDF + Random Forest Regressor (100 estimators)</li>
                  <li><strong>Document Classifier:</strong> TF-IDF + SVM with linear kernel</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Evaluation Metrics</h4>
                <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                  <li>Classification: Accuracy, Precision, Recall, F1-Score</li>
                  <li>Regression: RMSE, R² Score</li>
                  <li>Cross-validation: 5-fold CV for classifiers</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
