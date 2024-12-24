import os
from typing import Any

from autogen.agentchat import ConversableAgent
from autogen.oai.openai_utils import filter_config
from fastagency import UI
from fastagency.runtimes.autogen import AutoGenWorkflows
from fastagency.runtimes.autogen.agents.websurfer import WebSurferAgent

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

wf = AutoGenWorkflows()


@wf.register(
    name="web_surfer_prompt", description="Websurfer chat with a simple prompt screen"
)  # type: ignore[misc]
def web_surfer_workflow(ui: UI, params: dict[str, Any]) -> str:
    def is_termination_msg(msg: dict[str, Any]) -> bool:
        return msg["content"] is not None and "TERMINATE" in msg["content"]

    initial_message = ui.text_input(
        sender="Workflow",
        recipient="User",
        prompt="What would you like to explore?",
    )
    conversable_agent = ConversableAgent(
        name="Conversable_Agent",
        llm_config=llm_config,
        human_input_mode="NEVER",
        is_termination_msg=is_termination_msg,
    )
    Web_surfer = WebSurferAgent(
        name="Web_Surfer_Agent",
        llm_config=llm_config,
        summarizer_llm_config=llm_config,
        human_input_mode="NEVER",
        is_termination_msg=is_termination_msg,
        bing_api_key=os.getenv("BING_API_KEY"),
        executor=conversable_agent,  # executor
    )

    chat_result = Web_surfer.initiate_chat(
        conversable_agent,
        message=initial_message,
        summary_method="reflection_with_llm",
        max_turns=3,
    )

    return str(chat_result.summary)
