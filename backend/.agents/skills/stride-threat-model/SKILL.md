---
name: stride-threat-model
description: Performs a systematic STRIDE threat modeling assessment on the current project's codebase and architecture. Use this when starting a new implementation phase or reviewing existing components.
---

# STRIDE Threat Modeling Skill

## Goal
Perform a systematic STRIDE threat modeling assessment on the shopping-assistant agent graph, tools, and endpoints to identify potential security risks and propose specific mitigations.

## Scope of Analysis
1. **System Boundaries**: Identify trust boundaries between the user, the agent, external API endpoints, data storage, and local file systems.
2. **Data Flows**: Track how user inputs, tool responses, LLM queries, and application configurations flow through the system.
3. **Components**:
   - **External Entities**: Users, LLM APIs (e.g. Gemini / Vertex AI), and mock databases/APIs.
   - **Processes**: Fast API Server, ReAct Agent Execution Loop, Custom Python scripts.
   - **Data Stores**: Configuration files (`AGENTS.md`, `pyproject.toml`, `.env`), runtime memory, local logs, and cache directories.

## STRIDE Methodology Guidelines

For each of the STRIDE categories, analyze the shopping-assistant codebase (specifically [app/agent.py](file:///C:/Users/mogal/secure-agent-lab/shopping-assistant/app/agent.py) and [app/fast_api_app.py](file:///C:/Users/mogal/secure-agent-lab/shopping-assistant/app/fast_api_app.py)) and identify potential threats:

### 1. **S**poofing (Impersonation of entities)
- **Threat**: Attackers impersonating legitimate users or spoofing external API callbacks to manipulate the shopping assistant.
- **Questions**: How are incoming requests authenticated? Are API keys (like Google GenAI credentials) safely isolated?

### 2. **T**ampering (Unauthorized modification of data/code)
- **Threat**: Attackers modifying runtime prompts, tool definitions, or dependency configurations (`pyproject.toml`, `uv.lock`) to inject malicious code or hijack the agent's behavior.
- **Questions**: Are tool inputs validated against strict schemas before execution? Are dependencies locked?

### 3. **R**epudiation (Denying actions performed)
- **Threat**: The agent performing actions (like running command lines, calling external endpoints) without sufficient logging to verify who/what initiated the request.
- **Questions**: Are agent decisions, tool invocations, and user interactions adequately logged for auditable traceability?

### 5. **I**nformation Disclosure (Unauthorized exposure of data)
- **Threat**: Exposure of system environment variables, internal server configs, or user-private search terms through verbose logs, unhandled agent errors, or prompt injection.
- **Questions**: Do exception handlers mask detailed system paths/errors? Are secrets excluded from code repositories?

### 5. **D**enial of Service (Disrupting availability)
- **Threat**: Triggering infinite loops in the ReAct planning cycle, sending extremely large payloads, or flooding the fast API endpoints to exhaust resources.
- **Questions**: Are there max-iteration limits on the agent loop? Is there input length/token limit validation?

### 6. **E**levation of Privilege (Gaining unauthorized access)
- **Threat**: The agent executing tool actions (like shell execution, file read/write) with host-level privileges that allow an attacker to hijack the underlying server.
- **Questions**: Does the agent run as a restricted user? Are tool execution permissions minimized?

## Deliverable
When invoked, produce a structured markdown artifact `threat_model.md` in the project root containing:
- **System Decomposition**: A list of identified processes, data stores, external entities, and data flows.
- **Threat Matrix**: A table mapping identified threats to STRIDE categories, indicating likelihood, impact, and mitigation status.
- **Actionable Mitigations**: Concrete security recommendations for the agent codebase (e.g. input sanitation, logging enhancement, validation constraints).
