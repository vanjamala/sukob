# Now you can safely use pandas
import io
import json
import os
from typing import Any, Optional

import mesop as me
import pandas as pd
from autogen.agentchat import ConversableAgent
from autogen.oai.openai_utils import filter_config
from fastagency import UI
from fastagency.runtimes.autogen import AutoGenWorkflows
from fastagency.runtimes.autogen.agents.websurfer import WebSurferAgent
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

OAI_CONFIG_LIST = [{"model": "gpt-4o-mini", "api_key": os.getenv("OPENAI_API_KEY")}]

llm_config = {
    "timeout": 600,
    "cache_seed": 44,  # change the seed for different trials
    "config_list": filter_config(
        OAI_CONFIG_LIST, filter_dict={"model": ["gpt-4o-mini"]}
    ),
    "temperature": 0,
}


summarizer_llm_config = {
    "timeout": 600,
    "cache_seed": 44,  # change the seed for different trials
    "config_list": filter_config(
        OAI_CONFIG_LIST, filter_dict={"model": ["gpt-4o-mini"]}
    ),
    "temperature": 0,
}

print(os.getenv("BING_API_KEY"))  # Check if the API key is correctly retrieved


@me.stateclass
class State:
    file: me.UploadedFile


def load(e: me.LoadEvent) -> None:
    me.set_theme_mode("system")


wf = AutoGenWorkflows()

task1 = """
Please search the internet for sites mentioning people listed in table that you will access with registered function import_table.
Do not visit Dun & Bradstreet site.
Please summarize their roles in this format

json_data_sukob = '''
[
    {
      "Name": "Name1",
      "Institution": "Institution1",
      "Findings": "Findings1",
      "Links": "relevant links1"
    },
    {
      "Name": "Name 2",
      "Institution": "Institution2",
      "Findings": "Findings2",
      "Links": "relevant links2"
    },
    ...,
    {
      "Name": "Name n",
      "Institution": "Institution n",
      "Findings": "Findings n",
      "Links": "relevant linksn"
     }
  ]
'''
Then access function sukob_output_table to pass json_data_sukob as an argument in order to create a df and then export it to excel on google drive.
"""
conversable_agent = ConversableAgent(
    name="Conversable_Agent",
    llm_config=llm_config,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: msg["content"] is not None
    and "TERMINATE" in msg["content"],
)

web_surfer = WebSurferAgent(
    name="Web_Surfer_Agent",
    llm_config=llm_config,
    summarizer_llm_config=llm_config,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: msg["content"] is not None
    and "TERMINATE" in msg["content"],
    bing_api_key=os.getenv("BING_API_KEY"),
    executor=conversable_agent,  # executor
)


def import_table() -> Optional[str]:
    """Reads an Excel table from a specified file on Google Drive and returns it as a JSON string.

    Returns:
        A JSON string representation of the Excel table if successful, or None if an error occurs.
    """
    try:
        # Path to the service account key JSON file
        SERVICE_ACCOUNT_FILE = "./credentials/algebravm20230415-30bf03c40517.json"  # Replace with your actual file name

        # Authenticate using the service account key
        credentials = service_account.Credentials.from_service_account_file(  # type: ignore [no-untyped-call]
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )

        # Build the Google Drive API service
        service = build("drive", "v3", credentials=credentials)

        # Specify the file ID of the Excel file on Google Drive (replace with your actual file ID)
        file_id = "1BUmA3-pj4nQVy616NP3avFLjE-mH3Gxw"

        # Request the file from Google Drive
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO(request.execute())  # Read the file into memory

        # Read the Excel file directly from the in-memory file
        df = pd.read_excel(file)  # Use pandas to read the Excel file

        print("File successfully loaded!")
        print(df)

        # Convert the DataFrame to a JSON string
        df_json = df.to_json(orient="records")
        print(df_json)

        return df_json  # type: ignore[no-any-return]

    except HttpError as err:
        print(f"An error occurred: {err}")
        return None
    except Exception as e:
        print(f"Error loading the file: {e}")
        return None


def sukob_output_table(json_data_sukob: str) -> None:
    try:
        # Path to the service account key JSON file
        SERVICE_ACCOUNT_FILE = "./credentials/algebravm20230415-30bf03c40517.json"  # Replace with your actual service account file

        # Authenticate using the service account credentials
        credentials = service_account.Credentials.from_service_account_file(  # type: ignore [no-untyped-call]
            SERVICE_ACCOUNT_FILE,
            scopes=[
                "https://www.googleapis.com/auth/drive.file"
            ],  # Drive file scope for uploading
        )

        # Build the Google Drive API service
        service = build("drive", "v3", credentials=credentials)

        # Load the JSON data into a DataFrame
        data = json.loads(json_data_sukob)
        summary_df = pd.DataFrame(data)

        # Save the DataFrame as an Excel file locally
        local_path = "summary_sukob.xlsx"
        summary_df.to_excel(local_path, index=False)
        print(f"Local path of the file: {local_path}")

        # Specify the folder ID on Google Drive where the file should be uploaded
        folder_id = "14KsPXt3yecsuPmQJAnHU1PPzP7ahm_11"

        # Create the file metadata (name, folder, etc.)
        file_metadata = {
            "name": "summary_sukob.xlsx",
            "parents": [folder_id],  # The folder in which the file will be uploaded
        }

        # Create the MediaFileUpload object for the file to be uploaded
        media = MediaFileUpload(
            local_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Upload the file to Google Drive
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        print(f'File successfully uploaded to Google Drive with file ID: {file["id"]}')

    except Exception as e:
        print(f"Error uploading the file: {e}")


conversable_agent.register_for_execution(name="import_table")(import_table)
web_surfer.register_for_llm(
    name="import_table", description="Import table from specified file path"
)(import_table)
conversable_agent.register_for_execution(name="sukob_output_table")(sukob_output_table)
web_surfer.register_for_llm(
    name="sukob_output_table", description="Upload table to specified file path"
)(sukob_output_table)


@wf.register(
    name="web_surfer_prompt", description="Websurfer chat with a simple prompt screen"
)  # type: ignore[misc]
def web_surfer_workflow(ui: UI, params: dict[str, Any]) -> str:
    def is_termination_msg(msg: dict[str, Any]) -> bool:
        return msg["content"] is not None and "TERMINATE" in msg["content"]

    #    initial_message = ui.text_input(
    #       sender="Workflow",
    #        recipient="User",
    #       prompt="What would you like to explore?",
    #    )

    chat_result = web_surfer.initiate_chat(
        conversable_agent,
        message=task1,
        summary_method="reflection_with_llm",
        max_turns=3,
    )

    return str(chat_result.summary)
