import React from 'react';
import {useLocation} from "wouter";
import OverlayModal from "./OverlayModal";
import styles from "./ExceptionModal.module.css"

interface ExceptionModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const ExceptionModal: React.FC<ExceptionModalProps> = ({isOpen, onClose}) => {
    const [, navigate] = useLocation();
    return (
        <OverlayModal
            isOpen={isOpen}
            onClose={() => {
                onClose();
                navigate("/");
            }}
            closeOnContentClick={true}
        >
            <div className={styles.container}>
                <img height="55px" width="60px" src="/assets/error.svg" alt="ОШИБКА!"/>
                <span>Тех ошибка</span>
                <span className={styles.description}>
                    <span className={styles.red}>//</span>
                    <span>Доступ к функциям сервиса временно заблокирован.</span>
                </span>
            </div>
        </OverlayModal>
    );
};

export default ExceptionModal;