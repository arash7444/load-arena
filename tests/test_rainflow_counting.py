import numpy as np
import pandas as pd
from load_arena.process import rainflow_astm

signal = np.array([
    -2.0, 0.0, 1.0, 0.0, -3.0, 0.0,
    5.0, 0.0, -1.0, 0.0, 3.0, 0.0,
    -4.0, 0.0, 4.0, 0.0, -2.0
])

ranges, means = rainflow_astm(signal)

# print(ranges)
# print(means)

df = pd.DataFrame(
        {
            "range": ranges,
            "mean": means,
            "count": np.full(len(ranges), 0.5),
        }
    )

print(df)