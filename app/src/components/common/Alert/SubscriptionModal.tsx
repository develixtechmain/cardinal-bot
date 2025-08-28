import React from 'react';
import {useLocation} from "wouter";
import OverlayModal from "./OverlayModal";
import styles from "./SubscriptionModal.module.css"
import WideButton from "../Buttons/WideButton";

interface SubscriptionModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const excluded = ["/", "/subscription"];

const SubscriptionModal: React.FC<SubscriptionModalProps> = ({isOpen, onClose}) => {
    const [location, navigate] = useLocation();

    if (excluded.includes(location)) return null;

    return (
        <OverlayModal
            isOpen={isOpen}
            onClose={() => {
                onClose();
                navigate("/");
            }}
        >
            <div className={styles.container}>
                <img height="126px" width="213px" src="/assets/subscription_expired.svg" alt="Подписка закончилась!"/>
                <div className={styles.text}>
                <span className={styles.header}>
                    <span>Доступ ограничен</span>
                    <span className={styles.red}> — тариф истёк</span>
                </span>
                    <span className={styles.description}>
                    <span className={styles.red}>//</span>
                    <span>Доступ к функциям сервиса временно заблокирован.</span>
                </span>
                    <span className={styles.advice}>
                    Оплатите тариф чтобы снова пользоваться всеми возможностями платформы и получать клиентов
                </span>
                </div>
                <WideButton color={"#F81B1120"} text={
                    <div className={styles.subscriptionExpiredButtonText}>
                        <img height="22px" width="21px" src="/assets/icons/key.svg" alt=" "/>
                        Оформить подписку
                    </div>
                } buttonStyle={{minHeight: 60, maxHeight: 60}} style={{
                    border: "1px solid #F81B11",
                    borderRadius: 19
                }} onClick={async () => navigate("/subscription")}/>
            </div>
        </OverlayModal>
    );
};

export default SubscriptionModal;