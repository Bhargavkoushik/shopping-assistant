# AI Shopping Assistant

An AI-powered shopping assistant built with Google ADK and Gemini that allows customers to search products, compare specs side-by-side, receive personalized recommendations, and redeem single-use coupons.

---

## 🚀 Project Overview

The **AI Shopping Assistant** is a startup-grade retail demo demonstrating how businesses can leverage agentic AI to power a conversational shopping copilot. By wrapping core business logic and an in-memory product catalog in an intelligent agent framework, the platform enables customers to discover and compare items naturally while securely validating coupons and user accounts.

### Key Capabilities
- **Product Search**: Helps shoppers search through a catalog of items using keywords, maximum price limits, and categories.
- **Side-by-Side Product Comparison**: Allows comparing key features, specifications, and prices of any two products.
- **Personalized Recommendations**: Offers smart recommendations matching user specifications, budgets, and categories.
- **Secure Coupon Redemption**: Validates and applies single-use discount codes dynamically via stateful checks.
- **Paved-Road Security Design**: Shifts security left by defining strict schemas and containment boundaries directly around agent capabilities.

---

## 🏗️ Architecture & Component Flow

```
              User
               │
               ▼
      Streamlit Frontend
               │
               ▼
        Google ADK Agent
               │
               ▼
         Gemini Model
        /     │     \
       /      │      \
  Product  Product   Discount
  Search  Compare   Redeem
```

### Component Responsibilities

1. **Streamlit Frontend**: A polished dark-themed SaaS UI focusing on conversational shopping. It features user profiles, quick action buttons, a coupon display panel, and switchable user accounts.
2. **Google ADK Agent**: Orchestrated using Google's **Agent Development Kit (ADK) 2.0**, utilizing a ReAct planning loop to evaluate user queries and trigger the correct tools (`search_products`, `compare_products`, `recommend_products`, `register_user`, `redeem_discount_code`).
3. **Gemini Model**: Vertex AI / Gemini Flash model providing the underlying reasoning and message parsing.
4. **Agent Tools**: Backend Python logic implementing product catalog lookups, specifications comparison, registration, and discount validation.

---

## 🔒 Security Architecture & Controls

This project implements **5 key security controls** following a shift-left DevSecOps approach, moving all technical validation and threat details out of the consumer interface and into this technical documentation.

### 1. STRIDE Threat Model
Below is the STRIDE threat assessment mapping the application's core attack surface:

| STRIDE Category | Threat Description | Likelihood | Impact | Mitigation Status |
| :--- | :--- | :--- | :--- | :--- |
| **S**poofing | Attackers guess/brute-force registered user IDs to redeem coupons on behalf of others. | High | Medium | **Mitigated in Demo**: Strictly displays registered test accounts. Production requires OAuth/JWT session extraction. |
| **T**ampering | Prompt injection alters agent behavior or bypasses single-use checks. In-memory data structures drift. | Medium | High | **Mitigated**: Core logic resides inside Python validation blocks, not LLM prompts. |
| **R**epudiation | Lack of auditable logs prevents verification of transaction source. | Medium | Low | **Mitigated**: Integrated OpenTelemetry tracing and structured logging for all redemptions. |
| **I**nformation Disclosure | Attackers query the agent to harvest/enumerate registered user IDs or API keys. | High | Medium | **Mitigated**: Safe key isolation via environment variables; error masking on invalid inputs. |
| **D**enial of Service | Unbounded user registration floods memory, causing Out-Of-Memory (OOM) crashes. | High | High | **Mitigated**: String length restrictions and input sanitation at tool boundaries. |
| **E**elevation of Privilege | Command injection leading to remote code execution (RCE) on the host machine. | Low | Critical | **Mitigated**: `PreToolUse` shell execution blocklist filters system requests. |

### 2. Semgrep Secret Detection
We integrate static code analysis scanning via Semgrep.
- **Rule Configuration**: Checks python files on commit to catch hardcoded secrets or API keys.
- **Pattern Matcher**: A custom rule blocks hardcoded Gemini keys matching the `AIzaSy` pattern.
- **Location**: Configuration defined at [backend/.semgrep.yaml](file:///C:/Users/mogal/secure-agent-lab/shopping-assistant/backend/.semgrep.yaml).

### 3. Pre-Commit Verification Gates
To maintain code quality and prevent credentials leakage, the project uses pre-commit hooks:
- **Lint Checks**: Auto-checks formatting, trailing whitespace, and end-of-file markers.
- **Security Scans**: Automatically runs the Semgrep rule suite on every git commit.
- **Location**: Configuration defined at [backend/.pre-commit-config.yaml](file:///C:/Users/mogal/secure-agent-lab/shopping-assistant/backend/.pre-commit-config.yaml).

### 4. Input Parameter Validation
Every agent tool enforces strict parameters using Python typing and validations inside [backend/app/agent.py](file:///C:/Users/mogal/secure-agent-lab/shopping-assistant/backend/app/agent.py):
- Whitespace stripping and emptiness checks prevent null-byte registration.
- Code upper-casing validates patterns (e.g. `WELCOME50`) uniformly.

### 5. Safe Execution Hooks
The ADK agent framework uses runtime hooks to monitor tool execution:
- **PreToolUse Hook**: A script validates command line parameters before executing generic tool processes, stopping shell injection.
- **Registration**: Registered in [backend/.agents/hooks.json](file:///C:/Users/mogal/secure-agent-lab/shopping-assistant/backend/.agents/hooks.json).

---

## 🧪 Testing Strategy

Our testing strategy covers unit functional tests, integration tests, and security boundaries.

### Test Categories
1. **Unit Tests**: Asserts correct discount calculations and checks registration and redemption boundaries. Located in [backend/tests/test_agent.py](file:///C:/Users/mogal/secure-agent-lab/shopping-assistant/backend/tests/test_agent.py).
2. **Integration Tests**: Tests streaming SSE events and user session lifecycle through FastAPI. Located in [backend/tests/integration/](file:///C:/Users/mogal/secure-agent-lab/shopping-assistant/backend/tests/integration/).

### Running Tests
Execute pytest from the `backend/` directory:
```bash
cd backend
uv run pytest tests/test_agent.py tests/unit
```

---

## ⚙️ Setup & Usage Instructions

### Prerequisites
- **Python**: version `3.11` to `3.13`
- **uv**: Python package manager (`pip install uv`)
- **agents-cli**: Installed globally with `uv tool install google-agents-cli`

### Running the Application
1. **Navigate to the backend directory and sync dependencies**:
   ```bash
   cd backend
   uv sync
   ```
2. **Configure credentials**:
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your-api-key"
   ```
3. **Launch the Streamlit frontend**:
   ```bash
   uv run streamlit run ../frontend/streamlit_app.py
   ```
4. **Access the application**: Open `http://localhost:8501` in your browser.
