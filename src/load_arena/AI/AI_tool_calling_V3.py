from pydantic import BaseModel
import pandas as pd
from rich.console import Console
console = Console()

import os
from google import genai
from google.genai import types
if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError(
        "GEMINI_API_KEY is not configured. "
        'Create a Gemini API key, then run: setx GEMINI_API_KEY "YOUR_API_KEY". '
        "Restart your terminal or IDE afterward."
    )

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


def make_get_channel_info(df: pd.DataFrame, Channel_name:str):
    """
    Factory function that returns a function that can be used as a tool.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the channel stats.
    Channel_name : str
        Name of the channel to get info about.

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


def ask_ai(df:pd.DataFrame, Channel_name:str, prompt:str) -> AnalysisResult:
    """
    Ask AI to analyze the channel stats.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the channel stats.
    Channel_name : str
        Name of the channel to get info about.
    prompt : str
        Prompt to ask AI.

    Returns
    -------
    AnalysisResult
        Analysis result.
    """


    # use a factory function to create a tool
    get_channel_info = make_get_channel_info(df, Channel_name)
    get_available_channels = list_channels(df)

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
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
    


    # use a factory function to create a tool
    # get_channel_info = make_get_channel_info(df, Channel_name="WSPgl._[m/s]")
    # get_available_channels = list_channels(df)

    # prompt = "What is the maximum value of WSPgl._[m/s]?"
    prompt =  "Is WSPgl._[m/s] relatively stable or highly variable?"
    # prompt = "What channels are available in the dataset?"
    
    # response = client.models.generate_content(
    #     model="gemini-3.5-flash-lite",
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
    # # console.print(response.text)


    response = ask_ai(df, Channel_name="WSPgl._[m/s]", prompt=prompt)
    result = AnalysisResult.model_validate_json(response.text)
    console.print(result)