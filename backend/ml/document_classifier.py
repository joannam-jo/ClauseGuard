"""Document type classifier."""
import os
import json
import joblib
from pathlib import Path
from typing import List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

from core.config import ML_MODELS_DIR

# Training data for document type classification (60+ samples)
DOC_TYPE_TRAINING_DATA = [
    # ===== Loan agreements =====
    ("This Loan Agreement sets forth the terms of borrowing principal amount interest rate repayment schedule monthly installments", "loan"),
    ("Borrower agrees to repay the loan amount with interest over the specified term of 60 months", "loan"),
    ("The annual percentage rate APR for this loan is 8.5% fixed for the duration", "loan"),
    ("Monthly installment payments of $850 shall be made on the first of each month", "loan"),
    ("Personal loan agreement between lender and borrower for principal sum of $25,000", "loan"),
    ("Mortgage loan for property located at 123 Main Street with 30-year term", "loan"),
    ("Auto loan financing for vehicle purchase with 5-year repayment term", "loan"),
    ("Student loan disbursement agreement with income-driven repayment options", "loan"),
    ("Promissory note for borrowed funds with quarterly payment schedule", "loan"),
    ("Home equity line of credit HELOC agreement with variable draw period", "loan"),
    ("Unsecured personal loan terms repayment over 36 months fixed interest rate", "loan"),
    ("Debt consolidation loan payoff of existing creditors with single monthly payment", "loan"),
    ("Small business loan for equipment purchase with SBA guarantee terms", "loan"),
    ("Payday alternative loan PAL with regulated interest rate and short term", "loan"),
    ("Construction loan for building project with interest only payments during build phase", "loan"),
    ("Bridge loan financing for property purchase with 12 month term balloon payment", "loan"),
    ("Hard money loan for real estate investment with 70% LTV ratio", "loan"),
    ("Veterans Affairs VA loan with zero down payment and competitive rate", "loan"),
    ("FHA insured mortgage loan with 3.5% down payment requirement", "loan"),
    ("Reverse mortgage loan for homeowners aged 62 and older with no monthly payments", "loan"),

    # ===== Lease agreements =====
    ("This Lease Agreement is for rental of the property located at 456 Oak Avenue", "lease"),
    ("Tenant agrees to pay monthly rent of $2000 for the residential premises", "lease"),
    ("Security deposit of one month rent is required prior to occupancy", "lease"),
    ("Landlord shall maintain the property in habitable condition throughout tenancy", "lease"),
    ("Commercial lease for office space comprising 5000 square feet", "lease"),
    ("Equipment lease agreement for industrial machinery with maintenance clause", "lease"),
    ("Vehicle lease with mileage limits and wear and tear provisions", "lease"),
    ("Apartment rental agreement with utilities included in monthly payment", "lease"),
    ("Sublease agreement between primary tenant and subtenant for remainder of term", "lease"),
    ("Triple net lease NNN for commercial property with tenant responsible for expenses", "lease"),
    ("Month to month rental agreement with 30 day termination notice required", "lease"),
    ("Lease to own agreement with portion of rent applied to future purchase", "lease"),
    ("Furnished apartment lease including all appliances and utilities in rent", "lease"),
    ("Short term vacation rental agreement for property use less than 30 days", "lease"),
    ("Roommate agreement outlining shared common area responsibility and rent split", "lease"),
    ("Office space shared lease with coworking amenities and meeting room access", "lease"),
    ("Industrial warehouse lease with loading dock access and 24 hour security", "lease"),
    ("Agricultural land lease for crop cultivation with water rights included", "lease"),
    ("Ground lease for building development on leased land with 99 year term", "lease"),
    ("Rent controlled apartment lease renewal with regulated rent increase limits", "lease"),

    # ===== Credit card agreements =====
    ("This Credit Card Agreement governs the use of your credit card account and all transactions", "credit_card"),
    ("Minimum payment of 2% of outstanding balance or $25 whichever is greater is due monthly", "credit_card"),
    ("Cash advance APR is 24.99% with a 3% transaction fee minimum $10", "credit_card"),
    ("Credit limit may be adjusted based on account history and creditworthiness", "credit_card"),
    ("Rewards program offers 1.5% cash back on all purchases made with the card", "credit_card"),
    ("Balance transfer offer with 0% APR for 12 months and 3% transfer fee", "credit_card"),
    ("Foreign transaction fee of 3% applies to purchases made outside the country", "credit_card"),
    ("Annual fee of $95 waived for first year cardmember benefit", "credit_card"),
    ("Purchase APR ranges from 15.99% to 23.99% based on creditworthiness", "credit_card"),
    ("Credit card cardholder agreement for platinum rewards visa account", "credit_card"),
    ("Business credit card with employee spending controls and expense categorization", "credit_card"),
    ("Student credit card with lower credit limit and credit building tools", "credit_card"),
    ("Secured credit card requiring refundable deposit equal to the credit limit", "credit_card"),
    ("Premium travel rewards card with annual travel credit and lounge access", "credit_card"),
    ("Cash back credit card with rotating quarterly bonus categories 5% back", "credit_card"),
    ("Store credit card redeemable only at specific retailer with 10% first purchase discount", "credit_card"),
    ("Charge card with no preset spending limit and full balance due each month", "credit_card"),
    ("Gold rewards card with points multiplier on dining and grocery purchases", "credit_card"),
    ("Airline co-branded credit card with free checked bag priority boarding", "credit_card"),
    ("Hotel rewards credit card with free night certificate each anniversary year", "credit_card"),
]


class DocumentTypeClassifier:
    """Classifier for document types (loan, lease, credit_card)."""
    
    def __init__(self):
        self.model_path = ML_MODELS_DIR / "doc_type_classifier.joblib"
        self.metrics_path = ML_MODELS_DIR / "doc_type_classifier_metrics.json"
        self.pipeline = None
        self.is_trained = False
        self.metrics = {}
    
    def train(self, custom_data: Optional[List[tuple]] = None) -> dict:
        """Train the classifier."""
        data = custom_data if custom_data else DOC_TYPE_TRAINING_DATA
        
        texts = [t[0] for t in data]
        labels = [t[1] for t in data]
        
        # Create pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=1000,
                stop_words='english'
            )),
            ('clf', SVC(kernel='linear', probability=True, random_state=42))
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
        cv_scores = cross_val_score(self.pipeline, texts, labels, cv=3)
        
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
        """Predict document type."""
        if not self.is_trained:
            self.load_or_train()
        
        prediction = self.pipeline.predict([text])[0]
        probabilities = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        
        prob_dict = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
        
        return {
            'type': prediction,
            'confidence': float(max(probabilities)),
            'probabilities': prob_dict
        }
    
    def save(self):
        """Save the model using joblib (safer than pickle)."""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        # Save model with joblib
        joblib.dump(self.pipeline, self.model_path)
        
        # Save metrics as JSON
        with open(self.metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
    
    def load(self) -> bool:
        """Load the model."""
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
        """Load or train."""
        if not self.load():
            self.train()
            self.save()


# Global instance - initialized to None with type hint
_classifier: Optional[DocumentTypeClassifier] = None


def get_doc_type_classifier() -> DocumentTypeClassifier:
    """Get the classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = DocumentTypeClassifier()
        _classifier.load_or_train()
    return _classifier


def classify_document_type(text: str) -> dict:
    """Classify the type of a document."""
    classifier = get_doc_type_classifier()
    return classifier.predict(text)
