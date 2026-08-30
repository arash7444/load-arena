from load_arena.case_loader import read_uls_input_file
import pandas as pd

def get_ai_info(df:pd.DataFrame, Channel_name:str) -> dict:
    """
    Extract info about a channel stats.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the channel stats.
    Channel_name : str
        Name of the channel to get info about.

    Returns
    -------
    dict
        Dictionary containing the channel info.
    """
    channel_df = df[Channel_name]
    index_ch = df.attrs["channel_names"].index(Channel_name)


    # print(df.attrs.keys()) # for testing

    name_ch =  df.attrs["channel_names"][index_ch]
    unit_ch = df.attrs["units"][index_ch]
    desc_ch = df.attrs["descriptions"][index_ch]

    info = {
    "channel": name_ch,
    "mean": float(channel_df.mean()),
    "std": float(channel_df.std()),
    "minimum": float(channel_df.min()),
    "maximum": float(channel_df.max()),
    "unit": unit_ch,
    "description": desc_ch
    }


    return info


    

def get_channel_info(Channel_name: str) -> dict:
    return get_ai_info(df_1, Channel_name)


def get_available_channels() -> list[str]:
    return df_1.attrs["channel_names"]

if __name__ == "__main__":


    from rich.console import Console
    console = Console()
    from rich.markdown import Markdown

    from load_arena.data_reader import read_hawc2_flex
    from pathlib import Path

    df_1 = read_hawc2_flex(
        Path(r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004")
    )
    # print(df_1.head())

    # this get the info about a channel stats:
    info = get_ai_info(
        df=df_1,
        Channel_name="WSPgl._[m/s]"
    )
    #print(info)


    from google import genai
    from google.genai import types

    client = genai.Client()

    # prompt = "What is the maximum value of WSPgl._[m/s]?"
    # prompt =  "Is WSPgl._[m/s] relatively stable or highly variable?"
    prompt = "What channels are available in the dataset?"
    
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[
                get_channel_info,
                get_available_channels,
            ]
        ),
    )

    console.print(Markdown(response.text))
