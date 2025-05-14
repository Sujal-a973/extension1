from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type

from openai import RateLimitError
from pydantic import (BaseModel, ConfigDict, Field, ValidationError,
                      create_model)

from main_backend.browser.browser import Browser, BrowserConfig
from main_backend.browser.views import BrowserStateHistory
from main_backend.controller.registry.views import ActionModel
from main_backend.dom.history_tree_processor.service import (
    DOMElementNode, DOMHistoryElement, HistoryTreeProcessor)
from main_backend.dom.views import SelectorMap
# ✅ NEW IMPORTS for Gmail action execution
from main_backend.gmail.send_email import send_email


@dataclass
class AgentStepInfo:
	step_number: int
	max_steps: int


class ActionResult(BaseModel):
	"""Result of executing an action"""
	is_done: Optional[bool] = False
	extracted_content: Optional[str] = None
	error: Optional[str] = None
	include_in_memory: bool = False


class AgentBrain(BaseModel):
	"""Current state of the agent"""
	evaluation_previous_goal: str
	memory: str
	next_goal: str


class AgentOutput(BaseModel):
	"""Output model for agent"""
	model_config = ConfigDict(arbitrary_types_allowed=True)
	current_state: AgentBrain
	action: list[ActionModel]

	@staticmethod
	def type_with_custom_actions(custom_actions: Type[ActionModel]) -> Type['AgentOutput']:
		return create_model(
			'AgentOutput',
			__base__=AgentOutput,
			action=(list[custom_actions], Field(...)),
			__module__=AgentOutput.__module__,
		)


class AgentHistory(BaseModel):
	"""History item for agent actions"""
	model_output: AgentOutput | None
	result: list[ActionResult]
	state: BrowserStateHistory

	model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())

	@staticmethod
	def get_interacted_element(
		model_output: AgentOutput, selector_map: SelectorMap
	) -> list[DOMHistoryElement | None]:
		elements = []
		for action in model_output.action:
			index = action.get_index()
			if index and index in selector_map:
				el: DOMElementNode = selector_map[index]
				elements.append(HistoryTreeProcessor.convert_dom_element_to_history_element(el))
			else:
				elements.append(None)
		return elements

	def model_dump(self, **kwargs) -> Dict[str, Any]:
		model_output_dump = None
		if self.model_output:
			action_dump = [
				action.model_dump(exclude_none=True) for action in self.model_output.action
			]
			model_output_dump = {
				'current_state': self.model_output.current_state.model_dump(),
				'action': action_dump,
			}

		return {
			'model_output': model_output_dump,
			'result': [r.model_dump(exclude_none=True) for r in self.result],
			'state': self.state.to_dict(),
		}


class AgentHistoryList(BaseModel):
	"""List of agent history items"""
	history: list[AgentHistory]

	def __str__(self) -> str:
		return f'AgentHistoryList(all_results={self.action_results()}, all_model_outputs={self.model_actions()})'

	def __repr__(self) -> str:
		return self.__str__()

	def save_to_file(self, filepath: str | Path) -> None:
		try:
			Path(filepath).parent.mkdir(parents=True, exist_ok=True)
			data = self.model_dump()
			with open(filepath, 'w', encoding='utf-8') as f:
				json.dump(data, f, indent=2)
		except Exception as e:
			raise e

	def model_dump(self, **kwargs) -> Dict[str, Any]:
		return {
			'history': [h.model_dump(**kwargs) for h in self.history],
		}

	@classmethod
	def load_from_file(cls, filepath: str | Path, output_model: Type[AgentOutput]) -> 'AgentHistoryList':
		with open(filepath, 'r', encoding='utf-8') as f:
			data = json.load(f)
		for h in data['history']:
			if h['model_output']:
				if isinstance(h['model_output'], dict):
					h['model_output'] = output_model.model_validate(h['model_output'])
				else:
					h['model_output'] = None
			if 'interacted_element' not in h['state']:
				h['state']['interacted_element'] = None
		history = cls.model_validate(data)
		return history

	def last_action(self) -> None | dict:
		if self.history and self.history[-1].model_output:
			return self.history[-1].model_output.action[-1].model_dump(exclude_none=True)
		return None

	def errors(self) -> list[str]:
		errors = []
		for h in self.history:
			errors.extend([r.error for r in h.result if r.error])
		return errors

	def final_result(self) -> None | str:
		if self.history and self.history[-1].result[-1].extracted_content:
			return self.history[-1].result[-1].extracted_content
		return None

	def is_done(self) -> bool:
		if self.history and len(self.history[-1].result) > 0 and self.history[-1].result[-1].is_done:
			return self.history[-1].result[-1].is_done
		return False

	def has_errors(self) -> bool:
		return len(self.errors()) > 0

	def urls(self) -> list[str]:
		return [h.state.url for h in self.history if h.state.url]

	def screenshots(self) -> list[str]:
		return [h.state.screenshot for h in self.history if h.state.screenshot]

	def action_names(self) -> list[str]:
		return [list(action.keys())[0] for action in self.model_actions()]

	def model_thoughts(self) -> list[AgentBrain]:
		return [h.model_output.current_state for h in self.history if h.model_output]

	def model_outputs(self) -> list[AgentOutput]:
		return [h.model_output for h in self.history if h.model_output]

	def model_actions(self) -> list[dict]:
		outputs = []
		for h in self.history:
			if h.model_output:
				for action in h.model_output.action:
					output = action.model_dump(exclude_none=True)
					outputs.append(output)
		return outputs

	def action_results(self) -> list[ActionResult]:
		results = []
		for h in self.history:
			results.extend([r for r in h.result if r])
		return results

	def extracted_content(self) -> list[str]:
		content = []
		for h in self.history:
			content.extend([r.extracted_content for r in h.result if r.extracted_content])
		return content

	def model_actions_filtered(self, include: list[str] = []) -> list[dict]:
		outputs = self.model_actions()
		result = []
		for o in outputs:
			for i in include:
				if i == list(o.keys())[0]:
					result.append(o)
		return result


class AgentError:
	"""Container for agent error handling"""
	VALIDATION_ERROR = 'Invalid model output format. Please follow the correct schema.'
	RATE_LIMIT_ERROR = 'Rate limit reached. Waiting before retry.'
	NO_VALID_ACTION = 'No valid action found'

	@staticmethod
	def format_error(error: Exception, include_trace: bool = False) -> str:
		if isinstance(error, ValidationError):
			return f'{AgentError.VALIDATION_ERROR}\nDetails: {str(error)}'
		if isinstance(error, RateLimitError):
			return AgentError.RATE_LIMIT_ERROR
		if include_trace:
			return f'{str(error)}\nStacktrace:\n{traceback.format_exc()}'
		return f'{str(error)}'


# ✅ NEW: Execute agent actions (e.g. send_email)
async def execute_agent_actions(agent_output: AgentOutput) -> list[ActionResult]:
	results = []

	browser = Browser(BrowserConfig(cdp_url="http://localhost:9222"))
	playwright_browser = await browser.get_playwright_browser()

	# Find Gmail page
	gmail_page = None
	for context in playwright_browser.contexts:
		for page in context.pages:
			if "mail.google.com" in page.url:
				gmail_page = page
				break
		if gmail_page:
			break

	if not gmail_page:
		context = playwright_browser.contexts[0]
		gmail_page = context.pages[0]
		await gmail_page.goto("https://mail.google.com")

	for action in agent_output.action:
		action_dict = action.model_dump(exclude_none=True)
		if "send_email" in action_dict:
			try:
				data = action_dict["send_email"]
				await send_email(
					gmail_page,
					data.get("to"),
					data.get("subject"),
					data.get("body")
				)
				results.append(ActionResult(
					extracted_content="Email sent successfully.",
					is_done=True,
					include_in_memory=True
				))
			except Exception as e:
				results.append(ActionResult(
					error=f"Failed to send email: {str(e)}",
					is_done=False
				))

	return results
