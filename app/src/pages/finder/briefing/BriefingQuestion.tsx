import styles from "./BriefingQuestion.module.css";
import {CSSProperties, ChangeEvent, useEffect, useRef, useState} from "react";

import {useLocation} from "wouter";

import Header from "../../../components/common/Header/Header";
import {Loading} from "../../../components/common/Loading/Loading";
import BriefingExampleModal from "../../../components/finder/BriefingExampleModal/BriefingExampleModal";
import {useBriefingStore} from "../../../store/finder";
import {baseQuestions} from "../../../store/questions";

export default function BriefingQuestion() {
    const [, navigate] = useLocation();
    const [navigateTo, setNavigateTo] = useState("");
    const briefingId = useBriefingStore((s) => s.id);

    if (!briefingId) {
        navigate("/finder/briefing/alert");
    }

    const areaRef = useRef<HTMLTextAreaElement>(null);
    const answers = useBriefingStore((s) => s.answers);
    const setAnswers = useBriefingStore((s) => s.setAnswers);
    const [questionIndex, setQuestionIndex] = useState<number>(0);
    const [answerText, setAnswerText] = useState<string>("");
    const [selectionSearchText, setSelectionSearchText] = useState<string>("");
    const [answerError, setAnswerError] = useState<string>("");
    const [answerSelections, setAnswerSelections] = useState<Set<string>>(new Set());

    const searchInputRef = useRef<HTMLInputElement>(null);
    const lastSelectedButtonRef = useRef<HTMLButtonElement>(null);
    const [searchIsAlone, setSearchIsAlone] = useState(false);

    const [isExampleOpen, setIsExampleOpen] = useState(false);

    useEffect(() => {
        const check = () => {
            const last = lastSelectedButtonRef.current;
            const input = searchInputRef.current;

            if (!last) {
                if (!searchIsAlone) setSearchIsAlone(true);
                return;
            }

            if (!input) return;

            const lastTop = last.getBoundingClientRect().top;
            const inputTop = input.getBoundingClientRect().top;

            setSearchIsAlone(lastTop !== inputTop);
        };

        check();
        window.addEventListener("resize", check);
        return () => window.removeEventListener("resize", check);
    }, [answerSelections]);

    useEffect(() => {
        if (navigateTo !== "") navigate(navigateTo);
    }, [navigateTo]);

    useEffect(() => {
        if (!answers || answers.length !== baseQuestions.length) {
            setAnswers(baseQuestions.map(() => ({text: "", selections: new Set()})));
        }
    }, [answers, setAnswers]);

    useEffect(() => {
        if (answers && answers[questionIndex]) {
            setAnswerText(answers[questionIndex].text);
            setAnswerSelections(new Set(answers[questionIndex].selections));
        }
    }, [answers, questionIndex]);

    useEffect(() => {
        if (!areaRef.current) return;

        const area = areaRef.current;
        area.style.height = "auto";
        area.style.minHeight = "auto";

        requestAnimationFrame(() => {
            area.style.minHeight = Math.max(66, Math.min(area.scrollHeight, 230)) + "px";
        });
    }, [answerText, questionIndex]);

    const question = baseQuestions[questionIndex];

    if (!question) {
        return <Loading />;
    }

    const buttonNames = answers && answers[0] ? question.examples(questionIndex === 0 ? [] : [...answers[0].selections]) : [];
    const foundButtonNames = buttonNames.filter((buttonName) => buttonName.toLowerCase().includes(selectionSearchText.toLowerCase()));

    const handleAnswerChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
        handleChange(event.target.value);
    };

    const handleChange = (answer: string) => {
        if (answer.trim() === "") {
            setAnswerError("Введите ответ на вопрос");
        } else {
            setAnswerError("");
        }
        setAnswerText(answer);
    };

    const handleAddSelection = () => {
        handleSelection(selectionSearchText);
        setSelectionSearchText("");
    };

    const handleHint = () => {
        handleChange(question.hint.example!);
        setSelectionSearchText("");
        setIsExampleOpen(false);
    };

    const handleSelection = (buttonName: string) => {
        setAnswerSelections((prevSelections) => {
            const newSelections = new Set(prevSelections);
            if (newSelections.has(buttonName)) {
                newSelections.delete(buttonName);
            } else {
                newSelections.add(buttonName);
            }
            return newSelections;
        });
    };

    const handleQuestionChange = (next: boolean) => {
        if (next && (answerError.length !== 0 || (answerText === "" && !question.selection))) {
            setAnswerError("Введите ответ на вопрос");
            return;
        }

        let nextIndex = next ? questionIndex + 1 : questionIndex - 1;
        if (nextIndex < 0 || nextIndex > baseQuestions.length) {
            console.log("Unhandled index state, nextIndex", nextIndex);
            return;
        }

        const nextQuestion = baseQuestions[nextIndex];
        if (nextQuestion?.selection && [...answers![0].selections].length === 0) {
            nextIndex = next ? nextIndex + 1 : nextIndex - 1;
        }

        if (nextIndex >= baseQuestions.length) setNavigateTo("/finder/briefing/questions/additional");

        let currentAnswers = [...answers!];
        currentAnswers[questionIndex] = {text: answerText, selections: new Set(answerSelections)};
        setQuestionIndex(nextIndex);
        setAnswers(currentAnswers);
        setSelectionSearchText("");
        setAnswerError("");
    };

    return (
        <div className={styles.container}>
            <BriefingExampleModal isOpen={isExampleOpen} question={question} onClose={() => setIsExampleOpen(false)} useHint={handleHint} />
            <Header
                height={30}
                bottom={25}
                backTo={questionIndex > 0 ? undefined : ""}
                icon={<img height="30px" width="150px" style={{alignSelf: "center"}} src={`/assets/finder/briefing/progress-${questionIndex}.svg`} alt=" " />}
            />

            <span className={styles.question}>{question.question}</span>
            <span className={styles.description}>{question.description}</span>

            {!question.selection && (
                <>
                    <textarea
                        ref={areaRef}
                        id="answer_text"
                        value={answerText}
                        onChange={handleAnswerChange}
                        autoComplete={"off"}
                        placeholder={answerError || "Расскажите своими словами"}
                        className={`${styles.answerInput} ${answerError ? styles.inputError : ""}`}
                    />

                    <div className={styles.tip}>Пишите, как говорите — это помогает нам точнее понимать и подбирать ответы.</div>
                </>
            )}

            {buttonNames.length > 0 && (
                <>
                    {!question.selection && <div className={styles.tagsTitle}>Выберите подходящие теги</div>}

                    <div className={styles.selectionBlock}>
                        {Array.from(answerSelections).map((selection, i) => {
                            const isLast = i === answerSelections.size - 1;
                            return (
                                <button
                                    key={selection}
                                    ref={isLast ? lastSelectedButtonRef : undefined}
                                    onClick={() => setAnswerSelections(new Set([...answerSelections].filter((buttonName) => buttonName !== selection)))}
                                    className={styles.selectedButton}
                                    style={{"--background-color": "#7211F833"} as CSSProperties}
                                >
                                    <span>{selection}</span>
                                    <img height="15px" width="15px" src="/assets/finder/briefing/selection-cancel.svg" alt=" " />
                                </button>
                            );
                        })}
                        <input
                            type="text"
                            id="selection_text"
                            ref={searchInputRef}
                            value={selectionSearchText}
                            onChange={(event) => setSelectionSearchText(event.target.value.trim())}
                            autoComplete={"off"}
                            placeholder={"Поиск"}
                            className={styles.selectionSearchInput}
                            style={searchIsAlone ? {marginLeft: 8} : undefined}
                        />
                    </div>

                    {foundButtonNames.length > 0 ? (
                        <>
                            <div className={styles.selectionTip}>Выберите нужное из предложенных или начните вводить свой вариант.</div>
                            <div className={styles.selectionButtons}>
                                {foundButtonNames.map((buttonName: string, i) => (
                                    <button
                                        key={i + buttonName}
                                        onClick={() => handleSelection(buttonName)}
                                        className={`${answerSelections.has(buttonName) ? styles.selectedButton : styles.selectionButton} ${styles.extraSelectionButton}`}
                                    >
                                        {buttonName}
                                    </button>
                                ))}
                            </div>
                        </>
                    ) : (
                        <>
                            <div className={styles.notFoundTextContainer}>
                                <span>Мы не нашли похожих тегов - и это абсолютно нормально. </span>
                                <span className={styles.notFoundDescription}>
                                    Если этот ответ действительно отражает ваш профиль, просто добавьте его ниже.
                                </span>
                            </div>
                            <button className={styles.addSelectionButton} onClick={handleAddSelection}>
                                + Добавить как свой ответ
                            </button>
                        </>
                    )}
                </>
            )}

            <div style={{flex: 1}} />
            <div className={styles.additionalButtons}>
                {questionIndex > 0 && (
                    <button className={`${styles.backButton} ${styles.buttonText}`} onClick={() => handleQuestionChange(false)}>
                        Назад
                    </button>
                )}
                <button className={`${styles.nextButton} ${styles.buttonText}`} onClick={() => handleQuestionChange(true)}>
                    Далее
                </button>
            </div>

            <div style={{marginBottom: 25, width: "100%"}}>
                <button className={`${styles.exampleButton} ${styles.buttonText}`} style={{width: "100%"}} onClick={() => setIsExampleOpen(true)}>
                    <img height="20px" width="20px" src="/assets/finder/briefing/example.svg" alt=" " />
                    Пример качественного ответа
                </button>
            </div>
        </div>
    );
}
