import styles from "./ClubSection.module.css";
import {FC} from "react";

import {useLocation} from "wouter";

import {useStore} from "../../store/store";
import {PartialText} from "../../types";
import WideButton from "../common/Buttons/WideButton";

import Mark from "../../assets/icons/mark.svg";
import MoveArrowIcon from "../../assets/icons/move-arrow.svg";

const benefits: PartialText[] = [
    {id: "club_benefits_services", textParts: [{text: "Слив"}, {text: "нестандартных связок", bold: true}, {text: "и сервисов"}]},
    {id: "club_benefits_sales", textParts: [{text: "Подборки полезных инструментов", bold: true}, {text: "для лидгена и автоматизации продаж"}]},
    {id: "club_benefits_templates", textParts: [{text: "Готовые шаблоны:", bold: true}, {text: "паки, офферы, тексты, оформление и т.д."}]},
    {id: "club_benefits_cases", textParts: [{text: "Эксклюзивные"}, {text: "разборы кейсов", bold: true}]}
];

const ClubSection: FC = () => {
    const [, navigate] = useLocation();
    const subscription = useStore((s) => s.subscription);

    return (
        <section className={styles.clubSection}>
            <div className={styles.clubHeader}>
                <img height="37px" width="59px" src="/assets/club.svg" alt=" " />
                <div className={styles.titleContainer}>
                    <span className={styles.title}>
                        <span>Cardinal X</span>
                        <span className={styles.separator}> // </span>
                        <span>Club</span>
                    </span>
                    <span className={styles.subtitle}>Закрытый канал с инсайдами, сервисами и готовыми шаблонами для участников.</span>
                </div>
            </div>
            <div className={styles.benefitsTitle}>Что ты найдешь в закрытом канале:</div>

            <div className={styles.benefitsList}>
                {benefits.map(({id, textParts}) => (
                    <div key={id} className={styles.benefit}>
                        <Mark height="15px" width="15px" color="#7211F8" />
                        <div>
                            {textParts.map(({bold, text}, index) => (
                                <span key={index} className={styles.benefitText}>
                                    <span style={bold ? undefined : {opacity: 0.5}}>{text}</span>
                                    {index < textParts.length - 1 && <span> </span>}
                                </span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className={styles.clubAccess}>
                <img height="10px" width="15px" src="/assets/icons/club-insider.svg" alt=" " />
                <span>Только для активных пользователей</span>
            </div>

            {subscription!.isActive() ? (
                <WideButton
                    color="#7211F833"
                    text={
                        <div className={styles.moveButton}>
                            <MoveArrowIcon color="#7211F8" />
                            <span style={{color: "#7211F8"}}>Перейти в канал</span>
                        </div>
                        //     TODO URL to channel
                    }
                    buttonStyle={{borderRadius: 12, height: 50}}
                    onClick={() => navigate("https://google.com")}
                />
            ) : (
                <WideButton
                    color="#3C3C3C"
                    text={
                        <div className={styles.moveButton}>
                            <MoveArrowIcon color={"#232323"} />
                            <span>Перейти в канал</span>
                        </div>
                    }
                    buttonStyle={{borderRadius: 12, height: 50}}
                />
            )}
        </section>
    );
};

export default ClubSection;
