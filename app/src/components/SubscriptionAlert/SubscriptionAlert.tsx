import styles from "./SubscriptionAlert.module.css";
import {FC} from "react";

const SubscriptionAlert: FC = () => {
    return (
        <div>
            <div className={styles.title}>
                <span>ДОСТУП ОГРАНИЧЕН </span>
                <span className={styles.red}>— ТАРИФ ИСТЁК</span>
            </div>
            <div className={`${styles.container} ${styles.descriptionText}`}>
                <div className={styles.containerHeader}>
                    <span className={styles.red}>//</span>
                    <span>Доступ к функциям сервиса временно заблокирован.</span>
                </div>

                <span>Оплатите тариф чтобы снова пользоваться всеми возможностями платформы и получать клиентов</span>
            </div>
        </div>
    );
};

export default SubscriptionAlert;
