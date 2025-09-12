import json
import os
from typing import List

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from pydantic import SecretStr, BaseModel

import db
from utils import validate_env

llm: ChatOpenAI

ai_mode: str


class Questions(BaseModel):
    questions: List[str]


async def process_answer(user_id, onboarding, questions):
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
    return chain.invoke({"input": input_text})


class MeaningCloud(BaseModel):
    tags: List[str]


async def get_cloud_of_meaning(questions):
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


def get_task_title(tags):
    input_text = f"{tags}"

    system_prompt = """
    You are an expert in job title classification.  
    You will be given a list of tags describing skills, technologies, and work domains.  
    Your task is to determine the most accurate and common job title based on these tags.
    
    Rules:
    - Output only one short job title in plain text, no quotes, no explanations.
    - Use common industry-standard naming.
    - If most of the tags are in English, output in English.
    - If most of the tags are in Russian, output in Russian.
    - Do not add extra words like "Position", "Role", or "Job".
    - Maximum length: 255 characters.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({"input": input_text})


class CheckResult(BaseModel):
    decision: str


async def check_rules(text: str, rules: list[str]):
    input_text = f"""
        mode: {ai_mode}
        forbidden_rules_list: {rules}
        application_description: {text}
        """

    system_prompt = """
    [TOP INSTRUCTION — DO NOT IGNORE]  
    You are a strict, deterministic application filter. Your only job is to decide if an application fits, using a forbidden_rules_list and the application_description. Think step-by-step using a chain of drafts but do not reveal your intermediate reasoning unless debug mode is enabled. Output valid UTF-8 JSON ONLY.
    
    ## INPUT  
    mode: {{mode}}  
    forbidden_rules_list: {{forbidden_rules_list}}   # JSON array of rules, each formatted as "IF <condition> THEN DO NOT RECOMMEND"
    application_description: {{application_description}}   # free-form text  
    
    ## GOAL  
    Produce a single JSON object with these fields:  
    - decision: "fits" | "does not fit" | "insufficient data"  
    - violated_rules: array of rule strings that were violated (empty if none)  
    - evidence: array of verbatim quotes from application_description that justify the decision  
    - missing_info: array of critical facts that are absent (empty if none)  
    - notes: brief 1–2 sentence summary, no step-by-step logic  
    In debug mode, also include debug_chain.
    
    ## DRAFT PHASE (HIDDEN, unless mode=="debug")  
    1. Retrieve rules from forbidden_rules_list.  
    2. For each rule string:  
       a. Extract the condition text between "IF " and " THEN DO NOT RECOMMEND".  
       b. If the condition contains a numeric threshold (e.g., “< 1000”, “≥ 2025-01-01”), parse and normalize numbers or ISO dates from application_description.  
       c. Else evaluate by free-text semantic matching of the condition against application_description.  
       d. Mark status = "violated" if the condition is met; = "not_violated" if clearly not met; = "unknown" if critical facts are missing.  
    3. Determine decision:  
       - If any status == "violated" → decision = "does not fit".  
       - Else if no statuses == "violated" and no statuses == "unknown" → decision = "fits".  
       - Else → decision = "insufficient data".  
    4. Collect evidence quotes for each “violated” or “not_violated” determination.  
    5. List any critical facts missing under missing_info.  
    6. Assemble the final JSON object.
    
    ## OUTPUT FORMAT (JSON ONLY)  
    Return exactly one JSON object:
    {{
      "decision": "<fits|does not fit|insufficient data>",
      "violated_rules": ["IF ... THEN DO NOT RECOMMEND", …],
      "evidence": ["verbatim quote1", …],
      "missing_info": ["which fact is missing", …],
      "notes": "<brief summary>",
      {{#if mode=="debug"}}
      ,"debug_chain": [
         {{
           "rule": "IF ... THEN DO NOT RECOMMEND",
           "status": "violated|not_violated|unknown",
           "fact": "<short reason or extracted value>"
         }},
         …
      ]
      {{/if}}
    }}
    
    ## STRICTNESS RULES  
    - Never output anything except the JSON object.  
    - Treat any ambiguity or missing critical info as "insufficient data."  
    - When a rule’s condition includes a numeric threshold or ISO date, you must parse and compare values exactly (=, <, ≤, ≥, >).  
    - Normalize numeric and date mentions in application_description before evaluation.  
    - If the condition contains no explicit numbers or dates, evaluate by plain-text semantic matching.  
    - Evidence must be direct, verbatim fragments from application_description.  
    - Each referenced rule must be exactly one from forbidden_rules_list.  
    - Do not invent facts; base all checks solely on application_description.
    
    [BOTTOM INSTRUCTION — REPEAT]  
    Return ONLY the JSON object specified above. Do NOT include explanations outside of debug_chain when mode="debug".  
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    chain = prompt | llm | JsonOutputParser(pydantic_object=CheckResult)

    result = chain.invoke({"input": input_text})

    return result['decision'] == 'fits'


async def extract_rules(text: str, user_text: str):
    input_text = f"""
        mode: {ai_mode}
        client_description: {{client_description}}
        application_description: {text}
        user_feedback: {user_text}
        """

    system_prompt = """
    [TOP INSTRUCTION — DO NOT IGNORE]  
    You are a strict, deterministic “rule extractor.” Your task is to derive concise, testable FORBIDDEN RULES from two free-text inputs: **application_description** and **user_feedback**. Think step-by-step using a chain of drafts but do not reveal intermediate drafts unless debug mode is enabled. Output valid UTF-8 JSON ONLY.
    
    ## INPUT  
    mode: {{mode}}   # "prod" or "debug"  
    application_description: {{application_description}}   # free-form text  
    user_feedback: {{user_feedback}}   # free-form text containing the client’s explanation  
    
    ## GOAL  
    Produce one or more short, atomic rules—each corresponding to a distinct complaint in **user_feedback**—that prevent recommending similar applications in the future.  
    - Extract each complaint phrase directly from **user_feedback**.  
    - Normalize it into an English semantic condition (e.g., "missing specified tasks", "insufficient job reward", "job reward is not specified explicitly").  
    - Format each as `"IF <condition> THEN DO NOT RECOMMEND"`.
    
    If you cannot identify any clear, testable complaint, output:  
    ```json
    ["insufficient data"]
    
    ## DRAFT PHASE (HIDDEN, unless mode=debug)  
    1. Parse **user_feedback** to list distinct complaints.  
    2. For each complaint, create a normalized English condition.  
    3. Wrap each condition into the rule template.  
    4. Ensure each rule is short, atomic, and directly testable.  
    5. Output all valid rules or `["insufficient data"]`.
    
    ## OUTPUT FORMAT  
    Output must be a JSON array of strings.
    
    Examples:
    
    First scenario (abstract tasks + low reward):  
    ```json
    [
      "IF missing specified tasks THEN DO NOT RECOMMEND",
      "IF insufficient job reward THEN DO NOT RECOMMEND"
    ]

    ## STRICTNESS RULES
    - Never output anything except the JSON array.
    - Each rule must reflect one distinct complaint and be formatted exactly as "IF <condition> THEN DO NOT RECOMMEND".
    - Do not invent complaints or thresholds; use only what appears in user_feedback.
    - Do not create rules that check for the presence, absence, or sentiment of user_feedback itself.
    - All rules must be based on conditions that can be evaluated from application_description or other available structured/unstructured fields at recommendation time.
    - Do not infer or guess a complaint if user_feedback does not explicitly describe one, but treat general quality-related feedback (e.g., "short description", "low quality text") as valid if it can be mapped to a measurable condition.
    - If user_feedback is too short, generic, or unrelated to job details (e.g., "foo", "ok", "no"), return ["insufficient data"].
    - In debug mode, include a draft_chain array showing each draft step’s result.
    
    [BOTTOM INSTRUCTION — REPEAT]  
    Return ONLY the JSON object specified above. Do NOT include explanations outside of debug_chain when mode="debug".
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    chain = prompt | llm | JsonOutputParser(pydantic_object=Questions)

    result = chain.invoke({"input": input_text})

    return result


async def init_llm():
    global llm, ai_mode
    validate_env("OPENAI_API_KEY")
    llm = ChatOpenAI(
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
        model="gpt-4.1-mini"
    )

    validate_env("AI_MODE")
    ai_mode = os.environ["AI_MODE"]
    if ai_mode not in ("prod", "debug"):
        raise ValueError(f"AI_MODE может быть только prod или debug!")
