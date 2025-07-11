import pandas as pd
from typing import Tuple

from .state import StateGame24
from ...typedefs import Benchmark

class BenchmarkGame24(Benchmark):
    def __init__(self, path: str, split: str = "mini"):

        df = pd.read_csv(path, usecols=["Puzzles"], compression="gzip")
        df.reset_index(inplace=True)
        data = list(zip(df['index'], df['Puzzles']))

        if  split == "single":
            self.data = data[:1]
        elif split == "two":
            self.data = data[:2]
        elif split == "mini":
            self.data = data[:25]
        elif split == "mid":
            self.data = data[:50]
        elif split == "train":
            self.data = data[850:875] + data[1025:1050]
        elif split == "validation":
            self.data = data[875:900] + data[1000:1025]
        elif split == "test":
            self.data = data[900:1000]
        else:
            raise ValueError("Invalid set name")

    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx) -> Tuple[int, StateGame24]:
        index = self.data[idx][0]
        x = self.data[idx][1]

        # Create a state object
        # Note: Left None for randomness, which enforces a state.clone() call in the algorithm
        state = StateGame24(
            puzzle=x,
            current_state=x,
            steps=[],
            randomness=None,
            summary=""
        )
        return index, state
    
    