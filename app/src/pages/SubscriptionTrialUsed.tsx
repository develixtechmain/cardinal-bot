import styles from "./SubscriptionTrialUsed.module.css";
import {useEffect} from "react";

import {useLocation} from "wouter";

import {useStore} from "../store/store";
import {formatToDayMonth} from "../utils/date";

import MoveArrowIcon from "../assets/icons/move-arrow.svg";

export const SubscriptionTrialUsed = () => {
    const [, navigate] = useLocation();
    const subscription = useStore((s) => s.subscription);

    useEffect(() => {
        if (!subscription) navigate("/");
    }, []);

    const endsAt = subscription!.subscription_ends_at || subscription!.trial_ends_at;

    return (
        <div className={styles.container}>
            <img height="75px" width="75px" className={styles.icon} src="/assets/trial-used.svg" alt=" " />
            <div className={styles.textContainer}>
                <div className={styles.title}>
                    <span style={{color: "#BEF811"}}>//</span>
                    <span>Тариф активирован</span>
                </div>
                <div className={styles.description}>
                    <span className={styles.descriptionBold}>Готово!</span>
                    <span>Все функции Cardinal активированы - теперь вам доступны все сервисы и инструменты.</span>
                </div>
                <div className={styles.tillContainer}>//Тариф активен до {formatToDayMonth(endsAt!)}</div>
            </div>

            <div style={{flex: 1}} />
            <div className={styles.buttons}>
                <div className={`${styles.button} ${styles.transparent}`} onClick={() => navigate("/")}>
                    Перейти в ЛК
                </div>
                <div className={styles.moveToButtons}>
                    <div className={`${styles.button} ${styles.moveToContainer}`} onClick={() => navigate("/finder")}>
                        <MoveArrowIcon height="24px" width="24px" />
                        <span>ИИ лид файндер</span>
                    </div>
                    <div className={`${styles.button} ${styles.moveToContainer}`}>
                        <MoveArrowIcon height="24px" width="24px" />
                        <span>Перехват контактов</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
