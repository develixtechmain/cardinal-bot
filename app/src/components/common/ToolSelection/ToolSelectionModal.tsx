import React from "react";
import OverlayModal from "../Alert/OverlayModal";
import styles from "./ToolSelectionModal.module.css"
import {tools} from "../../../utils/consts";
import {ToolCard} from "./ToolCard";

interface ToolSelectionModalProps {
    toolId: string;
    isOpen: boolean;
    onClose: () => void;
}

const ToolSelectionModal: React.FC<ToolSelectionModalProps> = ({toolId, isOpen, onClose}) => {
    return (
        <OverlayModal
            isOpen={isOpen}
            onClose={onClose}
        >
            <div className={styles.container}>
                <div className={styles.toolsSection}>
                    {Object.values(tools).map((tool) => (
                        <ToolCard key={tool.id} tool={tool} currentToolId={toolId} onClose={onClose}/>
                    ))}
                </div>
                <div className={styles.footer}>
                    <span className={styles.purple}>// </span>
                    <span>Выберите инструмент</span>
                    <span className={styles.purple}> //</span>
                </div>
            </div>
        </OverlayModal>
    );
};

export default ToolSelectionModal;