import styles from "./BriefingAdditional.module.css";
import {ChangeEvent, useEffect, useRef, useState} from "react";

import {useLocation} from "wouter";

import {useBriefingStore} from "../../../store/finder";

export default function BriefingAdditional() {
    const [, navigate] = useLocation();
    const answerAreaRef = useRef<HTMLTextAreaElement>(null);
    const briefingId = useBriefingStore((s) => s.id);

    if (!briefingId) {
        navigate("/finder/briefing/alert");
    }

    const additionalQuestions = useBriefingStore((s) => s.additionalQuestions);
    const setAdditionalQuestions = useBriefingStore((s) => s.setAdditionalQuestions);

    const [answerText, setAnswerText] = useState("");
    const [answerError, setAnswerError] = useState("");

    let questions = additionalQuestions ?? [];
    let questionIndex = questions.findIndex((q) => q.answer.trim() === "");
    let question = questions[questionIndex];

    useEffect(() => {
        if (questionIndex === -1) {
            navigate("/finder/briefing/verify");
        }
    }, [questionIndex]);

    useEffect(() => {
        questions = additionalQuestions ?? [];
        questionIndex = questions.findIndex((q) => q.answer.trim() === "");
        question = questions[questionIndex];
        setAnswerText(question?.answer || "");
        setAnswerError("");
    }, [additionalQuestions]);

    useEffect(() => {
        if (!answerAreaRef.current) return;

        const area = answerAreaRef.current;
        area.style.height = "auto";
        area.style.minHeight = "auto";

        requestAnimationFrame(() => {
            const min = answerError ? 64 : 66;
            const height = Math.max(min, Math.min(area.scrollHeight, 230)) + "px";
            area.style.height = height;
            area.style.minHeight = height;
        });
    }, [answerText]);

    const handleAnswerChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
        const answer = event.target.value;
        if (answer.trim() === "") {
            setAnswerError("Введите ответ на вопрос");
        } else {
            setAnswerError("");
        }
        setAnswerText(answer);
    };

    const handleQuestionChange = () => {
        if (answerError.length !== 0 || answerText === "") {
            setAnswerError("Введите ответ на вопрос");
            return;
        }

        let currentQuestions = [...questions];
        currentQuestions[questionIndex] = {question: question.question, answer: answerText};
        setAdditionalQuestions(currentQuestions);
    };

    return (
        <div className={styles.container}>
            <div className={styles.headerContainer}>
                <div className={styles.headerBlock}>
                    <img height="12px" width="12px" src="/assets/finder/briefing/additional-mark.svg" alt=" " />
                    <span>Дополнительный вопрос от ИИ</span>
                </div>
                <span className={styles.headerText}>ИИ задал этот вопрос, чтобы точнее подобрать для тебя заказы</span>
                <div style={{flex: 1}} />
            </div>
            <div className={styles.question}>{question?.question || ""}</div>

            <textarea
                ref={answerAreaRef}
                id="answer_text"
                value={answerText}
                onChange={handleAnswerChange}
                autoComplete={"off"}
                placeholder={answerError || "Расскажите своими словами"}
                className={`${styles.answerInput} ${answerError ? styles.inputError : ""}`}
            />

            <div className={styles.tip}>Пишите, как говорите — это помогает нам точнее понимать и подбирать ответы.</div>

            <div style={{flex: 1}}></div>

            <div className={styles.additionalButtons}>
                <button className={`${styles.nextButton} ${styles.buttonText}`} onClick={handleQuestionChange}>
                    Далее
                </button>
            </div>
        </div>
    );
}
