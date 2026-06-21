from pathlib import Path
from load_arena.data_reader.hawc2_reader import hawc2_reader

p = Path(
    r"e:\Projects\Git_Arash\load-arena\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004.int"
)
df = hawc2_reader(p)
print("shape:", df.shape)
print(df.head())
