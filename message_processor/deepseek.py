import json
import logging
import os

from langchain_core.messages import HumanMessage
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_deepseek import ChatDeepSeek

from utils import validate_env

llm: ChatDeepSeek
min_confidence: float

logger = logging.getLogger(__name__)


def _parse_json_from_llm_response(raw: str) -> dict:
    """Parse JSON from model output; strips optional ``` / ```json fences."""
    text = raw.strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl != -1:
            text = text[first_nl + 1 :]
        else:
            text = text.strip("`")
        closing = text.rfind("```")
        if closing != -1:
            text = text[:closing]
        text = text.strip()
    return json.loads(text)


SYSTEM_PROMPT = (
    "You are an AI agent that evaluates how well a client's request description matches "
    "a specialist's service offering.\n\n"
    "You will receive input as a JSON object with the following fields:\n"
    '- "request": a string describing what the client needs.\n'
    '- "service": a string describing what the specialist provides.\n'
    '- "tags": an array of strings representing additional structured information about the service '
    "(e.g., skills, tools, categories).\n\n"
    "Based on the analysis, determine whether the service is suitable for fulfilling the request. "
    "Use both the service description and the tags to inform your judgment.\n\n"
    "Confidence score meaning:\n"
    "- 0.0 – 0.2: The service does not match the request at all; the specialist cannot perform the required work.\n"
    "- 0.3 – 0.4: Minimal overlap; the specialist has only a vague or incidental connection to the request.\n"
    "- 0.5 – 0.6: Partial match; the specialist covers some aspects but misses critical elements.\n"
    "- 0.7 – 0.8: Good match; the specialist covers most key requirements, with minor gaps.\n"
    "- 0.9 – 1.0: Excellent match; the specialist is perfectly aligned with the request, with no significant gaps.\n\n"
    "Return your response strictly as a JSON object with two fields:\n"
    '- "confidence": a number between 0 and 1 following the scale above.\n'
    '- "reasoning": a short string explaining your conclusion, highlighting key matches or mismatches '
    "in the description and tags.\n\n"
    "Do not include any text outside the JSON."
)


async def check_relevance(message_text: str, title: str, tags: list) -> dict | None:
    system_prompt = SystemMessagePromptTemplate.from_template(
        SYSTEM_PROMPT, template_format="mustache"
    ).format()

    payload = json.dumps({
        "request": message_text,
        "service": title,
        "tags": tags,
    }, ensure_ascii=False)

    messages = [system_prompt, HumanMessage(content=payload)]

    try:
        result = (await llm.ainvoke(messages)).content.strip()
    except Exception as e:
        logger.warning(f"DeepSeek relevance check failed: {e}")
        return None

    try:
        parsed = _parse_json_from_llm_response(result)
        confidence = float(parsed.get("confidence", 0))
        reasoning = parsed.get("reasoning", "")
        return {"confidence": confidence, "reasoning": reasoning}
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse DeepSeek response: {result}, error: {e}")
        return None


def is_relevant(result: dict | None) -> bool:
    if result is None:
        return True
    return result["confidence"] >= min_confidence


def init_deepseek():
    global llm, min_confidence

    validate_env("DEEPSEEK_API_KEY")

    llm = ChatDeepSeek(
        model="deepseek-chat",
        api_key=os.environ["DEEPSEEK_API_KEY"],
    )

    min_confidence = float(os.environ.get("MIN_CONFIDENCE", "0.5"))
    logger.info(f"DeepSeek initialized with MIN_CONFIDENCE={min_confidence}")
