from email import charset
from xarray.namedarray import parallelcompat
from pydantic import BaseModel
import pandas as pd
from rich.console import Console
console = Console()

from google import genai
from google.genai import types
client = genai.Client()


from load_arena.data_reader import read_hawc2_flex
from pathlib import Path

class AnalysisResult(BaseModel):
    summary: str
    observations: list[str]
    requires_attention: bool


def get_ai_info(df:pd.DataFrame,
                 Channel_name:str,
                 ) -> dict:
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

    available_channels = df.attrs["channel_names"]


    if Channel_name not in available_channels:
        return {
            "error": f"Channel '{Channel_name}' was not found.",
            "available_channels": available_channels,
        } 

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


def make_get_channel_info(df: pd.DataFrame):
    """
    Factory function that returns a function that can be used as a tool.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the channel stats.

    Returns
    -------
    function
        Function that can be used as a tool.
    """
    

    def get_channel_info(Channel_name: str) -> dict:
        """
        This function is a wrapper around get_ai_info that is used as a tool for the AI.
        """
        return get_ai_info(df, Channel_name)

    return get_channel_info
    



def list_channels(df:pd.DataFrame):

    def get_available_channels() -> list[str]:
        return df.attrs["channel_names"]
    return get_available_channels


def ask_ai(df:pd.DataFrame, prompt:str):
    """
    Ask AI to analyze the channel stats.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the channel stats.
    prompt : str
        Prompt to ask AI.

    Returns
    -------
    AnalysisResult
        Analysis result.
    """

    # Create tools once
    get_channel_info = make_get_channel_info(df)
    get_available_channels = list_channels(df)

    # response = client.models.generate_content(
    #     model="gemini-3.5-flash-lite",  #"gemini-3.5-flash-lite", Gemini 3.1 Flash Lite
    #     contents=prompt,
    #     config=types.GenerateContentConfig(
    #         tools=[
    #             get_channel_info,
    #             get_available_channels,
    #         ],
    #         response_mime_type="application/json",
    #         response_schema=AnalysisResult,
    #     ),
    # )

    # Create one persistent chat
    chat = client.chats.create(
        model="gemini-3.5-flash-lite",
        config=types.GenerateContentConfig(
            tools=[
                get_channel_info,
                get_available_channels,
            ],
            response_mime_type="application/json",
            response_schema=AnalysisResult,
        ),
    )

    return response

if __name__ == "__main__":



    df = read_hawc2_flex(
        Path(r".\tests\h2_res\dlc13\dlc13_wsp04_wdir000_s023004")
    )
    
    result_1 = ask_ai(
        df,
        "Compare flapwise loads on Blade 1 and Blade 2."
    )

    console.print(result_1)

    result_2 = ask_ai(
        chat,
        "Which one had the larger maximum?"
    )

    console.print(result_2)
    

    response = chat.send_message(prompt)

    result = AnalysisResult.model_validate_json(response.text)
    console.print(response.text)
