from src.langtrust.backend.base import AgentBackend
from src.langtrust.agent.simulator import AgentSimulator


class SimulatorBackend(AgentBackend):
    """
    Backend using the internal LangTrust simulator.
    """

    def run(
        self,
        language_assignment,
        scenario
    ):

        agent = AgentSimulator(
            language_assignment=
                language_assignment,
            scenario=scenario
        )

        return agent.run(
            scenario["agent"]["goal"],
            scenario["environment"]["invoice"]["content"],
            scenario["attack"]["payload"]
        )
