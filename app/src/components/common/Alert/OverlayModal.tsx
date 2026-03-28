import styles from "./OverlayModal.module.css";
import {CSSProperties, FC, MouseEvent, ReactNode} from "react";

import {createPortal} from "react-dom";

interface ModalProps {
    isOpen: boolean;
    onClose?: () => void;
    children: ReactNode;
    closeOnContentClick?: boolean;
    centered?: boolean;
    blur?: number;
}

const OverlayModal: FC<ModalProps> = ({isOpen, onClose, children, closeOnContentClick = false, centered = true, blur = 4}) => {
    if (!isOpen) return null;

    const handleOverlayClick = () => {
        if (onClose) onClose();
    };

    const handleContentClick = (e: MouseEvent) => {
        if (!closeOnContentClick) e.stopPropagation();
        else if (onClose) onClose();
    };

    return createPortal(
        <div
            className={styles.overlay}
            onClick={handleOverlayClick}
            style={{"--align": centered ? "center" : "start", "--blur": `blur(${blur}px)`} as CSSProperties}
        >
            <div className={styles.wrapper} onClick={handleContentClick}>
                {children}
            </div>
        </div>,
        document.body
    );
};

export default OverlayModal;
