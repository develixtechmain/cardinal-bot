import React, {useEffect, useRef, useState} from "react";
import {useBriefingStore, useFinder} from "../../../store/finder";
import {useLocation} from "wouter";

import styles from './BriefingVerify.module.css'
import {totalAnswers} from "../../../store/questions";
import {answerQuestions, completeBriefing, createTask} from "../../../api/briefing";

export default function BriefingVerify() {
    const hasRun = useRef(false);
    const [navigateTo, setNavigateTo] = useState("");

    const [, navigate] = useLocation();
    const briefingId = useBriefingStore(s => s.id);
    const additionalQuestions = useBriefingStore(s => s.additionalQuestions);
    const setAdditionalQuestions = useBriefingStore(s => s.setAdditionalQuestions);
    const answers = useBriefingStore(s => s.answers);

    const tasks = useFinder(s => s.tasks)
    const setTasks = useFinder(s => s.setTasks)

    useEffect(() => {
        const run = async () => {
            if (hasRun.current) return;
            hasRun.current = true;

            const additional = additionalQuestions ?? [];
            const total = totalAnswers(answers ?? [], additional);

            const newQuestions = await answerQuestions(briefingId!, total);

            if (newQuestions.length == 0) {
                const cloudTask = await completeBriefing(briefingId!, total)
                const task = await createTask(cloudTask)
                setTasks([...tasks, task])
                setNavigateTo("/finder/briefing/completed")
            } else {
                const totalAdditionalQuestions = [...additional];
                newQuestions.forEach(q => totalAdditionalQuestions.push({question: q, answer: ""}))
                setAdditionalQuestions(totalAdditionalQuestions)
                setNavigateTo("/finder/briefing/questions/additional")
            }
        }

        void run();
    }, []);

    useEffect(() => {
        if (navigateTo !== "") navigate(navigateTo)
    }, [navigateTo]);

    return (
        <div className={styles.container}>
            <svg className={styles.loadingContainer} viewBox="0 0 131 131">
                <image height="121" width="121" x={5} y={5} href="/assets/finder/briefing/loading-eagle.svg"/>
                <circle cx="65.5" cy="65.5" r="63" fill="none" stroke="#7211F8" strokeWidth="5"
                        strokeDasharray={299}
                        className={styles.loadingStroke}>
                    <animateTransform
                        attributeName="transform"
                        type="rotate"
                        from="0 65.5 65.5"
                        to="360 65.5 65.5"
                        dur="3s"
                        repeatCount="indefinite"
                    />
                </circle>
            </svg>
            <div className={styles.infoBlock}>
                <span className={styles.title}>Анализируем ваши ответы…</span>
                <span className={styles.subtitle}>Это займёт меньше минуты.</span>
                <div className={styles.description}>
                    ИИ внимательно изучает ваши ответы, чтобы подобрать нужные теги. Если информации окажется
                    недостаточно — ИИ задаст дополнительные вопросы
                </div>
            </div>
            <div className={styles.gradientBottom}/>
        </div>
    );
}