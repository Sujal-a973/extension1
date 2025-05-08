"""
Context Manager Module

Manages conversation context and state throughout the interaction.
Handles context persistence, retrieval, and updates.
"""

from langchain.memory import ConversationBufferWindowMemory
from .clarifier import Clarifier

class ConversationManager:
    def __init__(self, llm, k=5):
        # sliding window of the last k user+assistant exchanges
        self.memory = ConversationBufferWindowMemory(k=k, return_messages=True)
        self.clarifier = Clarifier(llm)

    def process_input(self, user_text: str) -> dict:
        # 1. record the new user message
        self.memory.chat_memory.add_user_message(user_text)
        # 2. load the recent chat history
        history = self.memory.load_memory_variables({})["history"]
        # 3. ask the clarifier to decide: question vs. final task
        step = self.clarifier.run(history)
        # 4. save what the assistant "said" (question or task) into memory
        ai_msg = step["message"] if step.get("is_clarification") else step["task"]
        self.memory.chat_memory.add_ai_message(ai_msg)
        # 5. return the clarifier's decision dict
        return step 