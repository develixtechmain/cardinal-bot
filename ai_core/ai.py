import json
import os
from typing import List

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from pydantic import SecretStr, BaseModel

import db
from utils import validate_env

llm: ChatOpenAI


class Questions(BaseModel):
    questions: List[str]


async def process_answer(user_id, onboarding, questions):
    await db.complete_onboarding(user_id, onboarding['id'])
    return []
    # return ['Какой-то вопрос', "Опишите типичный процесс создания сайта на Тильде от начала до конца."]
    questions_dict = {item["question"]: item["answer"] for item in json.loads(onboarding['questions'])}

    for item in questions:
        if item.answer:
            questions_dict[item.question] = item.answer
        else:
            questions_dict.pop(item.question, None)

    await db.save_questions(user_id, onboarding['id'], questions_dict)

    input_text = "\n".join([f"Q: {key}\nA: {value}" for key, value in questions_dict.items()])

    system_prompt = """
    You are an assistant for analyzing job applicant questionnaires. Your task is to determine whether the provided questionnaire contains enough meaningful information to build a "cloud of meanings".

    Input format: a list of questions and answers from the candidate's questionnaire.
    
    Processing steps:
    1. Analyze all answers for meaningful content: skills, tools, experience, interests, or qualities.
    2. **Only** if at least 50 specific and meaningful phrases can be extracted — consider the data sufficient.
    3. If not enough meaningful content exists — return up to 5 Russian-language follow-up questions aimed at clarifying key missing points.
    4. Avoid over-demanding generic info like "soft skills" unless clearly absent AND needed.
    5. Return result as a JSON array of strings (questions), or empty array if sufficient.
    
    Example output when info is insufficient:
    [
        "Какими технологиями вы владеете?",
        "Чем занимались на предыдущей работе?"
    ]
    
    Example output when info is sufficient:
    []
    
    Do not include explanations or additional text — return only the JSON array of questions in Russian.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    chain = prompt | llm | JsonOutputParser(pydantic_object=Questions)

    result = chain.invoke({"input": input_text})

    if not result:
        await db.complete_onboarding(onboarding['id'])

    return result


class MeaningCloud(BaseModel):
    tags: List[str]


async def get_cloud_of_meaning(questions):
    return ['test', 'test2']

    input_text = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in json.loads(questions)])

    system_prompt = """
    You are an assistant for analyzing job applicant questionnaires. Your task is to convert the candidate's questionnaire into a "cloud of meanings" — a JSON array of strings representing key skills, areas of activity, technologies, tools, achievements, professional interests, and personal traits.

    Input format: a list of questions and answers from the candidate's questionnaire.

    Processing steps:
    1. Read all questions and answers step by step.
    2. Extract unique by meaning key elements such as skills, experience, tools, interests, and qualities.
    3. Normalize extracted phrases to a consistent format (e.g., "software development" instead of "developing software").
    4. All keys must include a specialization context (e.g., "massage for dogs" instead of just "massage").
    5. Avoid duplicates and select the most relevant and meaningful phrases.
    6. Return the result as a JSON array of Russian-language strings, sorted by relevance (most important first).

    Example output format:
    [
        "software development",
        "web development",
        "bot development",
        "Python",
        "Java"
    ]

    Be precise, use professional language, and avoid explanations or extra text.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    chain = prompt | llm | JsonOutputParser(pydantic_object=MeaningCloud)

    return chain.invoke({"input": input_text})


async def init_llm():
    global llm
    validate_env("OPENAI_API_KEY")
    llm = ChatOpenAI(
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
        model="gpt-4.1-mini"
    )
