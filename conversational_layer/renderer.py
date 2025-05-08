"""
Renderer Module

Handles the presentation and formatting of conversation outputs.
Manages how information is displayed to the user.
"""

import json
from .templates import RESULT_TEMPLATE

def render_agent_output(agent_trace: dict) -> str:
    """
    agent_trace should contain:
        - 'actions': a list of strings describing each action
        - 'results': a dict or JSON-serializable data structure
    """
    # Format actions as a numbered Markdown list
    actions = agent_trace.get('actions', [])
    actions_markdown = ''
    if actions:
        actions_markdown = '\n'.join(f"{i+1}. {a}" for i, a in enumerate(actions))
    # Serialize results as pretty JSON
    results_json = json.dumps(agent_trace.get('results', {}), indent=2)
    # Render with the RESULT_TEMPLATE
    return RESULT_TEMPLATE.format(
        actions_markdown=actions_markdown,
        results_json=results_json
    ) 