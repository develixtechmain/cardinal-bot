import React from "react";
import styles from "./BriefingCompleted.module.css";
import {useLocation} from "wouter";

export default function BriefingCompleted() {
    const [, navigate] = useLocation();

    return (<>
            <div className={styles.container}>
                <div className={styles.backgroundLogo}><img src="/assets/finder/briefing/completed-background.svg" alt=" "/></div>
                <img height="40px" width="150px" className={styles.progress} src={`/assets/finder/briefing/progress-completed.svg`} alt=" "/>
                <img height="142px" width="142px" className={styles.logo} src="/assets/finder/briefing/logo-completed.svg"
                     alt=" "/>
                <div className={styles.textContainer}>
                    <span className={styles.title}>БРИФИНГ ЗАВЕРШЕН</span>
                    <span className={styles.subtitle}>
                        <span className={styles.subtitleHeader}>Cardinal AI</span>
                        <span> уже начал искать подходящие заявки под твой профиль. Ожидай первые лиды совсем скоро.</span>
                    </span>
                    <div className={styles.description}>
                        <span className={styles.descriptionHeader}>Важно:</span>
                        <span>Не забывай оценивать и откликаться на заявки — ИИ будет самообучаться на твоих действиях и каждый день подбирать всё более точные и релевантные заказы именно для тебя.</span>
                    </div>
                </div>
                <div style={{flex: 1}}/>
                {/*TODO leads*/}
                <button className={styles.leadsButton} onClick={() => navigate("/finder")}>
                    Перейти к лидам
                </button>
                <button className={styles.clientButton} onClick={() => navigate("/")}>
                    Перейти в ЛК
                </button>
            </div>
        </>
    );
}
