"""Pipeline stage — abstract base for all pipeline stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from content_automata.models import ContentBrief

# Type variables for stage input/output contracts
I = TypeVar("I")
O = TypeVar("O")


class StageContract(ABC, Generic[I, O]):
    """Abstract base class defining the contract for all pipeline stages.

    Each stage receives typed input and produces typed output.
    All stages share a common lifecycle: validate → execute → post_process.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._name: str = self.__class__.__name__

    @property
    def name(self) -> str:
        """Human-readable stage name."""
        return self._name

    @abstractmethod
    def validate_input(self, input_data: I) -> bool:
        """Validate that input meets stage requirements.

        Args:
            input_data: The stage input.

        Returns:
            True if input is valid, False otherwise.
        """
        ...

    @abstractmethod
    def execute(self, input_data: I, brief: ContentBrief) -> O:
        """Execute the stage logic.

        Args:
            input_data: Typed input data.
            brief: Original content brief for context.

        Returns:
            Typed output data.
        """
        ...

    def post_process(self, output: O) -> O:
        """Post-process output before returning.

        Override in subclasses for enrichment, validation, etc.
        Default implementation returns output unchanged.

        Args:
            output: The stage output.

        Returns:
            Processed output.
        """
        return output

    def run(self, input_data: I, brief: ContentBrief) -> O:
        """Full stage lifecycle: validate → execute → post_process.

        Args:
            input_data: Typed input data.
            brief: Original content brief.

        Returns:
            Typed output data.
        """
        if not self.validate_input(input_data):
            raise ValueError(f"Invalid input for stage '{self._name}'")
        output = self.execute(input_data, brief)
        return self.post_process(output)
