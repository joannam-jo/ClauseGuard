"""
Backend API Testing for Finance Agreement Analyzer
Tests all endpoints including new cookie-based authentication
"""
import requests
import sys
import os
import time
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Resolve paths
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / 'backend'

# Public endpoint (defaults to local server)
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8001/api")

class FinanceAnalyzerTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.tests_run = 0
        self.tests_passed = 0
        self.document_id = None
        self.test_pdf_path = str(BACKEND_DIR / "test_sample.pdf")
        self.session = requests.Session()  # Use session to maintain cookies
        self.test_user_email = f"test_{int(time.time())}@example.com"
        self.test_user_password = "TestPass123!"
        self.test_user_name = "Test User"
        
    def log_test(self, name, passed, details=""):
        """Log test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ PASS: {name}")
        else:
            print(f"❌ FAIL: {name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    # ========================================================================
    # AUTH TESTS (Cookie-based)
    # ========================================================================
    
    def test_register(self):
        """Test POST /api/auth/register - should set httpOnly cookie"""
        print("=" * 60)
        print("Testing Auth Register Endpoint (Cookie-based)")
        print("=" * 60)
        
        try:
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "name": self.test_user_name
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if not data.get('user'):
                    self.log_test("Register - Response Structure", False, "Missing 'user' in response")
                    return False
                
                # Check if cookie was set
                has_cookie = 'session_token' in self.session.cookies
                
                # Check user data
                user = data['user']
                user_valid = (
                    user.get('email') == self.test_user_email and
                    user.get('name') == self.test_user_name and
                    'user_id' in user
                )
                
                if has_cookie and user_valid:
                    self.log_test("Register with Cookie", True, 
                                f"User created: {user.get('email')}, Cookie set: {has_cookie}")
                    return True
                else:
                    self.log_test("Register with Cookie", False, 
                                f"Cookie set: {has_cookie}, User valid: {user_valid}")
                    return False
            else:
                self.log_test("Register with Cookie", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Register with Cookie", False, f"Error: {str(e)}")
            return False
    
    def test_login(self):
        """Test POST /api/auth/login - should set httpOnly cookie"""
        print("=" * 60)
        print("Testing Auth Login Endpoint (Cookie-based)")
        print("=" * 60)
        
        # Clear cookies first to test fresh login
        self.session.cookies.clear()
        
        try:
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if cookie was set
                has_cookie = 'session_token' in self.session.cookies
                
                # Check user data
                user_valid = (
                    data.get('user') and
                    data['user'].get('email') == self.test_user_email
                )
                
                if has_cookie and user_valid:
                    self.log_test("Login with Cookie", True, 
                                f"Login successful, Cookie set: {has_cookie}")
                    return True
                else:
                    self.log_test("Login with Cookie", False, 
                                f"Cookie set: {has_cookie}, User valid: {user_valid}")
                    return False
            else:
                self.log_test("Login with Cookie", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Login with Cookie", False, f"Error: {str(e)}")
            return False
    
    def test_get_me(self):
        """Test GET /api/auth/me - should work with cookie"""
        print("=" * 60)
        print("Testing Auth Me Endpoint (Cookie-based)")
        print("=" * 60)
        
        try:
            response = self.session.get(
                f"{self.base_url}/auth/me",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check user data
                user_valid = (
                    data.get('email') == self.test_user_email and
                    data.get('name') == self.test_user_name and
                    'user_id' in data
                )
                
                if user_valid:
                    self.log_test("Get Me with Cookie", True, 
                                f"User data retrieved: {data.get('email')}")
                    return True
                else:
                    self.log_test("Get Me with Cookie", False, 
                                f"Invalid user data: {data}")
                    return False
            else:
                self.log_test("Get Me with Cookie", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Get Me with Cookie", False, f"Error: {str(e)}")
            return False
    
    def test_logout(self):
        """Test POST /api/auth/logout - should clear cookie"""
        print("=" * 60)
        print("Testing Auth Logout Endpoint")
        print("=" * 60)
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/logout",
                timeout=30
            )
            
            if response.status_code == 200:
                # Check if cookie was cleared
                has_cookie = 'session_token' in self.session.cookies
                
                if not has_cookie:
                    self.log_test("Logout (Cookie Cleared)", True, 
                                "Cookie cleared successfully")
                    return True
                else:
                    self.log_test("Logout (Cookie Cleared)", False, 
                                "Cookie still present after logout")
                    return False
            else:
                self.log_test("Logout (Cookie Cleared)", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Logout (Cookie Cleared)", False, f"Error: {str(e)}")
            return False
    
    def test_me_after_logout(self):
        """Test GET /api/auth/me after logout - should return 401"""
        print("=" * 60)
        print("Testing Auth Me After Logout (Should Fail)")
        print("=" * 60)
        
        try:
            response = self.session.get(
                f"{self.base_url}/auth/me",
                timeout=30
            )
            
            if response.status_code == 401:
                self.log_test("Get Me After Logout (401)", True, 
                            "Correctly returns 401 after logout")
                return True
            else:
                self.log_test("Get Me After Logout (401)", False, 
                            f"Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Get Me After Logout (401)", False, f"Error: {str(e)}")
            return False
    
    # ========================================================================
    # DOCUMENT TESTS
    # ========================================================================
    
    def test_health(self):
        """Test /api/health endpoint"""
        print("=" * 60)
        print("Testing Health Check Endpoint")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test("Health Check", True, f"Status: {response.status_code}, Response: {data}")
                    return True
                else:
                    self.log_test("Health Check", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_upload(self):
        """Test /api/upload endpoint with authentication"""
        print("=" * 60)
        print("Testing Upload Endpoint (Authenticated)")
        print("=" * 60)
        
        # Re-login to get fresh cookie
        login_payload = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        self.session.post(f"{self.base_url}/auth/login", json=login_payload, timeout=30)
        
        # Check if test PDF exists
        if not os.path.exists(self.test_pdf_path):
            self.log_test("Upload - File Check", False, f"Test PDF not found at {self.test_pdf_path}")
            return False
        
        try:
            with open(self.test_pdf_path, 'rb') as f:
                files = {'file': ('test_agreement.pdf', f, 'application/pdf')}
                response = self.session.post(
                    f"{self.base_url}/upload",
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('document'):
                    self.document_id = data['document']['document_id']
                    doc_type = data['document'].get('document_type', 'Unknown')
                    self.log_test("Upload PDF (Authenticated)", True, 
                                f"Document ID: {self.document_id}, Type: {doc_type}")
                    return True
                else:
                    self.log_test("Upload PDF (Authenticated)", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Upload PDF (Authenticated)", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Upload PDF (Authenticated)", False, f"Error: {str(e)}")
            return False
    
    def test_analyze(self):
        """Test /api/analyze endpoint"""
        print("=" * 60)
        print("Testing Analyze Endpoint")
        print("=" * 60)
        
        if not self.document_id:
            self.log_test("Analyze - Document Check", False, "No document_id available")
            return False
        
        try:
            payload = {
                "document_id": self.document_id,
                "force_reanalyze": False
            }
            
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=payload,
                timeout=120  # Analysis can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('analysis'):
                    analysis = data['analysis']
                    risk_score = analysis.get('overall_risk_score', 'N/A')
                    rating = analysis.get('overall_rating', 'N/A')
                    clause_count = len(analysis.get('clauses', []))
                    
                    self.log_test("Analyze Document", True, 
                                f"Risk Score: {risk_score}, Rating: {rating}, Clauses: {clause_count}")
                    return True
                else:
                    self.log_test("Analyze Document", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Analyze Document", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Analyze Document", False, f"Error: {str(e)}")
            return False
    
    def test_get_analysis(self):
        """Test GET /api/analyze/{document_id} endpoint"""
        print("=" * 60)
        print("Testing Get Analysis Endpoint")
        print("=" * 60)
        
        if not self.document_id:
            self.log_test("Get Analysis - Document Check", False, "No document_id available")
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/analyze/{self.document_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('analysis'):
                    self.log_test("Get Analysis", True, "Analysis retrieved successfully")
                    return True
                else:
                    self.log_test("Get Analysis", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Get Analysis", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Get Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_list_documents(self):
        """Test /api/analyze/documents/list endpoint (authenticated)"""
        print("=" * 60)
        print("Testing List Documents Endpoint (Authenticated)")
        print("=" * 60)
        
        try:
            response = self.session.get(
                f"{self.base_url}/analyze/documents/list",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    doc_count = len(data.get('documents', []))
                    self.log_test("List Documents (Authenticated)", True, f"Found {doc_count} documents")
                    return True
                else:
                    self.log_test("List Documents (Authenticated)", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("List Documents (Authenticated)", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("List Documents (Authenticated)", False, f"Error: {str(e)}")
            return False
    
    def test_chat(self):
        """Test /api/chat endpoint"""
        print("=" * 60)
        print("Testing Chat Endpoint")
        print("=" * 60)
        
        if not self.document_id:
            self.log_test("Chat - Document Check", False, "No document_id available")
            return False
        
        try:
            payload = {
                "document_id": self.document_id,
                "message": "What is the interest rate mentioned in this document?",
                "history": []
            }
            
            response = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('response'):
                    response_text = data['response'][:100]
                    self.log_test("Chat Q&A", True, f"Response: {response_text}...")
                    return True
                else:
                    self.log_test("Chat Q&A", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Chat Q&A", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Chat Q&A", False, f"Error: {str(e)}")
            return False
    
    def test_ml_metrics(self):
        """Test /api/ml/metrics endpoint"""
        print("=" * 60)
        print("Testing ML Metrics Endpoint")
        print("=" * 60)
        
        try:
            response = requests.get(
                f"{self.base_url}/ml/metrics",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    metrics = data.get('training_metrics', {})
                    status = data.get('model_status', {})
                    self.log_test("ML Metrics", True, 
                                f"Models: {list(status.keys())}")
                    return True
                else:
                    self.log_test("ML Metrics", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("ML Metrics", False, 
                            f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("ML Metrics", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "=" * 60)
        print("FINANCE AGREEMENT ANALYZER - BACKEND API TESTS")
        print("Testing Cookie-based Authentication & All Endpoints")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Test User: {self.test_user_email}")
        print("=" * 60 + "\n")
        
        # Test 1: Health check
        if not self.test_health():
            print("\n⚠️  Health check failed. Backend may not be running.")
            print("Continuing with other tests...\n")
        
        # Test 2: ML Metrics (doesn't require auth)
        self.test_ml_metrics()
        
        # ===== AUTH TESTS =====
        print("\n" + "=" * 60)
        print("AUTHENTICATION TESTS (Cookie-based)")
        print("=" * 60 + "\n")
        
        # Test 3: Register
        register_success = self.test_register()
        
        # Test 4: Login
        if register_success:
            self.test_login()
        
        # Test 5: Get Me
        self.test_get_me()
        
        # Test 6: Logout
        self.test_logout()
        
        # Test 7: Get Me after logout (should fail)
        self.test_me_after_logout()
        
        # Re-login for document tests
        print("\n" + "=" * 60)
        print("DOCUMENT TESTS (Authenticated)")
        print("=" * 60 + "\n")
        
        # Test 8: Upload
        upload_success = self.test_upload()
        
        # Test 9: List documents
        self.test_list_documents()
        
        # Tests that require a document
        if upload_success and self.document_id:
            # Test 10: Analyze
            self.test_analyze()
            
            # Test 11: Get Analysis
            self.test_get_analysis()
            
            # Test 12: Chat
            self.test_chat()
        else:
            print("\n⚠️  Skipping document-dependent tests (analyze, chat) due to upload failure\n")
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print("=" * 60 + "\n")
        
        return self.tests_passed == self.tests_run


def main():
    tester = FinanceAnalyzerTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
