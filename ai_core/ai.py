import json
import os
from datetime import datetime, timezone
from typing import List

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from pydantic import BaseModel, SecretStr

import db
from metrics import onboardings_completed_total, onboardings_time
from utils import validate_env

llm: ChatOpenAI

ai_mode: str


class Questions(BaseModel):
    questions: List[str]


async def process_answer(user_id, onboarding, questions):
    questions_dict = {question["question"]: question for question in json.loads(onboarding["questions"])}

    for question in questions:
        questions_dict[question.question] = {"question": question.question, "answer": question.answer, "selections": question.selections}

    questions_answers = list(questions_dict.values())

    onboarding = await db.save_questions(user_id, onboarding["id"], questions_answers)

    if onboarding["status"] == "completed":
        count_completed(onboarding)
        return []

    input_text = json.dumps(questions_answers, ensure_ascii=False)

    system_prompt = """
        You are an assistant for analyzing job applicant questionnaires. Your task is to determine whether the provided questionnaire contains enough meaningful information to build a "cloud of meanings" and, if not, to generate up to 3 focused follow-up questions in Russian.

        Input format: a JSON array of objects [{{"question":"string","answer":"string"|null,"selections":["string"]|null}}].
        - "answer" may be empty or null.
        - "selections" is an array of labels that were explicitly checked by the candidate; if absent or empty it means no options were selected.
        - Treat each non-empty "answer" and each string in "selections" as explicit assertions.

        Processing steps:
        1. Interpret explicit assertions:
           - Any non-empty "answer" is an explicit assertion; extract phrases from it.
           - Any string in "selections" is an explicit assertion; treat each selected label as equivalent to a short textual answer.
           - If a question has both "answer" and "selections", use both sources.

        2. Phrase extraction and normalization:
           - From explicit assertions extract distinct meaningful phrases: domains (areas of work or use cases), roles, core tasks/skills, tools/technologies, measurable experience, interests, or concrete achievements.
           - Prefer concise canonical phrases of 1–6 words; allow up to 8 words only for clearly necessary, non-redundant specialization.
           - Normalize and canonicalize: lowercase (except official tech tokens), normalize spacing and hyphens, convert verbal forms to nominal where appropriate ("разрабатывал интерфейсы" → "frontend разработка"), and unify obvious synonyms into a single canonical form (e.g., "разработка backend" ↔ "backend разработка" → "backend разработка").
           - Preserve official technology names exactly (Java, React, Docker, LangChain, etc.).

        3. Counting trustworthy phrases:
           - Count only distinct, trustworthy phrases extracted from explicit assertions (answer + selections).
           - Do not fabricate phrases; do not infer unstated specializations.

        4. Sufficiency decision:
           - If count >= 50 distinct trustworthy phrases → return an empty JSON array [] (sufficient).
           - If count < 50 → generate up to 3 follow-up questions in Russian to clarify missing information.

        5. Follow-up generation priorities and constraints (strong rules):
           - Priority A — Domains (highest priority): prefer questions that uncover concrete domains, product types, target audiences and use cases. Frame follow-ups to elicit domain context first.
           - Priority B — Domain-related skills/tasks: next ask which concrete tasks or aspects of the domain the candidate performed (e.g., "frontend vs backend vs analytics", "prototyping vs research"), not generic tool lists.
           - Priority C — Tools (rare): ask about tools only when tools are decisive for meaning extraction; prefer asking how a tool was used or what role the candidate played with it, not a raw tool list.
           - Priority D — Experience metrics (rare): ask about duration/role/scope only if necessary to assess the significance of a claimed competence.
           - Emphasize domains: every generated question should, where applicable, relate back to a domain or clarify domain context.
           - Minimize tool and experience questions: include them only when domain or task clarity depends on them.

        6. No duplicated or semantically overlapping questions (hard constraint):
           - If multiple potential follow-ups would overlap strongly in meaning, produce a single consolidated question that covers the missing points.
           - Ensure each question in the output adds a semantically distinct information request; avoid periphrastic paraphrases.
           - Do not emit two questions that cover the same domain/topic even if phrased differently.
           - When merging related clarifications, structure the single question to cover the related subtopics concisely (comma or colon separated).

        7. Question style, templates and succinctness:
           - When selections exist, referencing them is allowed but not mandatory; prefer concise direct questions when that reads better (e.g., instead of "Вы отметили 'Тильда' — расскажите..." you may simply ask "Расскажите подробнее о типах маркетинговых структур и wow-дизайне, которые вы используете.").
           - Use one of three concise templates (choose the best-fitting one for each follow-up):
             1) Domain: "В каких продуктах вы использовали X и что это дало проекту?"
             2) Skills/tasks: "Какие этапы вы выполняли при работе с Y?"
             3) Tools/usage: "Как вы использовали T в последних проектах?"
           - If referencing related selections, join multiple succinctly: "Вы отметили 'A' и 'B' — ...", but prefer dropping the prefix if a shorter direct question is clearer.
           - Limit each question length to roughly 120 characters where possible; keep questions direct and actionable.

        8. Additional constraints and behaviors:
           - Never repeat or strongly overlap existing explicit assertions; if an item is partially answered, reframe to probe adjacent or deeper detail rather than repeat.
           - Keep follow-ups within the same domain when a domain is present; avoid switching to unrelated domains.
           - Avoid generic soft-skill questions unless their absence blocks extraction of domain-relevant phrases.
           - When helpful, reference specific selections in questions (e.g., "Вы отметили 'X' — уточните, какие задачи вы решали с помощью X?").

        9. Output requirements:
           - Return only a JSON array of strings (follow-up questions) in Russian, up to 3 items, or an empty array [] if sufficient.
           - Do not include explanations, metadata, examples, or any additional text.

        Example output when info is insufficient: [ "Опишите, ваши навыки и опыт в архитектурном проектировании.", "Какие типы проектов или задач тебе наиболее интересны и ближе всего по профилю?" ]

        Example output when info is sufficient: []

        Do not include explanations or additional text — return only the JSON array of questions in Russian.
    """

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])

    chain = prompt | llm | JsonOutputParser(pydantic_object=Questions)
    result = chain.invoke({"input": input_text})

    if not result:
        await db.complete_onboarding(onboarding["user_id"], onboarding["id"])
        count_completed(onboarding)

    return result


def count_completed(onboarding):
    onboardings_completed_total.inc()
    now = datetime.now(timezone.utc)
    if onboarding["created_at"].tzinfo is None:
        created = onboarding["created_at"].replace(tzinfo=timezone.utc)
    else:
        created = onboarding["created_at"]
    onboardings_time.observe((now - created).total_seconds())


class MeaningCloud(BaseModel):
    tags: List[str]


async def get_cloud_of_meaning(questions):
    system_prompt = """
        You are an assistant for converting a candidate's questionnaire (questions + answers) into a "cloud of meanings" — a JSON array of concise tags for downstream 768-dim embedding and Russian-language similarity search.
        
        Input format: a JSON array of objects [{{"question":"string","answer":"string"|null,"selections":["string"]|null}}].
        - "answer" may be empty or null.
        - "selections" is an array of labels that were explicitly checked by the candidate; if absent or empty it means no options were selected.
        - Treat each non-empty "answer" and each string in "selections" as explicit assertions.
        
        Task: extract concise, high-quality tags that map well to how vacancies/tasks are phrased.
        
        Rules:
        1) Output structure and order:
           - Return a JSON array of strings.
           - Order: first Role (single tag) if explicitly present, then Core skills/tasks, then Tools/technologies.
           - Do not include duplicates or near-duplicates.
        
        2) Tag form and length:
           - Tag = 1–4 words preferred; allow up to 8 words only for absolutely necessary specialization.
           - Use canonical Russian phrasing for roles/skills (e.g., "Java разработчик", "backend разработка", "разработка платежных систем").
           - Preserve official technology names as tokens (Java, React, Docker).
        
        3) Normalization and canonicalization:
           - Lowercase except technology tokens; normalize spacing and hyphens; remove punctuation except parentheses for metrics.
           - Merge synonyms into a single canonical tag (e.g., "backend разработка", "разработка backend" → "backend разработка").
           - For multi-concept fragments, split only when explicitly supported (e.g., "интерфейсы и интеграция платежей" → "frontend разработка", "интеграция платежных систем").
        
        4) Usefulness filter:
           - Exclude generic, low-value phrases that don't help vacancy matching (examples to drop: "подсчёт максимальных объёмов данных" unless presented as core).
           - Keep phrases that directly answer "who is needed" or "what should someone be able to do" (Role, Core skill/task, Tool).
        
        5) Numeric metrics:
           - Include years/metrics only if explicitly stated; format as "(N лет)" appended to the relevant tag (e.g., "backend (3 года)").
        
        6) Fidelity and no invention:
           - Do not fabricate. Include only items explicitly supported by the text or trivially canonicalized synonyms.
           - If uncertain, omit the tag.
        
        7) Deduplication rules:
           - If both specific and general tags exist, keep both only when they add distinct matching value (e.g., keep "Java" and "Java разработчик" only if both are explicitly supported; prefer role if choice).
           - Normalize variants: prefer "backend разработка" over "разработка backend" and remove redundant tokens like "разработка" duplicates.
        
        8) Embedding guidance (internal):
           - Use the produced string (canonical_ru) as the primary embedding text for RU search.
        
        Examples of desired outputs:
        - Good: "Java разработчик", "backend разработка", "разработка платежных систем", "разработка сайтов на React", "создание дизайна в Figma"
        - Bad (drop or canonicalize): "расчёт максимальных объёмов данных" (drop unless core), "разработка java сервисов" → canonical "разработка на Java" or "Java разработчик"
        
        Return only the JSON array of canonical tags, nothing else.
        
        Example:
        [
          "Java разработчик",
          "разработка backend (3 года)",
          "разработка платежных систем",
          "разработка сайтов на React",
          "создание дизайна в Figma"
        ]
    """

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])

    chain = prompt | llm | JsonOutputParser(pydantic_object=MeaningCloud)

    return chain.invoke({"input": questions})


async def get_task_title(tags):
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

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])

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
           b. If the condition contains a numeric threshold (e.g., "< 1000", "≥ 2025-01-01"), parse and normalize numbers or ISO dates from application_description.  
           c. Else evaluate by free-text semantic matching of the condition against application_description.  
           d. Mark status = "violated" if the condition is met; = "not_violated" if clearly not met; = "unknown" if critical facts are missing.  
        3. Determine decision:  
           - If any status == "violated" → decision = "does not fit".  
           - Else if no statuses == "violated" and no statuses == "unknown" → decision = "fits".  
           - Else → decision = "insufficient data".  
        4. Collect evidence quotes for each "violated" or "not_violated" determination.  
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

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])

    chain = prompt | llm | JsonOutputParser(pydantic_object=CheckResult)

    result = chain.invoke({"input": input_text})

    return result["decision"] == "fits"


async def extract_rules(text: str, user_text: str):
    input_text = f"""
        mode: {ai_mode}
        client_description: {{client_description}}
        application_description: {text}
        user_feedback: {user_text}
        """

    system_prompt = """
        [TOP INSTRUCTION — DO NOT IGNORE]  
        You are a strict, deterministic "rule extractor." Your task is to derive concise, testable FORBIDDEN RULES from two free-text inputs: **application_description** and **user_feedback**. Think step-by-step using a chain of drafts but do not reveal intermediate drafts unless debug mode is enabled. Output valid UTF-8 JSON ONLY.
        
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
        - If the user_feedback contains a personal preference or personal limitation ("I don’t do X", "I’m not interested in Y", "I’m not skilled at Z", "this is not my field", etc.), you MUST reinterpret it as a property of the application. Convert these personal statements into an application-related condition, such as: "application involves X", "application requires skill Y", "application belongs to category Z", "application's main function is <domain>"
        - Reinterpreted application-related conditions MUST be limited strictly to the domain explicitly mentioned in user_feedback (e.g., "I don’t do video editing" → "application involves video editing"). Do NOT create inverse, broad, or category-negating rules.
        - Only produce a rule if the reinterpreted application property could realistically appear or be detected in application_description; otherwise treat it as insufficient data.
        - The condition MUST describe only properties of the application. Never include the user, preferences, or personal circumstances.
        - All output rules MUST be evaluable solely from application_description.
        - In debug mode, include a draft_chain array showing each draft step’s result.
        
        [BOTTOM INSTRUCTION — REPEAT]  
        Return ONLY the JSON object specified above. Do NOT include explanations outside of debug_chain when mode="debug".
    """

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])

    chain = prompt | llm | JsonOutputParser(pydantic_object=Questions)

    result = chain.invoke({"input": input_text})

    return result


async def init_llm():
    global llm, ai_mode
    validate_env("OPENAI_API_KEY")
    llm = ChatOpenAI(api_key=SecretStr(os.environ["OPENAI_API_KEY"]), model=os.environ.get("AI_VERSION", "gpt-4.1-mini"))

    validate_env("AI_MODE")
    ai_mode = os.environ["AI_MODE"]
    if ai_mode not in ("prod", "debug"):
        raise ValueError(f"AI_MODE может быть только prod или debug!")
