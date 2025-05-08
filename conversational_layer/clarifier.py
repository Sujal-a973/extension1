"""
Clarifier Module

Handles ambiguity resolution and clarification requests.
Ensures clear understanding of user intents and requirements.
"""

from .templates import CLARIFICATION_PROMPT

class Clarifier:
    def __init__(self, llm):
        # llm: a LangChain LLM chain instance
        self.llm = llm

    def run(self, history: str) -> dict:
        # 1. Format the clarification prompt
        prompt = CLARIFICATION_PROMPT.format(history=history)
        # 2. Call the model
        response = self.llm.predict(prompt)
        # 3. If it starts with æ, treat as clarification question
        if response.strip().startswith("æ"):
            return {"is_clarification": True, "message": response}
        # Otherwise, treat as final task
        else:
            return {"is_clarification": False, "task": response} 