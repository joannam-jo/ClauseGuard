"""Risk scorer for overall document risk assessment."""
import os
import json
import joblib
from pathlib import Path
from typing import List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from core.config import ML_MODELS_DIR

# Training data for risk scoring (text, risk_score 0-10)
RISK_TRAINING_DATA = [
    # High risk (7-10)
    ("Late payments incur penalty of 5% per month. Lender may modify terms unilaterally. No grace period. Mandatory arbitration selected by lender.", 9.0),
    ("Prepayment penalty of 5%. Cross-collateralization with all accounts. Variable rate at lender discretion. Waiver of jury trial.", 8.5),
    ("Auto-renewal without notice. Hidden fees. Acceleration without cure period. Inconvenient jurisdiction.", 8.0),
    ("Interest compounds daily at 24%. Late fee $75 plus 8% of balance. No hardship provisions.", 8.5),
    ("Confession of judgment clause. Security interest in all assets. No right to dispute.", 9.5),
    ("Rate increases automatically 3% annually. Minimum payment trap structure. Early termination fee 10%.", 7.5),
    ("Discretionary interest rate adjustments monthly. Unlimited late fees. No cancellation rights. Mandatory binding arbitration.", 9.0),
    ("Floating interest rate with 25% ceiling. 7% origination fee. Daily compounding. Automatic renewal with 5% penalty.", 8.0),
    ("Balloon payment after 36 months. Deferred interest accrues from day one. Mandatory escrow account fee.", 7.5),
    ("Lender can demand full repayment at any time. No notice required. All personal property as collateral.", 9.5),
    ("Minimum payment covers interest only. Negative amortization. Deferred principal grows unlimited.", 8.5),
    ("Interest rate 29.99% default APR. Retroactive penalty applied to entire balance. No grace period.", 9.0),
    ("Borrower bears all foreign exchange risk. Unlimited rate adjustments. No cap on total interest.", 8.0),
    ("Automatic renewal with fee of $300. No reminder sent. Opt-out window only 10 days before renewal.", 7.5),

    # Medium risk (4-6.9)
    ("Interest rate 18% fixed. Late fee of $35 after 15 day grace period. Standard arbitration clause.", 5.5),
    ("Prepayment penalty 2% in first year only. Annual fee $95. Grace period 10 days.", 5.0),
    ("Variable rate tied to prime plus 12%. Some fees disclosed. Standard terms.", 6.0),
    ("Auto-renewal with 30 day notice required. Moderate late fees. Basic dispute process.", 5.5),
    ("Cross-collateral limited to related accounts. Rate lock for 6 months. Some hidden fees.", 6.5),
    ("Arbitration required but neutral arbiter. Jurisdiction in neighboring state. Moderate penalties.", 4.5),
    ("Interest only payments for first 12 months. Variable rate prime plus 8%. Annual fee $150.", 6.0),
    ("Credit limit may be reviewed annually. Over-limit fee $35. Late payment up to $40.", 5.0),
    ("Balance transfer fee 4% each transfer. Foreign transaction fee 3%. Cash advance fee 5%.", 5.5),
    ("Introductory rate 0% for 6 months then 15.99% variable. Minimum payment 3% of balance.", 4.5),
    ("Origination fee 2% of principal. Prepayment allowed with 1% penalty in first 2 years.", 5.5),
    ("Automatic payment discount 0.25%. Paper statement fee $2 per month. No e-signature waiver.", 4.0),
    ("Monthly service fee $12 unless minimum balance $5000 maintained. ATM fee $3 per withdrawal.", 5.0),
    ("Returned check fee $35. Stop payment fee $30. Cashier check fee $10. Research fee $25.", 4.5),

    # Low risk (0-3.9)
    ("Fixed rate 8%. No prepayment penalty. 30 day grace period. All fees disclosed. Right to cure.", 2.0),
    ("No annual fee. Cash back rewards. Zero liability. Free credit monitoring. Clear terms.", 1.5),
    ("Grace period 21 days. No hidden fees. Hardship program available. Fair dispute resolution.", 2.5),
    ("Rate capped at 12%. No acceleration without 60 day notice and cure period. Transparent fees.", 3.0),
    ("Mediation before arbitration. Local jurisdiction. No prepayment penalty. Rate reduction available.", 2.0),
    ("All terms clearly stated. Consumer-friendly cancellation. No cross-collateralization. Fair rates.", 1.0),
    ("Interest rate below market average. Multiple grace periods. Free balance transfers. No hidden fees.", 1.5),
    ("Standard terms with consumer protections. Reasonable late fees. Clear dispute process.", 3.5),
    ("Fixed rate 5.99% APR. No annual fee. Free automatic payments. 25 day grace period on purchases.", 1.0),
    ("Zero liability fraud protection. Free credit score access. Travel rewards with no blackout dates.", 1.5),
    ("Rate reduction of 2% after 12 on-time payments. No fee balance transfers. Free additional cards.", 2.0),
    ("Clear fee schedule in simple language. No surprise fees. Free customer support 24/7.", 2.5),
    ("Right to cancel within 14 days for full refund. No questions asked return policy.", 1.0),
    ("All rates locked for 5 years. No hidden escalation clauses. Annual cap on total fees.", 2.0),
    ("Personalized financial wellness program included. Free credit counseling sessions annually.", 1.5),
    ("No minimum balance requirement. Free unlimited transactions. No monthly maintenance fee.", 0.5),
]


class RiskScorer:
    """Scorer for document overall risk level."""
    
    def __init__(self):
        self.model_path = ML_MODELS_DIR / "risk_scorer.joblib"
        self.metrics_path = ML_MODELS_DIR / "risk_scorer_metrics.json"
        self.pipeline = None
        self.is_trained = False
        self.metrics = {}
    
    def train(self, custom_data: Optional[List[tuple]] = None) -> dict:
        """Train the risk scorer."""
        data = custom_data if custom_data else RISK_TRAINING_DATA
        
        texts = [t[0] for t in data]
        scores = [t[1] for t in data]
        
        # Create pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=1500,
                stop_words='english'
            )),
            ('regressor', RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            ))
        ])
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            texts, scores, test_size=0.2, random_state=42
        )
        
        # Train
        self.pipeline.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        self.metrics = {
            'mse': float(mse),
            'rmse': float(np.sqrt(mse)),
            'r2': float(r2),
            'train_size': len(X_train),
            'test_size': len(X_test)
        }
        
        self.is_trained = True
        return self.metrics
    
    def predict(self, text: str) -> dict:
        """Predict risk score for a document."""
        if not self.is_trained:
            self.load_or_train()
        
        score = self.pipeline.predict([text])[0]
        score = min(10.0, max(0.0, score))  # Clamp to 0-10
        
        # Determine risk level with default values
        level = 'MEDIUM'
        recommendation = 'Negotiate Terms'
        
        if score <= 3:
            level = 'LOW'
            recommendation = 'Safe to Sign'
        elif score <= 6:
            level = 'MEDIUM'
            recommendation = 'Negotiate Terms'
        else:
            level = 'HIGH'
            recommendation = 'Consider Alternatives'
        
        return {
            'score': round(score, 1),
            'level': level,
            'recommendation': recommendation
        }
    
    def save(self):
        """Save the trained model using joblib (safer than pickle)."""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        # Save model with joblib
        joblib.dump(self.pipeline, self.model_path)
        
        # Save metrics as JSON
        with open(self.metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def load(self) -> bool:
        """Load a trained model."""
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
        """Load or train the model."""
        if not self.load():
            self.train()
            self.save()


# Global instance - initialized to None with type hint
_scorer: Optional[RiskScorer] = None


def get_risk_scorer() -> RiskScorer:
    """Get or create the risk scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
        _scorer.load_or_train()
    return _scorer


def score_document_risk(text: str) -> dict:
    """Score the risk of a document."""
    scorer = get_risk_scorer()
    return scorer.predict(text)
