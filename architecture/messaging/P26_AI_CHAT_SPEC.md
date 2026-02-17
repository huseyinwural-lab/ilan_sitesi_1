# P26: AI Chat Assistant Specification

## 1. AI Moderation Policy
Every message passes through a synchronous AI check before storage.

### 1.1. Filters
*   **Toxicity**: Insults, hate speech.
*   **Fraud**: "Send money via Western Union", "Whatsapp me at...".
*   **Spam**: Copy-paste repetitive text.

### 1.2. Action
*   **Score > 0.9**: Block immediately (HTTP 400).
*   **Score > 0.7**: Flag for review (Store but hide, or `is_hidden=True`).
*   **Score < 0.7**: Allow.

## 2. Smart Reply Engine
Suggest quick responses based on the last message context.

### 2.1. Logic
*   **Input**: Last received message body.
*   **Output**: List of 3 strings.
*   **Examples**:
    *   "Is this still available?" -> ["Yes, it is!", "Yes, but pending.", "Sold, sorry."]
    *   "What is the price?" -> ["Price is firm.", "Make an offer.", "Check description."]

## 3. Implementation
*   **Service**: `AIChatService`.
*   **Model**: Simple Regex/Keyword for MVP, LLM (OpenAI/Claude) for v2 via `integration_agent`.
*   **Latency**: Must return < 50ms. Keyword matching preferred for V1.
