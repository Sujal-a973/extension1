from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class BaseTelemetryEvent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def properties(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if k != "name"}


@dataclass
class RegisteredFunction:
    name: str
    params: dict[str, Any]


@dataclass
class ControllerRegisteredFunctionsTelemetryEvent(BaseTelemetryEvent):
    registered_functions: list[RegisteredFunction]
    name: str = "action_taken"


@dataclass
class AgentRunTelemetryEvent(BaseTelemetryEvent):
    agent_id: str
    task: str
    name: str = "task_run"


@dataclass
class AgentStepErrorTelemetryEvent(BaseTelemetryEvent):
    agent_id: str
    error: str
    name: str = "task_error"


@dataclass
class AgentEndTelemetryEvent(BaseTelemetryEvent):
    agent_id: str
    task: str
    steps: int
    success: bool
    error: Optional[str] = None
    name: str = "task_success"
