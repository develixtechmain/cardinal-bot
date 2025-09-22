import styles from "./AboutToolModalFooter.module.css";
import {FC} from "react";

import {useLocation} from "wouter";

import WideButton from "../Buttons/WideButton";

const AboutToolModalFooter: FC = () => {
    const [, navigate] = useLocation();
    return (
        <>
            <div className={styles.title}>
                <span>
                    <span className={styles.purple}>//</span>
                    <span>Нужна помощь?</span>
                </span>
            </div>

            <div className={styles.subtitle}>Мы всегда рядом, чтобы ты быстро разобрался и начал получать лиды.</div>

            <div className={styles.supportSection}>
                <div className={styles.supportBlock}>
                    <div className={styles.supportHeader}>
                        <div className={styles.dot} />
                        <span>Персональный менеджер</span>
                    </div>
                    <div className={styles.supportDescription} style={{paddingRight: 20}}>
                        <div className={styles.stick} />
                        <span>Тебе назначается специалист, который настроит сервис и подскажет, как выжать из него максимум.</span>
                    </div>
                </div>
                <div className={styles.supportBlock}>
                    <div className={styles.supportHeader}>
                        <div className={styles.dot} />
                        <span>Обучающие материалы</span>
                    </div>
                    <div className={styles.supportDescription} style={{paddingRight: 45}}>
                        <div className={styles.stick} />
                        <span>Пошаговые инструкции, руководства и видео, чтобы легко освоить работу.</span>
                    </div>
                </div>
                <div className={styles.supportBlock}>
                    <div className={styles.supportHeader}>
                        <div className={styles.dot} />
                        <span>Техническая поддержка</span>
                    </div>
                    <div className={styles.supportDescription} style={{paddingRight: 115}}>
                        <div className={styles.stick} />
                        <span>Оперативная экспертов, помощь по любым вопросам.</span>
                    </div>
                </div>
                <WideButton
                    color="#31125C"
                    text={
                        <div className={styles.supportButton}>
                            <img height="19px" width="18px" src="/assets/about-support.svg" alt=" " />
                            Написать в тех поддержку
                        </div>
                    }
                    buttonStyle={{border: "1px solid #7211F8", borderRadius: 10, minHeight: 45, marginTop: 9}}
                    onClick={() => navigate("https://google.com")}
                />
            </div>
        </>
    );
};

export default AboutToolModalFooter;
