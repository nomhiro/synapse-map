from typing import Sequence
from typing_extensions import Self

from autogen_agentchat.messages import BaseChatMessage, BaseAgentEvent
from autogen_agentchat.messages import TextMessage, StopMessage
from autogen_agentchat.base import TerminationCondition
from pydantic import BaseModel


class AgentCountTerminationConfig(BaseModel):
    agent_name: str
    max_count: int = 1


class AgentCountTermination(TerminationCondition):
    """
    指定のエージェントが max_count 以上発話した時点で会話を終了させる。
    """
    def __init__(self, agent_name: str, max_count: int):
        self._target_source = agent_name
        self._max_count = max_count
        self._count = 0
        self._terminated = False

    @property
    def terminated(self) -> bool:
        return self._terminated

    async def __call__(self, messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> StopMessage | None:
        for message in messages:
            if isinstance(message, TextMessage) and (self._target_source is None or self._target_source == message.source):
                self._count += 1
                if self._count >= self._max_count:
                    self._terminated = True
                    return StopMessage(content=f"Agent '{self._target_source}' has been called {self._count} time(s).", source="AgentCountTermination")

        return None

    async def reset(self) -> None:
        self._count = 0
        self._terminated = False

    def _to_config(self) -> AgentCountTerminationConfig:
        return AgentCountTerminationConfig(agent_name=self._target_source, max_count=self._max_count)

    @classmethod
    def _from_config(cls, config: AgentCountTerminationConfig) -> Self:
        return cls(agent_name=config.agent_name, max_count=config.max_count)