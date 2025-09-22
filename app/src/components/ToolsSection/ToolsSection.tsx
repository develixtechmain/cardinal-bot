import styles from "./ToolsSection.module.css";
import {FC} from "react";

import {Tool} from "../../types/home";
import {ToolID} from "../../utils/consts";
import LearnMoreButton from "../common/Buttons/LearnMoreButton";
import Delimiter from "../common/Delimiter/Delimiter";
import {ToolCard} from "./ToolCard";

interface ToolsSectionProps {
    tools: Tool[];
    showModal: Partial<Record<ToolID, () => void>>;
    showTitle?: boolean;
}

const ToolsSection: FC<ToolsSectionProps> = ({tools, showModal, showTitle = true}) => {
    return (
        <section className={styles.toolsSection}>
            {showTitle && (
                <div className={styles.title}>
                    <span>Выберите инструмент лидогенерации</span>
                    <span className={styles.titleArrow}>{" >"}</span>
                </div>
            )}
            <div className={styles.toolsList}>
                {tools.map((tool) => (
                    <div key={tool.id}>
                        <ToolCard tool={tool} />
                        <LearnMoreButton showModal={showModal[tool.id] ?? (() => console.error(`Tool ${tool.id} learning button is not setup`))} />
                        <Delimiter />
                    </div>
                ))}
            </div>
        </section>
    );
};

export default ToolsSection;
