from abc import ABC, abstractmethod


class AgentBackend(ABC):
    """
    Abstract interface for agent execution backends.
    """

    @abstractmethod
    def run(
        self,
        language_assignment,
        scenario
    ):
        pass
