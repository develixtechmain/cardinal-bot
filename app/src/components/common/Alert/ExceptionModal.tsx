import styles from "./ExceptionModal.module.css";
import {FC} from "react";

import {useLocation} from "wouter";

import OverlayModal from "./OverlayModal";

interface ExceptionModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const ExceptionModal: FC<ExceptionModalProps> = ({isOpen, onClose}) => {
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
                <img height="28px" width="30px" className={styles.closeButon} onClick={onClose} src="/assets/icons/close.svg" alt="CLOSE" />
                <img height="55px" width="60px" src="/assets/error.svg" alt="ОШИБКА!" />
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
