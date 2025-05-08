"""
Templates Module

Contains predefined templates and formats for conversation elements.
Provides consistent structure for different types of interactions.
"""

CLARIFICATION_PROMPT = """
You are a helpful assistant. Here is our chat so far:
{history}

Ask any follow-up question needed to complete the user's intent,
or if you fully understand, output only the final task description.
- Prefix questions with "æ:"
"""

RESULT_TEMPLATE = """
**✅ Task Complete**

**Actions executed:**
{actions_markdown}

**Results:**
```json
{results_json}
```
""" 