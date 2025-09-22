import styles from "./ToolCard.module.css";
import {FC} from "react";

import {useLocation} from "wouter";

import {Tool} from "../../types/home";

interface ToolCardProps {
    tool: Tool;
}

export const ToolCard: FC<ToolCardProps> = ({tool}) => {
    const [, navigate] = useLocation();
    return (
        <div className={styles.toolCards}>
            <div className={styles.toolCard} onClick={() => navigate(tool.url)}>
                <div className={styles.header}>
                    <img height="37px" width="63px" src={`/assets/${tool.id}/icon.svg`} alt=" " />
                    <span className={styles.headerText}>
                        <span>{tool.title}</span>
                        <span className={styles.headerSeparator}> // </span>
                        <span>{tool.subtitle}</span>
                    </span>
                    <img height="27px" width="48px" src={`/assets/${tool.id}/subicon.svg`} alt=" " />
                </div>
                <div className={styles.descriptionBlock}>
                    <div className={styles.descriptionText}>{tool.description}</div>
                    <div style={{flex: 1}} />
                    <div className={tool.id === "finder" ? styles.finderBackground : styles.contactCatcherBackground}>
                        <img src={`/assets/${tool.id}/background.svg`} alt=" " />
                    </div>
                </div>
            </div>
        </div>
    );
};
