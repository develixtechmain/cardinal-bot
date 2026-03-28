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
    system_prompt = SystemMessagePromptTemplate.from_template(
        (
            "You must respond strictly with plaintext only: true or false.\n\n"
            "You are evaluating Telegram messages to determine whether they are genuine job offers or business leads. Think step by step before answering:\n\n"
            "1. Is the sender clearly looking to hire, contract, or find a collaborator — not offering or promoting their own services?\n"
            "2. Does the message describe a specific paid task, job, role, or professional opportunity?\n"
            "3. Is there a clear business context or project that requires outside help?\n"
            "4. Does it avoid vague or hype language like “join the team,” “big opportunity,” “launching something,” or “let’s grow together” without specifics?\n"
            "5. Does it avoid sales pitches, promotions, or personal introductions?\n"
            "6. Does the message look legitimate and not suspicious, fraudulent, or illegal in nature? For example, does it avoid requests for personal or financial information, unreasonably high promises, or anything that seems like a scam?\n\n"
            "If the message fails any of these checks, classify it as false.\n\n"
            "Examples:\n"
            "true → “Looking for a designer to help with Telegram channel branding. Payment negotiable.”\n"
            "true → “Seeking a crypto copywriter for a paid part-time project.”\n"
            "false → “I offer packaging and promotion services. DM me.”\n"
            "false → “Open to offers. I do targeting and design.”\n"
            "false → “Looking for ambitious partners to build a business. No experience needed. Full training provided.”\n"
            "false → “Please send your ID and bank details to proceed with the job application.”\n"
            "false → “Earn $1000/day working from home. Just send money to get started.”\n"
            "false → “Go through the route, leave markers and coordinates. Payment 5000.”\n"
            "false → “Deliver packages to designated points. Payment is guaranteed.”\n\n"
            "Do not include your reasoning in the output. Do not explain your answer. Do not add any words or formatting. Respond with exactly true or false."
        )
    ).format()
    messages = [system_prompt, HumanMessage(content=message["text"])]
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
    llm = ChatOpenAI(api_key=SecretStr(os.environ["OPENAI_API_KEY"]), model=os.environ.get("AI_VERSION", "gpt-4.1-mini"))
