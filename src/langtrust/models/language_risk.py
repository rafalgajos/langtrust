class LanguageRiskModel:
    """
    Experimental model estimating the probability
    of indirect prompt injection success based on
    language configuration.

    This is a placeholder model used to validate
    the LangTrust architecture before connecting
    real LLM agents.
    """

    def calculate(
        self,
        user_instruction,
        tool_description,
        untrusted_content,
        attack_payload,
    ):
        """
        Returns risk score in range [0,1].
        """

        risk = 0.2

        # Same language between attack and content
        # increases semantic alignment.
        if attack_payload == untrusted_content:
            risk += 0.3

        # Same language across the whole context
        # increases consistency.
        if (
            user_instruction
            == tool_description
            == untrusted_content
            == attack_payload
        ):
            risk += 0.3

        # Mixed language scenarios are usually harder.
        unique_languages = len(
            {
                user_instruction,
                tool_description,
                untrusted_content,
                attack_payload,
            }
        )

        if unique_languages > 1:
            risk -= 0.1

        return max(
            0,
            min(1, risk)
        )
