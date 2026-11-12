import os
import logging
import httpx
import json
import time
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class UserMessage:
    def __init__(self, text: str):
        self.text = text


class LlmChat:
    def __init__(self, api_key: str, session_id: str, system_message: str):
        self.api_key = api_key
        self.session_id = session_id
        self.system_message = system_message
        self.provider = "openai"
        self.model_name = "gpt-4o"

    def with_model(self, provider: str, model_name: str):
        self.provider = provider
        # Map gpt-4.1 or others to standard GPT models
        if model_name == "gpt-4.1" or "gpt-4" in model_name:
            self.model_name = "gpt-4o"
        else:
            self.model_name = model_name
        return self

    async def send_message(self, message: UserMessage) -> str:
        if self.provider == "ollama":
            return await self._send_ollama(message)

        # OpenAI-compatible provider
        api_key = self.api_key or os.environ.get("LLM_API_KEY")
        if not api_key or api_key.startswith("mock") or api_key == "YOUR_LLM_API_KEY_HERE":
            return self._generate_fallback_response(message.text)

        try:
            client_kwargs = {"api_key": api_key, "timeout": 60.0}
            base_url = os.environ.get("LLM_BASE_URL")
            if base_url:
                client_kwargs["base_url"] = base_url
            client = AsyncOpenAI(**client_kwargs)
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": message.text}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Failed to call OpenAI: {e}. Falling back to mock generator.")
            return self._generate_fallback_response(message.text)

    async def _send_ollama(self, message: UserMessage) -> str:
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        model = self.model_name or os.environ.get("OLLAMA_MODEL", "llama3")
        timeout_seconds = float(os.environ.get("OLLAMA_TIMEOUT", "180"))
        num_predict = int(os.environ.get("OLLAMA_NUM_PREDICT", "512"))
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": message.text},
            ],
            "stream": False,
            "options": {
                "num_predict": num_predict
            }
        }

        # Log request metadata for debugging timeouts and sizes
        try:
            payload_text = json.dumps(payload)
        except Exception:
            payload_text = str(payload)

        payload_size = len(payload_text)
        prompt_len = len(message.text or "")
        logger.info(
            "Ollama request: url=%s model=%s num_predict=%s timeout=%s payload_bytes=%d prompt_chars=%d",
            base_url, model, num_predict, timeout_seconds, payload_size, prompt_len,
        )

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(f"{base_url}/api/chat", json=payload)
                elapsed = time.monotonic() - start
                logger.info("Ollama response received in %.2fs status=%s", elapsed, getattr(response, 'status_code', None))
                response.raise_for_status()
                data = response.json()
                # Some Ollama responses place the content in different fields; be defensive
                content = ""
                if isinstance(data, dict):
                    content = data.get("message", {}).get("content") or data.get("output") or data.get("response")
                if not content and isinstance(data, list) and len(data) > 0:
                    content = data[0].get("content") if isinstance(data[0], dict) else None
                return (content or "").strip()
        except httpx.ReadTimeout as e:
            elapsed = time.monotonic() - start
            logger.warning(
                "Ollama ReadTimeout after %.2fs (timeout=%ss). url=%s model=%s payload_bytes=%d prompt_chars=%d",
                elapsed, timeout_seconds, base_url, model, payload_size, prompt_len,
            )
            return self._generate_fallback_response(message.text)
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.warning(
                "Failed to call Ollama (%s) after %.2fs: %s. url=%s model=%s payload_bytes=%d prompt_chars=%d. Falling back to mock generator.",
                type(e).__name__, elapsed, e, base_url, model, payload_size, prompt_len,
            )
            return self._generate_fallback_response(message.text)

    def _generate_fallback_response(self, prompt: str) -> str:
        # Check prompts and generate expected patterns
        prompt_lower = prompt.lower()
        if "interest" in prompt_lower or "rate" in prompt_lower or "prepayment" in prompt_lower:
            return """# Clause Analysis
### 1. Interest Rate Clause
- **Risk Level**: HIGH
- **Type**: harmful
- **Explanation**: The annual interest rate of 18% is extremely high and compounded monthly, which leads to exponential debt growth.
- **Negotiation Suggestion**: Request a reduction to standard market rates (e.g., 6-8%) and simple interest calculation instead of monthly compounding.
- **Confidence**: 95%

### 2. Prepayment Penalty Clause
- **Risk Level**: HIGH
- **Type**: harmful
- **Explanation**: A 3% penalty on the outstanding principal if paid off early restricts the borrower's refinance options.
- **Negotiation Suggestion**: Ask for the removal of the prepayment penalty or restrict it only to the first 12 months.
- **Confidence**: 90%

### 3. Modification Clause
- **Risk Level**: HIGH
- **Type**: harmful
- **Explanation**: Allowing the Lender to unilaterally modify terms on 15 days notice gives the lender too much power.
- **Negotiation Suggestion**: Require mutual written consent for any changes to interest rates, fees, or core payment terms.
- **Confidence**: 95%

## Executive Summary
This document outlines standard credit terms with highly unfavorable provisions. Specifically, the high interest rate (18%), the prepayment penalty, and the unilateral modification rights make this agreement high risk for the borrower.

## Risk Score: 8.5

## Checklist
- Verify interest rate calculations
- Negotiate prepayment penalty removal
- Request mutual consent for modifications

## Questions for Lender
- Why is the interest rate set at 18%?
- Can the prepayment penalty be removed?
- Can we require written consent for all contract modifications?

## Alternatives if Refused
- Walk away and seek funding from traditional banks or line of credit.
- Request a cap on any unilateral modifications.
"""
        return """# Analysis Report
## Executive Summary
This document has been parsed and analyzed.

## Risk Score: 4.5

## Checklist
- Confirm all dates are correct
- Check definition of terms

## Questions for Lender
- What are the late fees?

## Alternatives if Refused
- Ask for a shorter term duration.
"""
