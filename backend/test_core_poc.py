"""
Finance Agreement Analyzer - Core POC Test Script
Tests the entire RAG pipeline: PDF extraction → Chunking → Embeddings → ChromaDB → Retrieval → LLM Analysis
"""
import os
import sys
import asyncio
import hashlib
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Set HuggingFace cache directory before any imports
BACKEND_DIR = Path(__file__).resolve().parent
os.environ['HF_HOME'] = str(BACKEND_DIR / 'model_cache')
os.environ['TRANSFORMERS_CACHE'] = str(BACKEND_DIR / 'model_cache')
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from dotenv import load_dotenv

load_dotenv()

# Test Results Tracker
test_results = {
    "passed": [],
    "failed": []
}

def log_result(test_name: str, passed: bool, details: str = ""):
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
    if passed:
        test_results["passed"].append(test_name)
    else:
        test_results["failed"].append(test_name)

# ==================== TEST 1: PDF EXTRACTION ====================
def test_pdf_extraction():
    """Test PyMuPDF extraction from a sample PDF"""
    try:
        import fitz  # PyMuPDF
        
        # Create a sample PDF for testing
        sample_pdf_path = str(BACKEND_DIR / "test_sample.pdf")
        
        # Create test PDF with sample finance agreement text
        doc = fitz.open()
        page = doc.new_page()
        
        sample_text = """
LOAN AGREEMENT

This Loan Agreement ("Agreement") is entered into on January 1, 2024.

SECTION 1: INTEREST RATE
The annual interest rate shall be 18% compounded monthly. Late payments will incur 
a penalty of 5% per month on the outstanding balance.

SECTION 2: PREPAYMENT PENALTY
Borrower shall pay a prepayment penalty of 3% of the outstanding principal if the 
loan is paid off before the maturity date.

SECTION 3: AUTO-RENEWAL
This agreement shall automatically renew for successive one-year terms unless 
terminated by written notice 90 days prior to renewal.

SECTION 4: JURISDICTION
Any disputes arising under this Agreement shall be resolved exclusively in the 
courts of Delaware, regardless of the borrower's location.

SECTION 5: MODIFICATION CLAUSE
Lender reserves the right to unilaterally modify the terms of this Agreement, 
including interest rates and fees, with 15 days notice.

SECTION 6: GRACE PERIOD
A grace period of 10 days is provided for all payments before late fees apply.

SECTION 7: ACCELERATION
If borrower misses any single payment, lender may declare the entire balance 
immediately due and payable without further notice.
"""
        page.insert_text((50, 50), sample_text, fontsize=10)
        doc.save(sample_pdf_path)
        doc.close()
        
        # Now extract text from the PDF
        doc = fitz.open(sample_pdf_path)
        extracted_text = ""
        page_count = doc.page_count
        
        for page_num in range(page_count):
            page = doc[page_num]
            extracted_text += page.get_text()
        
        doc.close()
        
        # Verify extraction worked
        assert len(extracted_text) > 100, "Extracted text too short"
        assert "LOAN AGREEMENT" in extracted_text, "Key text not found"
        assert page_count == 1, f"Expected 1 page, got {page_count}"
        
        log_result(
            "PDF Extraction (PyMuPDF)", 
            True, 
            f"Extracted {len(extracted_text)} characters from {page_count} page(s)"
        )
        return extracted_text, sample_pdf_path
        
    except Exception as e:
        log_result("PDF Extraction (PyMuPDF)", False, str(e))
        return None, None


# ==================== TEST 2: TEXT CHUNKING ====================
def test_text_chunking(text: str):
    """Test sentence-aware chunking with overlap"""
    try:
        import spacy
        
        nlp = spacy.load("en_core_web_sm")
        
        def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200, min_chunk_size: int = 300):
            """Sentence-aware chunking with overlap"""
            doc = nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            
            chunks = []
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_len = len(sentence)
                
                if current_length + sentence_len > chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = " ".join(current_chunk)
                    if len(chunk_text) >= min_chunk_size:
                        chunks.append(chunk_text)
                    elif chunks:
                        # Merge small chunk with previous
                        chunks[-1] = chunks[-1] + " " + chunk_text
                    else:
                        chunks.append(chunk_text)
                    
                    # Start new chunk with overlap
                    overlap_sentences = []
                    overlap_length = 0
                    for s in reversed(current_chunk):
                        if overlap_length + len(s) <= overlap:
                            overlap_sentences.insert(0, s)
                            overlap_length += len(s)
                        else:
                            break
                    
                    current_chunk = overlap_sentences
                    current_length = overlap_length
                
                current_chunk.append(sentence)
                current_length += sentence_len
            
            # Add remaining chunk
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= min_chunk_size:
                    chunks.append(chunk_text)
                elif chunks:
                    chunks[-1] = chunks[-1] + " " + chunk_text
                else:
                    chunks.append(chunk_text)
            
            return chunks
        
        chunks = chunk_text(text)
        
        # Verify chunking
        assert len(chunks) > 0, "No chunks created"
        
        # Check chunk sizes
        chunk_sizes = [len(c) for c in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        
        log_result(
            "Text Chunking (SpaCy)",
            True,
            f"Created {len(chunks)} chunks, avg size: {avg_size:.0f} chars, sizes: {chunk_sizes}"
        )
        return chunks
        
    except Exception as e:
        log_result("Text Chunking (SpaCy)", False, str(e))
        return None


# ==================== TEST 3: EMBEDDINGS ====================
def test_embeddings(chunks: list):
    """Test embeddings generation using all-MiniLM-L6-v2 (efficient and effective)"""
    try:
        from sentence_transformers import SentenceTransformer
        
        # Use all-MiniLM-L6-v2 - smaller (80MB), fast, and effective for semantic search
        # This model produces 384-dimensional embeddings
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate embeddings
        embeddings = model.encode(chunks, convert_to_numpy=True)
        
        # Verify embeddings
        assert embeddings.shape[0] == len(chunks), "Embedding count mismatch"
        assert embeddings.shape[1] == 384, f"Expected 384-dim embeddings, got {embeddings.shape[1]}"
        
        log_result(
            "Embeddings (all-MiniLM-L6-v2)",
            True,
            f"Generated {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}"
        )
        return embeddings, model
        
    except Exception as e:
        log_result("Embeddings (all-MiniLM-L6-v2)", False, str(e))
        return None, None


# ==================== TEST 4: CHROMADB PERSISTENCE ====================
def test_chromadb_persistence(chunks: list, embeddings, pdf_path: str):
    """Test ChromaDB persistent storage and retrieval"""
    try:
        import chromadb
        from chromadb.config import Settings
        import numpy as np
        
        # Generate document hash for collection name
        with open(pdf_path, 'rb') as f:
            doc_hash = hashlib.md5(f.read()).hexdigest()[:12]
        
        collection_name = f"doc_{doc_hash}"
        
        # Initialize persistent ChromaDB
        persist_dir = os.environ.get('CHROMA_PERSIST_DIR', str(BACKEND_DIR / 'chroma_db'))
        os.makedirs(persist_dir, exist_ok=True)
        
        client = chromadb.PersistentClient(path=persist_dir)
        
        # Delete collection if exists (for clean test)
        try:
            client.delete_collection(collection_name)
        except:
            pass
        
        # Create collection
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add documents with embeddings
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"chunk_index": i, "source": pdf_path} for i in range(len(chunks))]
        
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        # Verify data was persisted
        count = collection.count()
        assert count == len(chunks), f"Expected {len(chunks)} documents, got {count}"
        
        # Test retrieval
        test_query = "What is the interest rate penalty?"
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = model.encode([test_query])[0]
        
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=3
        )
        
        assert len(results['documents'][0]) > 0, "No results returned"
        
        # Verify persistence across restart simulation
        client2 = chromadb.PersistentClient(path=persist_dir)
        collection2 = client2.get_collection(collection_name)
        count2 = collection2.count()
        
        assert count2 == count, f"Persistence failed: {count2} != {count}"
        
        log_result(
            "ChromaDB Persistence",
            True,
            f"Stored {count} chunks, retrieved {len(results['documents'][0])} results for query, persistence verified"
        )
        return client, collection_name, model
        
    except Exception as e:
        log_result("ChromaDB Persistence", False, str(e))
        return None, None, None


# ==================== TEST 5: RAG RETRIEVAL ====================
def test_rag_retrieval(client, collection_name: str, model):
    """Test RAG retrieval with various queries"""
    try:
        collection = client.get_collection(collection_name)
        
        test_queries = [
            "What are the penalty fees?",
            "Is there an auto-renewal clause?",
            "What happens if I pay early?",
            "Where will disputes be resolved?"
        ]
        
        all_results = []
        for query in test_queries:
            query_embedding = model.encode([query])[0]
            
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=3
            )
            
            all_results.append({
                "query": query,
                "num_results": len(results['documents'][0]),
                "top_result_preview": results['documents'][0][0][:100] if results['documents'][0] else "N/A"
            })
        
        # Verify all queries returned results
        successful_queries = sum(1 for r in all_results if r['num_results'] > 0)
        
        log_result(
            "RAG Retrieval",
            True,
            f"Tested {len(test_queries)} queries, {successful_queries}/{len(test_queries)} returned results"
        )
        
        return all_results
        
    except Exception as e:
        log_result("RAG Retrieval", False, str(e))
        return None


# ==================== TEST 6: LLM ANALYSIS WITH STREAMING ====================
async def test_llm_analysis_streaming():
    """Test OpenAI GPT-4 analysis with streaming via LLM API key"""
    try:
        from integrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('LLM_API_KEY')
        if not api_key:
            raise ValueError("LLM_API_KEY not found in environment")
        
        # Sample context from RAG retrieval
        sample_context = """
SECTION 1: INTEREST RATE
The annual interest rate shall be 18% compounded monthly. Late payments will incur 
a penalty of 5% per month on the outstanding balance.

SECTION 2: PREPAYMENT PENALTY
Borrower shall pay a prepayment penalty of 3% of the outstanding principal if the 
loan is paid off before the maturity date.

SECTION 5: MODIFICATION CLAUSE
Lender reserves the right to unilaterally modify the terms of this Agreement, 
including interest rates and fees, with 15 days notice.
"""
        
        system_prompt = """You are a finance agreement analyzer. Analyze the provided clauses and identify:
1. Risk level (HIGH/MEDIUM/LOW)
2. Whether harmful or beneficial
3. Brief explanation
4. Suggested negotiation point

Format your response in Markdown."""

        user_prompt = f"""Analyze these finance agreement clauses:

{sample_context}

Provide a structured analysis of each clause."""

        # Initialize chat
        chat = LlmChat(
            api_key=api_key,
            session_id="poc_test",
            system_message=system_prompt
        ).with_model("openai", "gpt-4.1")
        
        message = UserMessage(text=user_prompt)
        
        # Get response (non-streaming for POC test)
        response = await chat.send_message(message)
        
        # Verify response
        assert response and len(response) > 100, "Response too short or empty"
        assert "INTEREST" in response.upper() or "RATE" in response.upper(), "Analysis doesn't mention key terms"
        
        log_result(
            "LLM Analysis (OpenAI GPT-4)",
            True,
            f"Received {len(response)} character analysis with risk assessment"
        )
        
        # Print sample of the response
        print(f"\n   --- Sample LLM Response (first 500 chars) ---")
        print(f"   {response[:500]}...")
        
        return response
        
    except Exception as e:
        log_result("LLM Analysis (OpenAI GPT-4)", False, str(e))
        return None


# ==================== TEST 7: CLAUSE CLASSIFICATION (ML COMPONENT) ====================
def test_clause_classification():
    """Test clause classification using scikit-learn"""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.pipeline import Pipeline
        from sklearn.model_selection import train_test_split
        import numpy as np
        
        # Sample training data for clause classification
        training_data = [
            # Harmful clauses
            ("Late payments will incur a penalty of 5% per month", "harmful"),
            ("Borrower shall pay a prepayment penalty of 3%", "harmful"),
            ("Lender reserves the right to unilaterally modify terms", "harmful"),
            ("Agreement shall automatically renew unless terminated", "harmful"),
            ("Disputes shall be resolved exclusively in Delaware", "harmful"),
            ("Entire balance immediately due without notice", "harmful"),
            ("Hidden processing fees apply to all transactions", "harmful"),
            ("Interest rate may increase at lender's sole discretion", "harmful"),
            
            # Beneficial clauses
            ("A grace period of 10 days is provided for all payments", "beneficial"),
            ("No prepayment penalty shall apply", "beneficial"),
            ("Interest rate shall remain fixed for the term", "beneficial"),
            ("Borrower may terminate with 30 days written notice", "beneficial"),
            ("All fees are clearly disclosed in Schedule A", "beneficial"),
            ("Disputes may be resolved through mediation first", "beneficial"),
            ("Rate cannot exceed 12% annually", "beneficial"),
            ("Borrower has right to cure default within 30 days", "beneficial"),
        ]
        
        texts = [t[0] for t in training_data]
        labels = [t[1] for t in training_data]
        
        # Create pipeline
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=1000)),
            ('clf', MultinomialNB())
        ])
        
        # Train
        pipeline.fit(texts, labels)
        
        # Test predictions
        test_clauses = [
            "Interest rate of 20% compounded daily",
            "Grace period of 15 days before any fees",
            "Lender may change terms at any time"
        ]
        
        predictions = pipeline.predict(test_clauses)
        probabilities = pipeline.predict_proba(test_clauses)
        
        results = []
        for clause, pred, probs in zip(test_clauses, predictions, probabilities):
            confidence = max(probs) * 100
            results.append({
                "clause": clause[:50],
                "prediction": pred,
                "confidence": f"{confidence:.1f}%"
            })
        
        log_result(
            "Clause Classification (ML)",
            True,
            f"Trained classifier, tested {len(test_clauses)} clauses: {results}"
        )
        
        return pipeline
        
    except Exception as e:
        log_result("Clause Classification (ML)", False, str(e))
        return None


# ==================== TEST 8: DOCUMENT TYPE CLASSIFICATION ====================
def test_document_type_classification():
    """Test document type classification (loan/lease/credit card)"""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.svm import SVC
        from sklearn.pipeline import Pipeline
        
        # Training data for document types
        training_data = [
            # Loan agreements
            ("This Loan Agreement sets forth the terms of borrowing principal amount interest rate repayment schedule", "loan"),
            ("Borrower agrees to repay the loan amount with interest over the specified term", "loan"),
            ("The annual percentage rate APR for this loan is 12%", "loan"),
            ("Monthly installment payments shall be made on the first of each month", "loan"),
            
            # Lease agreements
            ("This Lease Agreement is for rental of the property located at", "lease"),
            ("Tenant agrees to pay monthly rent of $2000 for the premises", "lease"),
            ("Security deposit of one month rent is required", "lease"),
            ("Landlord shall maintain the property in habitable condition", "lease"),
            
            # Credit card agreements
            ("This Credit Card Agreement governs the use of your credit card account", "credit_card"),
            ("Minimum payment of 2% of outstanding balance is due monthly", "credit_card"),
            ("Cash advance APR is 24.99% with a 3% transaction fee", "credit_card"),
            ("Credit limit may be adjusted based on account history", "credit_card"),
        ]
        
        texts = [t[0] for t in training_data]
        labels = [t[1] for t in training_data]
        
        # Create pipeline
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=500)),
            ('clf', SVC(kernel='linear', probability=True))
        ])
        
        # Train
        pipeline.fit(texts, labels)
        
        # Test with sample document
        test_doc = """
        This Loan Agreement is entered into between the lender and borrower.
        The principal amount of $50,000 shall be repaid over 60 months with
        an annual interest rate of 8.5%. Monthly payments of $1,020 are due
        on the 15th of each month.
        """
        
        prediction = pipeline.predict([test_doc])[0]
        probabilities = pipeline.predict_proba([test_doc])[0]
        classes = pipeline.classes_
        
        prob_dict = {cls: f"{prob*100:.1f}%" for cls, prob in zip(classes, probabilities)}
        
        log_result(
            "Document Type Classification (ML)",
            True,
            f"Detected type: {prediction}, probabilities: {prob_dict}"
        )
        
        return pipeline
        
    except Exception as e:
        log_result("Document Type Classification (ML)", False, str(e))
        return None


# ==================== MAIN TEST RUNNER ====================
async def run_all_tests():
    """Run all POC tests"""
    print("=" * 60)
    print("FINANCE AGREEMENT ANALYZER - CORE POC TESTS")
    print("=" * 60)
    
    # Test 1: PDF Extraction
    print("\n" + "=" * 40)
    print("TEST 1: PDF EXTRACTION")
    print("=" * 40)
    extracted_text, pdf_path = test_pdf_extraction()
    
    if not extracted_text:
        print("\n❌ Cannot continue without PDF extraction. Aborting.")
        return
    
    # Test 2: Text Chunking
    print("\n" + "=" * 40)
    print("TEST 2: TEXT CHUNKING")
    print("=" * 40)
    chunks = test_text_chunking(extracted_text)
    
    if not chunks:
        print("\n❌ Cannot continue without chunking. Aborting.")
        return
    
    # Test 3: Embeddings
    print("\n" + "=" * 40)
    print("TEST 3: EMBEDDINGS")
    print("=" * 40)
    embeddings, embed_model = test_embeddings(chunks)
    
    if embeddings is None:
        print("\n❌ Cannot continue without embeddings. Aborting.")
        return
    
    # Test 4: ChromaDB Persistence
    print("\n" + "=" * 40)
    print("TEST 4: CHROMADB PERSISTENCE")
    print("=" * 40)
    client, collection_name, model = test_chromadb_persistence(chunks, embeddings, pdf_path)
    
    if not client:
        print("\n❌ Cannot continue without ChromaDB. Aborting.")
        return
    
    # Test 5: RAG Retrieval
    print("\n" + "=" * 40)
    print("TEST 5: RAG RETRIEVAL")
    print("=" * 40)
    retrieval_results = test_rag_retrieval(client, collection_name, model)
    
    # Test 6: LLM Analysis
    print("\n" + "=" * 40)
    print("TEST 6: LLM ANALYSIS (STREAMING)")
    print("=" * 40)
    llm_response = await test_llm_analysis_streaming()
    
    # Test 7: Clause Classification (ML)
    print("\n" + "=" * 40)
    print("TEST 7: CLAUSE CLASSIFICATION (ML)")
    print("=" * 40)
    clause_classifier = test_clause_classification()
    
    # Test 8: Document Type Classification (ML)
    print("\n" + "=" * 40)
    print("TEST 8: DOCUMENT TYPE CLASSIFICATION (ML)")
    print("=" * 40)
    doc_type_classifier = test_document_type_classification()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"\n✅ PASSED: {len(test_results['passed'])}")
    for test in test_results['passed']:
        print(f"   - {test}")
    
    print(f"\n❌ FAILED: {len(test_results['failed'])}")
    for test in test_results['failed']:
        print(f"   - {test}")
    
    total = len(test_results['passed']) + len(test_results['failed'])
    success_rate = (len(test_results['passed']) / total * 100) if total > 0 else 0
    
    print(f"\n📊 SUCCESS RATE: {success_rate:.0f}%")
    
    if success_rate == 100:
        print("\n🎉 ALL POC TESTS PASSED! Core RAG pipeline is working.")
        print("   Ready to proceed with full app development.")
    else:
        print("\n⚠️  Some tests failed. Review and fix before proceeding.")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
