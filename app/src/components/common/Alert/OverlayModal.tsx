import React from 'react';
import ReactDOM from 'react-dom';
import styles from './OverlayModal.module.css';

interface ModalProps {
    isOpen: boolean;
    onClose?: () => void;
    children: React.ReactNode;
    closeOnContentClick?: boolean;
    centered?: boolean;
}

const OverlayModal: React.FC<ModalProps> = ({isOpen, onClose, children, closeOnContentClick = false, centered = true}) => {
    if (!isOpen) return null;

    const handleOverlayClick = () => {
        if (onClose) onClose();
    };

    const handleContentClick = (e: React.MouseEvent) => {
        if (!closeOnContentClick) e.stopPropagation();
        else if (onClose) onClose();
    };

    return ReactDOM.createPortal(
        <div className={styles.overlay} onClick={handleOverlayClick} style={{
            "--align": centered ? "center" : "start"
        } as React.CSSProperties}>
            <div onClick={handleContentClick}>
                {children}
            </div>
        </div>,
        document.body
    );
};

export default OverlayModal;