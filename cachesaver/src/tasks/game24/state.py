from dataclasses import dataclass, field
from typing import List

from ...typedefs import State

class StateEnumerator:
    def __init__(self):
        self.state_hashes = []
        self.hash_to_id = {}

    def get_id(self, state: "StateGame24") -> int:
        state_hash = hash(state)
        if state_hash not in self.hash_to_id:
            new_id = len(self.state_hashes)
            self.hash_to_id[state_hash] = new_id
            self.state_hashes.append(state_hash)
        return self.hash_to_id[state_hash]


state_enumerator = StateEnumerator()
@dataclass(frozen=True)
class StateGame24(State):
    # The initial puzzle to solve
    puzzle: str

    # Current state towards solving the puzzle
    current_state: str

    # Steps taken towards solving the puzzle
    steps: List[str]

    # A random number associated with the state
    randomness: int
    
    # A summary of the all reflections over previous trials
    summary: str

    # Context for the state, generated by reflection
    reflections: List[str] = field(default_factory=list)

    value: float | None = None

    def serialize(self) -> dict:
        """
        Returns a dictionary representation of the state.
        """
        return {
            "reflections": self.reflections,
            "current_state": self.current_state,
            "steps": " -> ".join(self.steps),
            "value": self.value,
            "summary": self.summary
        }
    
    def clone(self, randomness: int=None) -> "StateGame24":
        """
        Returns a new instance of GameOf24State with an optional new randomness value.
        """
        return StateGame24(
            puzzle=self.puzzle,
            current_state=self.current_state,
            steps=self.steps,
            randomness=randomness or self.randomness,
            reflections=self.reflections,
            value=self.value,
            summary=self.summary
        )
    
    def get_seed(self) -> int:
        """
        Returns the randomness value associated with the state.
        """
        return self.randomness
    
    def __hash__(self) -> int:
        """
        Returns a hash of the current state.
        """
        return hash(str(self.serialize()))