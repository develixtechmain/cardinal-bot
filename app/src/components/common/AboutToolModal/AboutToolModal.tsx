import styles from "./AboutToolModal.module.css";
import {FC, ReactNode} from "react";

import OverlayModal from "../../common/Alert/OverlayModal";
import Delimiter from "../Delimiter/Delimiter";
import AboutToolModalFooter from "./AboutToolModalFooter";

interface AboutToolModalProps {
    isOpen: boolean;
    onClose: () => void;
    header: ReactNode;
    children: ReactNode;
}

const AboutToolModal: FC<AboutToolModalProps> = ({isOpen, onClose, header, children}) => {
    return (
        <OverlayModal isOpen={isOpen} onClose={onClose} centered={false}>
            <div className={styles.overlay} onClick={onClose}>
                <div className={styles.container} onClick={(e) => e.stopPropagation()}>
                    {header}
                    <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "100%", marginLeft: 2, marginRight: 2}} />
                    {children}
                    <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "100%", marginLeft: 2, marginRight: 2}} />
                    <AboutToolModalFooter />
                </div>
            </div>
        </OverlayModal>
    );
};

export default AboutToolModal;
