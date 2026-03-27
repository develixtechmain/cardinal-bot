import styles from "./BriefingCompleted.module.css";
import {useEffect} from "react";

import {useLocation} from "wouter";

import WideButton from "../../../components/common/Buttons/WideButton";
import {useBriefingStore, useFinder} from "../../../store/finder";
import {openLink} from "../../../utils/common";

export default function BriefingCompleted() {
    const [, navigate] = useLocation();
    const reset = useBriefingStore((s) => s.reset);

    const tasks = useFinder((state) => state.tasks);

    useEffect(() => {
        reset();
    }, []);

    return (
        <div className={styles.container}>
            <div className={styles.backgroundLogo}>
                <img src="/assets/finder/briefing/completed-background.svg" alt=" " />
            </div>
            <div className={styles.content}>
                <img height="40px" width="150px" src={`/assets/finder/briefing/progress-completed.svg`} alt=" " />
                <img height="142px" width="142px" src="/assets/finder/briefing/logo-completed.svg" alt=" " />
                <div className={styles.textContainer}>
                    <span className={styles.title}>БРИФИНГ ЗАВЕРШЕН</span>
                    <span className={styles.subtitle}>
                        <span style={{fontWeight: 600}}>Cardinal AI</span>
                        <span> уже начал искать подходящие заявки под твой профиль. Ожидай первые лиды совсем скоро.</span>
                    </span>
                    <div className={styles.description}>
                        <span style={{fontSize: 15, fontWeight: 700}}>Важно:</span>
                        <span>
                            Не забывай оценивать и откликаться на заявки — ИИ будет самообучаться на твоих действиях и каждый день подбирать всё более точные и
                            релевантные заказы именно для тебя.
                        </span>
                    </div>
                </div>
                {tasks.length <= 1 ? (
                    <div className={styles.footer}>
                        <div className={styles.footerIcon}>
                            <img height="61px" width="61px" src="/assets/icons/tg.svg" alt=" " />
                        </div>
                        <span className={styles.footerMessage}>
                            Перейдите в бота и активируйте его как можно быстрее — туда будут приходить все ваши заявки.
                        </span>
                        <div className={styles.footerButtons}>
                            <WideButton
                                color="#7211F833"
                                textColor="#7211F8"
                                text="Активировать бота рассылщика"
                                onClick={() => openLink("https://t.me/cardinal_leadfinder_bot")}
                                buttonClassName={styles.button}
                                buttonStyle={{border: "1px solid #7211F8"}}
                            />
                            <WideButton
                                color="#7211F8"
                                textColor="#FFFFFF"
                                text="Перейти в ЛК"
                                onClick={() => navigate("/")}
                                buttonClassName={styles.button}
                                buttonStyle={{}}
                            />
                        </div>
                    </div>
                ) : (
                    <div className={styles.footerButtons} style={{width: "100%", marginTop: 114, marginBottom: 31}}>
                        <WideButton
                            color="#FFFFFF33"
                            textColor="#FFFFFF"
                            text="Перейти к лидам"
                            onClick={() => openLink("https://t.me/cardinal_leadfinder_bot")}
                            buttonClassName={styles.button}
                            buttonStyle={{border: "1px solid #FFFFFF"}}
                        />
                        <WideButton color="#FFFFFF" textColor="#000000" text="Перейти в ЛК" onClick={() => navigate("/")} buttonClassName={styles.button} />
                    </div>
                )}
            </div>
        </div>
    );
}
