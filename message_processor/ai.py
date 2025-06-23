import logging
import os

from langchain_core.messages import HumanMessage
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from pydantic import SecretStr

from utils import validate_env

llm: ChatOpenAI

logger = logging.getLogger(__name__)

async def check_lead(message):
    system_prompt = SystemMessagePromptTemplate.from_template((
        "You must respond strictly with plaintext only: `true` or `false`. "
        "Evaluate whether the input message is a job offer or lead. This includes: "
        "— Messages offering employment, freelance work, collaboration, gigs, or any form of professional opportunity. "
        "— Messages expressing interest in services, collaboration, or potential business engagement. "
        "Do not explain your answer. Do not include any additional words, characters, or formatting. "
        "Respond with exactly `true` or `false`."
    )).format()
    messages = [
        system_prompt,
        HumanMessage(content=message['text'])
    ]
    try:
        result = (await llm.ainvoke(messages)).content
    except Exception as e:
        logger.warning(f"Failed to process message {message['message_id']} from {message['chat_id']} via llm: {e}")
        result = "false"

    is_lead = "true" in result.strip().lower()
    logger.debug(f"LLM result: {is_lead}")
    return is_lead


async def init_llm():
    global llm
    validate_env("OPENAI_API_KEY")
    llm = ChatOpenAI(
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
        model="gpt-4.1-mini"
    )
