"""Model training utilities and evaluation."""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from core.config import ML_MODELS_DIR
from ml.clause_classifier import ClauseClassifier, TRAINING_DATA as CLAUSE_DATA
from ml.risk_scorer import RiskScorer, RISK_TRAINING_DATA as RISK_DATA
from ml.document_classifier import DocumentTypeClassifier, DOC_TYPE_TRAINING_DATA as DOC_DATA


def train_all_models() -> Dict[str, dict]:
    """Train all ML models and return metrics."""
    results = {}
    
    # Train clause classifier
    print("Training clause classifier...")
    clause_clf = ClauseClassifier()
    results['clause_classifier'] = clause_clf.train()
    clause_clf.save()
    print(f"  Accuracy: {results['clause_classifier']['accuracy']:.2%}")
    
    # Train risk scorer
    print("Training risk scorer...")
    risk_scorer = RiskScorer()
    results['risk_scorer'] = risk_scorer.train()
    risk_scorer.save()
    print(f"  RMSE: {results['risk_scorer']['rmse']:.2f}")
    
    # Train document type classifier
    print("Training document type classifier...")
    doc_clf = DocumentTypeClassifier()
    results['document_classifier'] = doc_clf.train()
    doc_clf.save()
    print(f"  Accuracy: {results['document_classifier']['accuracy']:.2%}")
    
    # Save combined metrics
    metrics_path = ML_MODELS_DIR / "training_metrics.json"
    results['timestamp'] = datetime.now().isoformat()
    results['training_data_sizes'] = {
        'clause_classifier': len(CLAUSE_DATA),
        'risk_scorer': len(RISK_DATA),
        'document_classifier': len(DOC_DATA)
    }
    
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results


def get_training_metrics() -> Optional[dict]:
    """Get the latest training metrics."""
    metrics_path = ML_MODELS_DIR / "training_metrics.json"
    if not metrics_path.exists():
        return None
    
    with open(metrics_path, 'r') as f:
        return json.load(f)


def evaluate_models() -> Dict[str, dict]:
    """Evaluate all models on their test data."""
    from sklearn.model_selection import cross_val_score
    
    results = {}
    
    # Clause classifier
    clause_clf = ClauseClassifier()
    clause_clf.load_or_train()
    results['clause_classifier'] = {
        'metrics': clause_clf.metrics,
        'model_path': str(clause_clf.model_path),
        'is_trained': clause_clf.is_trained
    }
    
    # Risk scorer
    risk_scorer = RiskScorer()
    risk_scorer.load_or_train()
    results['risk_scorer'] = {
        'metrics': risk_scorer.metrics,
        'model_path': str(risk_scorer.model_path),
        'is_trained': risk_scorer.is_trained
    }
    
    # Document classifier
    doc_clf = DocumentTypeClassifier()
    doc_clf.load_or_train()
    results['document_classifier'] = {
        'metrics': doc_clf.metrics,
        'model_path': str(doc_clf.model_path),
        'is_trained': doc_clf.is_trained
    }
    
    return results


if __name__ == "__main__":
    print("=" * 50)
    print("TRAINING ALL ML MODELS")
    print("=" * 50)
    
    results = train_all_models()
    
    print("\n" + "=" * 50)
    print("TRAINING COMPLETE")
    print("=" * 50)
    
    for model_name, metrics in results.items():
        if isinstance(metrics, dict) and 'accuracy' in metrics:
            print(f"\n{model_name}:")
            print(f"  Accuracy: {metrics.get('accuracy', 'N/A'):.2%}")
            print(f"  CV Mean: {metrics.get('cv_mean', 'N/A'):.2%}")
        elif isinstance(metrics, dict) and 'rmse' in metrics:
            print(f"\n{model_name}:")
            print(f"  RMSE: {metrics.get('rmse', 'N/A'):.2f}")
            print(f"  R2: {metrics.get('r2', 'N/A'):.2f}")
