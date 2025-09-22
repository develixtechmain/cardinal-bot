import styles from "./BriefingIntro.module.css";
import {useEffect, useState} from "react";

import {useLocation} from "wouter";

import {fetchBriefing} from "../../../api/briefing";
import Header from "../../../components/common/Header/Header";
import {useBriefingStore} from "../../../store/finder";
import {useStore} from "../../../store/store";
import {PartialText} from "../../../types";
import {DOCS_URL, SUPPORT_URL} from "../../../utils/consts";

const afterTexts: PartialText[] = [
    {id: "trial", textParts: [{text: "Активируется пробный доступ на 3 дня —"}, {text: "ты сразу начнёшь получать заявки", bold: true}]},
    {
        id: "cloud_of_meaning",
        textParts: [{text: "ИИ создаст персональное облако тегов —"}, {text: "по нему будет идти подбор самых релевантных заявок", bold: true}]
    },
    {id: "access", textParts: [{text: "Откроется доступ ко всем"}, {text: "ключевым функциям системы", bold: true}]}
];

const additionalButtons = [
    {text: "📚 База знаний", url: DOCS_URL},
    {text: "💬 Поддержка", url: SUPPORT_URL}
];

export default function BriefingIntro() {
    const [, navigate] = useLocation();
    const user = useStore((s) => s.user);
    const setBriefingId = useBriefingStore((s) => s.setId);
    const [isDisabled, setIsDisabled] = useState(true);

    useEffect(() => {
        const run = async () => {
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
            <Header />
            <div className={styles.introBackground}>
                <img src="/assets/finder/briefing/intro-background.svg" alt=" " />
            </div>
            <div className={styles.userContainer}>
                <img height="120px" width="120px" src={user!.avatar_url} alt="Аватар" />
                <span className={styles.hello}>ПРИВЕТ</span>
                <span className={styles.username}>@{user?.username}</span>
            </div>
            <div className={styles.introTitle}>
                <div className={styles.row}>
                    <img height="19px" width="17px" className={styles.smallStep} src="/assets/finder/briefing/clock.svg" alt=" " />
                    <span>2 минуты — и</span>
                </div>
                <div className={styles.row}>
                    <img height="19px" width="19px" className={styles.smallStep} src="/assets/finder/briefing/eagle.svg" alt=" " />
                    <span>Cardinal</span>
                    <div className={styles.midStep}>
                        <span className={styles.colored}>*</span>
                    </div>
                    <span>начнёт</span>
                    <img height="19px" width="24px" className={styles.largeStep} src="/assets/finder/briefing/spy.svg" alt=" " />
                    <span>искать</span>
                </div>
                <div className={styles.row}>
                    <span>заявки под тебя</span>
                </div>
            </div>

            <div className={styles.introDescription}>
                <span style={{opacity: 0.62}}>Для того чтобы запустить систему, нужно пройти короткий брифинг — </span>
                <span>ИИ подстроит систему под твои цели и начнёт находить подходящие заявки</span>
            </div>

            <div className={styles.afterContainer}>
                <div className={styles.afterTitle}>
                    <span>После брифинга </span>
                    <span className={styles.colored}>{">"}</span>
                </div>

                {afterTexts.map(({id, textParts}) => (
                    <div key={id} className={styles.afterRow}>
                        <img height="4px" width="4px" src="/assets/finder/briefing/dot.svg" alt=" " />
                        <div>
                            {textParts.map(({bold, text}, index) => (
                                <span key={index} className={styles.afterText}>
                                    <span style={bold ? {fontWeight: 700} : undefined}>{text}</span>
                                    {index < textParts.length - 1 && <span> </span>}
                                </span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className={styles.remark}>
                <span className={styles.remarkStar}>*</span>
                <span className={styles.remarkText}>
                    Cardinal — это умный софт на базе ИИ, который сам подбирает самые релевантные заявки под твой профиль.
                </span>
            </div>

            <div style={{flex: 1}} />
            <button className={styles.startButton} disabled={isDisabled} onClick={() => navigate("/finder/briefing/alert")}>
                Пройти брифинг
            </button>
            <div className={styles.additionalButtons}>
                {additionalButtons.map(({text, url}, i) => (
                    <button key={i} className={styles.additionalButton} onClick={() => navigate(url)}>
                        {text}
                    </button>
                ))}
            </div>
        </div>
    );
}
