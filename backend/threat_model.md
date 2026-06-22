# STRIDE Threat Model Assessment - Shopping Assistant

This document presents a systematic security architecture assessment of the **Shopping Assistant** application using the STRIDE methodology.

---

## 1. System Decomposition

### System Boundaries
* **User Boundary**: The client-side interface communicating with the FastAPI backend over HTTP/HTTPS.
* **LLM Boundary**: The trust boundary between the application backend and Google GenAI / Vertex AI endpoints.
* **Storage Boundary**: The boundary between the application runtime memory and persistent GCS logs bucket.

### Component Mapping
| Name | Type | Description |
| :--- | :--- | :--- |
| **FastAPI App** | Process | The FastAPI server (`fast_api_app.py`) routing requests. |
| **ReAct Agent Loop** | Process | The Agent orchestration engine (`agent.py`) running the planning loop. |
| **Tool Execution** | Process | Execution of `register_user` and `redeem_discount_code` tools. |
| **DISCOUNT_CODES** | Data Store | In-memory dictionary for tracking discount codes. |
| **REGISTERED_USERS** | Data Store | In-memory set of registered user IDs. |
| **Google GenAI API** | External Entity | The external Vertex AI LLM provider. |
| **GCS Telemetry Bucket** | Data Store | Google Cloud Storage bucket (`gs://{LOGS_BUCKET_NAME}`) for log collection. |

---

## 2. STRIDE Threat Matrix

| STRIDE Category | Threat Description | Likelihood | Impact | Mitigation Status |
| :--- | :--- | :--- | :--- | :--- |
| **S**poofing | Attackers guess or brute-force registered user IDs to redeem single-use codes on behalf of others. | High | Medium | **Unmitigated** (Simple string checks only) |
| **T**ampering | Prompt injection alters agent behavior or bypasses single-use checks. In-memory data structures are inconsistent across multiple workers. | Medium | High | **Unmitigated** |
| **R**epudiation | Lack of non-repudiable logs makes it impossible to verify the actual source/session of a discount redemption. | Medium | Low | **Partially Mitigated** (Standard OTEL logging present) |
| **I**nformation Disclosure | Attackers query the agent to enumerate/harvest registered user IDs. API keys are hardcoded in source files. | High | Medium | **Unmitigated** (Hardcoded mock keys present) |
| **D**enial of Service | Malicious users register millions of random user IDs, exhausting server memory (OOM). | High | High | **Unmitigated** (No limit on user registry size) |
| **E**levation of Privilege | Exploiting the shell run capability or agent tools to execute host system commands. | Low | Critical | **Mitigated** (Hook created to block `rm -rf /` and `mkfs`) |

---

## 3. Detailed Threat Explanations & Actionable Mitigations

### 1. **S**poofing: User ID Impersonation
* **Threat**: The `redeem_discount_code` tool takes a simple `user_id` string but performs no authentication checks. Anyone can specify `user123` or `shopper_jane` to consume their single-use coupons.
* **Mitigation**:
  * Implement authentication tokens (e.g. JWT) passed via request headers.
  * Retrieve the validated `user_id` from the secure session context instead of allowing the LLM agent to pass arbitrary user ID parameters to the tool.

### 2. **T**ampering: In-Memory Inconsistencies & State Bypass
* **Threat**: `DISCOUNT_CODES` and `REGISTERED_USERS` are mutable in-memory variables. If scaled to multiple FastAPI workers, the state will diverge between processes. Prompt injection could also bypass validation constraints.
* **Mitigation**:
  * Move state persistence from in-memory dictionaries to a secure database (e.g., Firestore or Cloud SQL) with transactional integrity.
  * Use strict Pydantic model schemas for tool parameters to prevent injection of malicious structures.

### 3. **R**epudiation: Lack of Redemption Audit Trail
* **Threat**: There is no audit log recording the IP address, timestamp, and session metadata of discount redemptions, preventing fraud resolution.
* **Mitigation**:
  * Write a dedicated security audit log for every transaction event containing IP, user ID, code, and timestamp, sent to a read-only logging database.

### 4. **I**nformation Disclosure: Enumeration Attack & Hardcoded Keys
* **Threat**: Attackers can query the agent repeatedly to verify if a specific `user_id` is registered (enumeration attack). The Gemini API key is hardcoded in `agent.py`.
* **Mitigation**:
  * Return generic error messages (e.g., "Invalid ID or code") to avoid user ID harvesting.
  * Retrieve Gemini/Vertex credentials dynamically from environment variables (`GEMINI_API_KEY`) or GCP IAM service accounts rather than hardcoding them.

### 5. **D**enial of Service: Memory Exhaustion via User Registration
* **Threat**: `register_user` adds strings to an unbounded set in memory. An attacker could automate thousands of requests, crashing the server process due to memory exhaustion.
* **Mitigation**:
  * Implement rate limiting on the FastAPI endpoints (e.g., using `slowapi`).
  * Enforce maximum length constraints on `user_id` inputs.
  * Store users in a database with database-level resource limits.

### 6. **E**levation of Privilege: Unauthorized Tool Usage
* **Threat**: Command injection leading to code execution on the host machine.
* **Mitigation**:
  * Run the application in a sandboxed, low-privilege container.
  * Maintain and enforce the `PreToolUse` hook to block unsafe tool commands.
