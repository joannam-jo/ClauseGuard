"""Clause classifier using scikit-learn."""
import os
import json
import joblib
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

from core.config import ML_MODELS_DIR

# Training data for clause classification (100+ samples)
TRAINING_DATA = [
    # ===== Harmful clauses =====
    ("Late payments will incur a penalty of 5% per month on the outstanding balance", "harmful"),
    ("Borrower shall pay a prepayment penalty of 3% of the outstanding principal", "harmful"),
    ("Lender reserves the right to unilaterally modify the terms of this Agreement", "harmful"),
    ("Agreement shall automatically renew for successive one-year terms unless terminated", "harmful"),
    ("Disputes shall be resolved exclusively in the courts of Delaware", "harmful"),
    ("Entire balance immediately due and payable without further notice", "harmful"),
    ("Hidden processing fees apply to all transactions", "harmful"),
    ("Interest rate may increase at lender's sole discretion", "harmful"),
    ("Borrower waives right to jury trial", "harmful"),
    ("Cross-collateralization with all other accounts held by lender", "harmful"),
    ("Confession of judgment clause allowing lender to enter judgment without notice", "harmful"),
    ("Mandatory arbitration with arbitrator selected by lender", "harmful"),
    ("Variable rate tied to undisclosed internal index", "harmful"),
    ("Fees may be changed at any time without notice", "harmful"),
    ("Lender may accelerate loan upon any breach of any term", "harmful"),
    ("Late fee of $50 plus 10% of payment amount", "harmful"),
    ("Annual fee of $500 non-refundable", "harmful"),
    ("Borrower agrees to pay all collection costs and attorney fees", "harmful"),
    ("Security interest in all current and future assets", "harmful"),
    ("Automatic payment increases of 5% annually", "harmful"),
    ("Mandatory binding arbitration with costs borne by borrower regardless of outcome", "harmful"),
    ("Lender may assign the agreement to any third party without borrower consent", "harmful"),
    ("Minimum usage fee applies even if account is not used", "harmful"),
    ("Borrower must maintain a compensating balance of 10% of the loan amount", "harmful"),
    ("Inactivity fee of $15 per month after 90 days of non-use", "harmful"),
    ("Credit limit may be reduced at any time without notice", "harmful"),
    ("Foreign transaction fee of 5% applies to all international purchases", "harmful"),
    ("Returned payment fee of $50 regardless of the payment amount", "harmful"),
    ("Document preparation fee of $200 non-refundable", "harmful"),
    ("Origination fee of 5% of the loan amount deducted from disbursement", "harmful"),
    ("Lender may offset debt from any accounts held at the institution", "harmful"),
    ("Borrower waives all rights to rescind the agreement after signing", "harmful"),
    ("Automatic debit authorization required with no opt-out option", "harmful"),
    ("Credit insurance fee automatically added unless borrower opts out in writing", "harmful"),
    ("Cash advance fee of 10% of the amount with no cap", "harmful"),
    ("Guarantor required even for qualified borrowers", "harmful"),
    ("Monthly maintenance fee of $25 charged regardless of account activity", "harmful"),
    ("Cure period is limited to 5 days for all defaults", "harmful"),
    ("Borrower waives right to class action participation", "harmful"),
    ("Lender may repossess collateral without prior notice", "harmful"),
    ("Wire transfer fee of $45 for all incoming and outgoing transfers", "harmful"),
    ("Closing costs include a processing fee equal to 2% of the loan value", "harmful"),
    ("Account closure fee of $100 applies within the first 12 months", "harmful"),
    ("Lien placed on all personal property including future acquisitions", "harmful"),
    ("Borrower liable for lender legal fees in any collection action", "harmful"),
    
    # ===== Beneficial clauses =====
    ("A grace period of 10 days is provided for all payments before late fees apply", "beneficial"),
    ("No prepayment penalty shall apply to early payoff", "beneficial"),
    ("Interest rate shall remain fixed for the entire loan term", "beneficial"),
    ("Borrower may terminate with 30 days written notice without penalty", "beneficial"),
    ("All fees are clearly disclosed in Schedule A attached hereto", "beneficial"),
    ("Disputes may be resolved through mediation before arbitration", "beneficial"),
    ("Interest rate cannot exceed 12% annually under any circumstances", "beneficial"),
    ("Borrower has right to cure any default within 30 days of notice", "beneficial"),
    ("No late fee for first late payment each year", "beneficial"),
    ("Free balance transfers for first 6 months", "beneficial"),
    ("Rewards program with 2% cash back on all purchases", "beneficial"),
    ("No annual fee for primary cardholder", "beneficial"),
    ("Zero liability for unauthorized transactions", "beneficial"),
    ("Rate lock guarantee for 60 days", "beneficial"),
    ("Free credit score monitoring included", "beneficial"),
    ("Hardship program available for financial difficulties", "beneficial"),
    ("No penalty for additional principal payments", "beneficial"),
    ("Clear monthly statements with all fees itemized", "beneficial"),
    ("Fair dispute resolution process with neutral arbiter", "beneficial"),
    ("Rate reduction after 12 months of on-time payments", "beneficial"),
    ("Interest rate decreases automatically after 24 on-time payments", "beneficial"),
    ("Automatic payment plan with 0.25% rate discount", "beneficial"),
    ("Free financial counseling included with the account", "beneficial"),
    ("No foreign transaction fees on any purchases worldwide", "beneficial"),
    ("Fraud protection guarantees zero liability for all unauthorized charges", "beneficial"),
    ("Extended warranty coverage on purchases made with the card", "beneficial"),
    ("Purchase protection against damage or theft for 120 days", "beneficial"),
    ("Price protection refunds the difference if an item price drops within 60 days", "beneficial"),
    ("Concierge service available 24/7 for cardholders", "beneficial"),
    ("Travel insurance included for flights booked with the card", "beneficial"),
    ("Cell phone protection when monthly bill is paid with the card", "beneficial"),
    ("Borrower may skip one payment per year without penalty", "beneficial"),
    ("Rate reduction for auto-pay enrollment", "beneficial"),
    ("No charge for copies of statements or documents", "beneficial"),
    ("Credit limit increase available after 6 months with no hard inquiry", "beneficial"),
    ("Free access to credit score and credit report summary", "beneficial"),
    ("Overdraft protection at no additional cost", "beneficial"),
    ("No penalty APR for late payments under 60 days", "beneficial"),
    ("Loyalty bonus of 10,000 points after first year", "beneficial"),
    ("Complimentary airport lounge access with the premium tier", "beneficial"),
    ("Rental car insurance included when using the card for booking", "beneficial"),
    ("Return protection refunds items the merchant won't accept", "beneficial"),
    ("Borrower may request a payment deferral for up to 3 months annually", "beneficial"),
    ("Emergency card replacement and cash advance within 24 hours", "beneficial"),
    ("No minimum interest charge on small balances under $5", "beneficial"),
]


class ClauseClassifier:
    """Classifier for determining if clauses are harmful or beneficial."""
    
    def __init__(self):
        self.model_path = ML_MODELS_DIR / "clause_classifier.joblib"
        self.metrics_path = ML_MODELS_DIR / "clause_classifier_metrics.json"
        self.pipeline = None
        self.is_trained = False
        self.metrics = {}
    
    def train(self, custom_data: Optional[List[Tuple[str, str]]] = None) -> dict:
        """Train the classifier on the training data."""
        data = custom_data if custom_data else TRAINING_DATA
        
        texts = [t[0] for t in data]
        labels = [t[1] for t in data]
        
        # Create pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=2000,
                stop_words='english'
            )),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        
        # Train-test split (skip stratify if too few samples per class)
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42, stratify=labels
            )
        except ValueError:
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42
            )
        
        # Train
        self.pipeline.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(self.pipeline, texts, labels, cv=5)
        
        self.metrics = {
            'accuracy': float(accuracy),
            'cv_mean': float(cv_scores.mean()),
            'cv_std': float(cv_scores.std()),
            'train_size': len(X_train),
            'test_size': len(X_test),
            'report': classification_report(y_test, y_pred, output_dict=True)
        }
        
        self.is_trained = True
        return self.metrics
    
    def predict(self, text: str) -> dict:
        """Predict if a clause is harmful or beneficial."""
        if not self.is_trained:
            self.load_or_train()
        
        prediction = self.pipeline.predict([text])[0]
        probabilities = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        
        prob_dict = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
        
        return {
            'prediction': prediction,
            'confidence': float(max(probabilities)),
            'probabilities': prob_dict
        }
    
    def predict_batch(self, texts: List[str]) -> List[dict]:
        """Predict for multiple clauses."""
        if not self.is_trained:
            self.load_or_train()
        
        predictions = self.pipeline.predict(texts)
        probabilities = self.pipeline.predict_proba(texts)
        classes = self.pipeline.classes_
        
        results = []
        for pred, probs in zip(predictions, probabilities):
            prob_dict = {cls: float(prob) for cls, prob in zip(classes, probs)}
            results.append({
                'prediction': pred,
                'confidence': float(max(probs)),
                'probabilities': prob_dict
            })
        
        return results
    
    def save(self):
        """Save the trained model to disk using joblib (safer than pickle)."""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        # Save model with joblib
        joblib.dump(self.pipeline, self.model_path)
        
        # Save metrics as JSON (safe serialization)
        with open(self.metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
    
    def load(self) -> bool:
        """Load a trained model from disk."""
        if not self.model_path.exists():
            return False
        
        try:
            self.pipeline = joblib.load(self.model_path)
            if self.metrics_path.exists():
                with open(self.metrics_path, 'r') as f:
                    self.metrics = json.load(f)
            else:
                self.metrics = {}
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def load_or_train(self):
        """Load model if exists, otherwise train new one."""
        if not self.load():
            self.train()
            self.save()


# Global instance - initialized to None
_classifier: Optional[ClauseClassifier] = None


def get_clause_classifier() -> ClauseClassifier:
    """Get or create the clause classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = ClauseClassifier()
        _classifier.load_or_train()
    return _classifier


def classify_clause(text: str) -> dict:
    """Classify a single clause."""
    classifier = get_clause_classifier()
    return classifier.predict(text)


def classify_clauses(texts: List[str]) -> List[dict]:
    """Classify multiple clauses."""
    classifier = get_clause_classifier()
    return classifier.predict_batch(texts)
