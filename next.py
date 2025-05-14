import asyncio
import os

import gradio as gr
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from conversational_layer.context_manager import ConversationManager
from conversational_layer.renderer import render_agent_output
from main_backend.agent.service import Agent
from main_backend.browser.browser import Browser
from main_backend.browser.context import BrowserContext

# ✅ Load environment variables from .env
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# ✅ Initialize the LLM and conversational manager
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
conv_mgr = ConversationManager(llm)

# Define the function to handle user inputs
async def handle_user_input(user_input):
    browser = Browser()
    try:
        step = conv_mgr.process_input(user_input)
        if isinstance(step, dict):
            if step.get("is_clarification"):
                return step.get("message")
            final_task = step.get("task")
        else:
            if getattr(step, "is_clarification", False):
                return getattr(step, "message", "Missing message")
            final_task = getattr(step, "task", None)
        if not final_task:
            return "I wasn't able to understand your request. Please try again."

        context = await browser.new_context()
        agent = Agent(
            task=final_task,
            llm=llm,
            browser_context=context,
            max_actions_per_step=10
        )

        trace = await agent.run(max_steps=50)
        return render_agent_output(trace)

    except Exception as e:
        return f"An error occurred: {str(e)}"

    finally:
        await browser.close()

# Define a synchronous wrapper for the async function
def chatbot_interface(user_input):
    return asyncio.run(handle_user_input(user_input))

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("""# Alfred - by theGoodBrowser\nGet things done with Alfred, now remotely.""")
    chatbot = gr.Chatbot(label="Chat with Alfred", elem_id="chatbot-box")
    with gr.Row():
        text_input = gr.Textbox(show_label=False, placeholder="What do you want to get done?", elem_id="input-box")
        submit_button = gr.Button("Submit", elem_id="submit-btn")

    def user_interaction(message, history):
        response = chatbot_interface(message)
        history.append((message, response))
        return history, history

    text_input.submit(user_interaction, inputs=[text_input, chatbot], outputs=[chatbot, chatbot])
    submit_button.click(user_interaction, inputs=[text_input, chatbot], outputs=[chatbot, chatbot])

# CSS
demo.css = """
#chatbot-box {
    height: 400px;
    overflow-y: auto;
    border-radius: 10px;
    background-color: #f8f9fa;
    padding: 10px;
}
#input-box input {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 10px;
    font-size: 16px;
}
#submit-btn {
    background-color: #fbf7f0;
    color: #f1613f;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
    font-size: 16px;
    cursor: pointer;
}
#submit-btn:hover {
    background-color: #f1613f;
    color: #fbf7f0;
}
body {
    font-family: 'Lexend', serif;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
}
"""

# Launch
if __name__ == "__main__":
    demo.launch(share=False, inbrowser=False)
