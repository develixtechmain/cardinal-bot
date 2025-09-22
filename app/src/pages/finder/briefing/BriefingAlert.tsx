import styles from "./BriefingAlert.module.css";
import {useEffect, useState} from "react";

import {useLocation} from "wouter";

import {fetchBriefing} from "../../../api/briefing";
import BriefingFullExampleModal from "../../../components/finder/BriefingExampleModal/BriefingFullExampleModal";
import {useBriefingStore} from "../../../store/finder";
import {useStore} from "../../../store/store";
import {PartialText} from "../../../types";

import Mark from "../../../assets/icons/mark.svg";

const recommendations: PartialText[] = [
    {id: "fluent", textParts: [{text: "Пиши свободно,", bold: true}, {text: "как будто рассказываешь человеку."}]},
    {id: "think", textParts: [{text: "Разворачивай мысль,", bold: true}, {text: "а не просто кликай по подсказкам."}]},
    {id: "mistake", textParts: [{text: "Не бойся ошибиться —"}, {text: "ИИ всё поймёт и адаптирует.", bold: true}]},
    {id: "questions", textParts: [{text: "Чем больше ты расскажешь,"}, {text: "тем меньше лишних вопросов будет дальше.", bold: true}]}
];

export default function BriefingAlert() {
    const [, navigate] = useLocation();
    const user = useStore((s) => s.user);
    const briefingId = useBriefingStore((s) => s.id);
    const setBriefingId = useBriefingStore((s) => s.setId);
    const [isDisabled, setIsDisabled] = useState(true);
    const [isExamplesOpen, setIsExamplesOpen] = useState(false);

    useEffect(() => {
        const run = async () => {
            if (briefingId) {
                setIsDisabled(false);
                return;
            }

            const briefing = await fetchBriefing(user!.id);
            setBriefingId(briefing.id);
            if (briefing.questions.length > 0) {
                console.log("Restarting briefing"); // TODO
            }
            setIsDisabled(false);
        };

        void run();
    }, []);

    return (
        <div className={styles.container}>
            <BriefingFullExampleModal isOpen={isExamplesOpen} onClose={() => setIsExamplesOpen(false)} />
            <img height="75px" width="75px" src="/assets/finder/briefing/alert.svg" alt="ВНИМАНИЕ!" />

            <div className={styles.alertTitle}>
                <span>Прочти перед стартом брифинга — </span>
                <span className={styles.red}>это влияет на результат</span>
            </div>

            <div className={styles.tipContainer}>
                <span className={styles.tipTitle}>Почему это важно:</span>
                <span className={styles.tipDescription}>
                    Брифинг помогает ИИ понять, какие заявки тебе реально нужны. Чем точнее ты опишешь себя и свои услуги — тем более подходящие заказы будет
                    находить система.
                </span>
            </div>

            <div className={styles.recommendations}>
                <div className={styles.recommendationsHeader}>
                    <img height="26px" width="26px" src="/assets/finder/briefing/alert-tip-header.svg" alt=" " />
                    <span>Как отвечать</span>
                </div>
                <div className={styles.recommendationsList}>
                    {recommendations.map(({id, textParts}) => (
                        <div key={id} className={styles.recommendation}>
                            <Mark height="15px" width="15px" color="#F81B11" />
                            <div>
                                {textParts.map(({bold, text}, index) => (
                                    <span key={index}>
                                        <span style={bold ? undefined : {fontWeight: 400}}>{text}</span>
                                        {index < textParts.length - 1 && <span> </span>}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className={styles.about}>
                <img height="20px" width="20px" src="/assets/finder/briefing/cpu.svg" alt=" " />
                <div className={styles.aboutWork}>
                    <span className={styles.aboutTitle}>Как это работает:</span>
                    <div className={styles.aboutDescription}>
                        <span>После брифинга ИИ создаст облако тегов и смысловую модель, которая будет ежедневно фильтровать заказы из Telegram-чатов.</span>
                        <span className={styles.aboutDescriptionRed}> Это значит, что от твоих ответов напрямую зависит качество заявок.</span>
                    </div>
                </div>
            </div>

            <div className={styles.alertTip}>
                <div>Важно:</div>
                <span className={styles.alertTipDescription}>
                    Отвечай честно, подробно и спокойно. Ты не проходишь тест — ты помогаешь ИИ работать персонально под тебя.
                </span>
            </div>

            <div style={{flex: 1}} />
            <button className={styles.startButton} disabled={isDisabled} onClick={() => navigate("/finder/briefing/questions")}>
                Начать брифинг
            </button>

            <button
                className={styles.examplesButton}
                onClick={() => {
                    setIsExamplesOpen(true);
                }}
            >
                <img height="20px" width="20px" src="/assets/finder/briefing/examples.svg" alt=" " />
                Посмотреть примеры ответов
            </button>
        </div>
    );
}
