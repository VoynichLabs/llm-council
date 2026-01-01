# CLAUDE.md - Technical Notes for LLM Council

This file contains technical details, architectural decisions, and important implementation notes for future development sessions.

## Project Overview

LLM Council is a 3-stage deliberation system where multiple LLMs collaboratively answer user questions. The key innovation is anonymized peer review in Stage 2, preventing models from playing favorites.

## Architecture

### Backend Structure (`backend/`)

**`config.py`**
- `COUNCIL_MODELS`: List of OpenRouter model identifiers (current defaults below)
- `CHAIRMAN_MODEL`: Model that synthesizes final answer (defaults to first council model)
- `REASONING_EFFORT`: Sets thinking/reasoning level ("high", "medium", "low", "minimal"; defaults to "medium")
- `OPENROUTER_API_KEY`: From environment variable in `.env`
- All config values can be overridden via environment variables:
  - `COUNCIL_MODELS`: Comma-separated list (e.g., `"anthropic/claude-haiku-4.5,openai/gpt-5-mini"`)
  - `CHAIRMAN_MODEL`: Single model ID
  - `REASONING_EFFORT`: Single value (high/medium/low/minimal/none)

**`openrouter.py`**
- `query_model()`: Single async model query with thinking/reasoning support
- `query_models_parallel()`: Parallel queries using `asyncio.gather()`
- Returns dict with 'content' and optional 'reasoning_details'
- Graceful degradation: returns None on failure, continues with successful responses
- Reasoning/thinking: If `REASONING_EFFORT` is set, sends `{"reasoning": {"effort": value}}` to OpenRouter
  - OpenRouter normalizes thinking across providers (OpenAI, Anthropic, Google, Grok, etc.)
  - Reasoning appears in `response.reasoning_details` when supported by model

**`council.py`** - The Core Logic
- `stage1_collect_responses()`: Parallel queries to all council models
- `stage2_collect_rankings()`:
  - Anonymizes responses as "Response A, B, C, etc."
  - Creates `label_to_model` mapping for de-anonymization
  - Prompts models to evaluate and rank (with strict format requirements)
  - Returns tuple: (rankings_list, label_to_model_dict)
  - Each ranking includes both raw text and `parsed_ranking` list
- `stage3_synthesize_final()`: Chairman synthesizes from all responses + rankings
- `parse_ranking_from_text()`: Extracts "FINAL RANKING:" section, handles both numbered lists and plain format
- `calculate_aggregate_rankings()`: Computes average rank position across all peer evaluations

**`storage.py`**
- JSON-based conversation storage in `data/conversations/`
- Each conversation: `{id, created_at, messages[]}`
- Assistant messages contain: `{role, stage1, stage2, stage3}`
- Note: metadata (label_to_model, aggregate_rankings) is NOT persisted to storage, only returned via API

**`main.py`**
- FastAPI app with CORS enabled for localhost:5173 and localhost:3000
- POST `/api/conversations/{id}/message` returns metadata in addition to stages
- Metadata includes: label_to_model mapping and aggregate_rankings

### Frontend Structure (`frontend/src/`)

**`App.jsx`**
- Main orchestration: manages conversations list and current conversation
- Handles message sending and metadata storage
- Important: metadata is stored in the UI state for display but not persisted to backend JSON

**`components/ChatInterface.jsx`**
- Multiline textarea (3 rows, resizable)
- Enter to send, Shift+Enter for new line
- User messages wrapped in markdown-content class for padding

**`components/Stage1.jsx`**
- Tab view of individual model responses
- ReactMarkdown rendering with markdown-content wrapper

**`components/Stage2.jsx`**
- **Critical Feature**: Tab view showing RAW evaluation text from each model
- De-anonymization happens CLIENT-SIDE for display (models receive anonymous labels)
- Shows "Extracted Ranking" below each evaluation so users can validate parsing
- Aggregate rankings shown with average position and vote count
- Explanatory text clarifies that boldface model names are for readability only

**`components/Stage3.jsx`**
- Final synthesized answer from chairman
- Green-tinted background (#f0fff0) to highlight conclusion

**Styling (`*.css`)**
- Light mode theme (not dark mode)
- Primary color: #4a90e2 (blue)
- Global markdown styling in `index.css` with `.markdown-content` class
- 12px padding on all markdown content to prevent cluttered appearance

## Key Design Decisions

### Stage 2 Prompt Format
The Stage 2 prompt is very specific to ensure parseable output:
```
1. Evaluate each response individually first
2. Provide "FINAL RANKING:" header
3. Numbered list format: "1. Response C", "2. Response A", etc.
4. No additional text after ranking section
```

This strict format allows reliable parsing while still getting thoughtful evaluations.

### De-anonymization Strategy
- Models receive: "Response A", "Response B", etc.
- Backend creates mapping: `{"Response A": "openai/gpt-5.1", ...}`
- Frontend displays model names in **bold** for readability
- Users see explanation that original evaluation used anonymous labels
- This prevents bias while maintaining transparency

### Error Handling Philosophy
- Continue with successful responses if some models fail (graceful degradation)
- Never fail the entire request due to single model failure
- Log errors but don't expose to user unless all models fail

### UI/UX Transparency
- All raw outputs are inspectable via tabs
- Parsed rankings shown below raw text for validation
- Users can verify system's interpretation of model outputs
- This builds trust and allows debugging of edge cases

## Important Implementation Details

### Relative Imports
All backend modules use relative imports (e.g., `from .config import ...`) not absolute imports. This is critical for Python's module system to work correctly when running as `python -m backend.main`.

### Port Configuration
- Backend: 8001 (changed from 8000 to avoid conflict)
- Frontend: 5173 (Vite default)
- Update both `backend/main.py` and `frontend/src/api.js` if changing

### Markdown Rendering
All ReactMarkdown components must be wrapped in `<div className="markdown-content">` for proper spacing. This class is defined globally in `index.css`.

### Model Configuration

**Current Council Models** (as of Jan 2026):
- `anthropic/claude-haiku-4.5` - Fast, efficient reasoning
- `google/gemini-3-flash-preview` - Google's latest fast model
- `openai/gpt-5-mini` - OpenAI's efficient GPT-5 variant
- `x-ai/grok-4.1-fast` - Grok's fast variant with large context window

**Chairman Model**: Defaults to `anthropic/claude-haiku-4.5` (first council member)

**Reasoning/Thinking**:
- All queries include `REASONING_EFFORT: "medium"` by default
- OpenRouter normalizes thinking across all providers:
  - OpenAI (gpt-5-*): Uses `reasoning.effort` with budget from `max_thinking_length`
  - Anthropic (claude-*): Uses `reasoning.max_tokens` (1024-32k range)
  - Google (gemini-*): Uses reasoning budget allocation
  - Grok (grok-*): Uses thinking/reasoning when supported
- Models that don't support thinking gracefully ignore the parameter
- For higher-quality answers, increase `REASONING_EFFORT` to "high" via env var

**Overriding Models**:
Override via environment variables in `.env`:
```
COUNCIL_MODELS="openai/gpt-5-mini,anthropic/claude-haiku-4.5,google/gemini-3-flash-preview"
CHAIRMAN_MODEL="openai/gpt-5-mini"
REASONING_EFFORT="high"
```

To list available models on OpenRouter:
```bash
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '.data[].id'
```

## OpenRouter Integration Details

### API Endpoint
- Uses OpenRouter's `POST https://openrouter.ai/api/v1/chat/completions`
- Normalizes model APIs (OpenAI, Anthropic, Google, Grok, etc.) under a single interface
- Non-supported parameters are ignored per provider (graceful degradation)

### Thinking/Reasoning Parameter
```json
{
  "model": "openai/gpt-5-mini",
  "messages": [...],
  "reasoning": {
    "effort": "medium"  // high, medium, low, minimal, or none
  }
}
```

- All models that support extended thinking accept this unified parameter
- OpenRouter converts `effort` to provider-specific configurations internally
- Reasoning output available in `response.reasoning_details` when model supports it

### Response Parsing
- Standard OpenAI-compatible response format
- Reasoning blocks preserved in `message.reasoning_details` (array of thinking tokens)
- These are captured and can be displayed in Stage 1 outputs if needed

## Common Gotchas

1. **Module Import Errors**: Always run backend as `python -m backend.main` from project root, not from backend directory
2. **CORS Issues**: Frontend must match allowed origins in `main.py` CORS middleware
3. **Ranking Parse Failures**: If models don't follow format, fallback regex extracts any "Response X" patterns in order
4. **Missing Metadata**: Metadata is ephemeral (not persisted), only available in API responses
5. **Reasoning Budget**: Increased reasoning effort consumes more tokens; monitor usage if costs become an issue
6. **Model Availability**: Always verify model IDs on OpenRouter before deployment; models change/deprecate frequently

## Future Enhancement Ideas

- Configurable council/chairman via UI instead of config file
- Streaming responses instead of batch loading
- Export conversations to markdown/PDF
- Model performance analytics over time
- Custom ranking criteria (not just accuracy/insight)
- Support for reasoning models (o1, etc.) with special handling

## Testing Notes

Use `test_openrouter.py` to verify API connectivity and test different model identifiers before adding to council. The script tests both streaming and non-streaming modes.

## Data Flow Summary

```
User Query
    ↓
Stage 1: Parallel queries → [individual responses]
    ↓
Stage 2: Anonymize → Parallel ranking queries → [evaluations + parsed rankings]
    ↓
Aggregate Rankings Calculation → [sorted by avg position]
    ↓
Stage 3: Chairman synthesis with full context
    ↓
Return: {stage1, stage2, stage3, metadata}
    ↓
Frontend: Display with tabs + validation UI
```

The entire flow is async/parallel where possible to minimize latency.
