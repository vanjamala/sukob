import os
from typing import Any

from autogen.agentchat import ConversableAgent
from fastagency import UI
from fastagency.runtimes.autogen import AutoGenWorkflows

llm_config = {
    "config_list": [
        {
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
    ],
    "temperature": 0.8,
}

wf = AutoGenWorkflows()


@wf.register(name="simple_learning", description="Student and teacher learning chat")  # type: ignore[misc]
def simple_workflow(ui: UI, params: dict[str, Any]) -> str:
    initial_message = ui.text_input(
        sender="Workflow",
        recipient="User",
        prompt="I can help you learn about mathematics. What subject you would like to explore?",
    )

    student_agent = ConversableAgent(
        name="Student_Agent",
        system_message="You are a student willing to learn.",
        llm_config=llm_config,
    )
    teacher_agent = ConversableAgent(
        name="Teacher_Agent",
        system_message="You are a math teacher.",
        llm_config=llm_config,
    )

    chat_result = student_agent.initiate_chat(
        teacher_agent,
        message=initial_message,
        summary_method="reflection_with_llm",
        max_turns=3,
    )

    return str(chat_result.summary)
