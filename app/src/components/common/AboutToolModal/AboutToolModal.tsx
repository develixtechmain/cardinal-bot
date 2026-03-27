import styles from "./AboutToolModal.module.css";
import {FC, ReactElement, ReactNode} from "react";

import OverlayModal from "../../common/Alert/OverlayModal";
import Delimiter from "../Delimiter/Delimiter";
import AboutToolModalFooter from "./AboutToolModalFooter";

interface AboutToolModalProps {
    icon: ReactElement;
    isOpen: boolean;
    onClose: () => void;
    header: ReactNode;
    children: ReactNode;
}

const AboutToolModal: FC<AboutToolModalProps> = ({icon, isOpen, onClose, header, children}) => {
    return (
        <OverlayModal isOpen={isOpen} onClose={onClose} centered={false}>
            <div className={styles.overlay} onClick={onClose}>
                <div className={styles.container} onClick={(e) => e.stopPropagation()}>
                    <div className={styles.header}>
                        {icon}
                        <span>как работает этот инструмент</span>
                        <img height="23px" width="25px" src="/assets/about-exit.svg" alt="CLOSE" onClick={onClose} />
                    </div>
                    <div className={styles.content}>
                        {header}
                        <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "100%", marginLeft: 2, marginRight: 2}} />
                        {children}
                        <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "100%", marginLeft: 2, marginRight: 2}} />
                        <AboutToolModalFooter />
                    </div>
                </div>
            </div>
        </OverlayModal>
    );
};

export default AboutToolModal;
