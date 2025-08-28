import React from 'react';
import {Tool} from '../../types/home';
import styles from './ToolsSection.module.css';
import {ToolCard} from "./ToolCard";
import Delimiter from "../common/Delimiter/Delimiter";
import LearnMoreButton from "../common/Buttons/LearnMoreButton";

interface ToolsSectionProps {
    tools: Tool[];
    showTitle?: boolean;
}

const ToolsSection: React.FC<ToolsSectionProps> = ({tools, showTitle = true}) => {
    return (
        <section className={styles.toolsSection}>
            {showTitle &&
                <div className={styles.title}>
                    <span>Выберите инструмент лидогенерации</span>
                    <span className={styles.titleArrow}>{' >'}</span>
                </div>
            }
            <div className={styles.toolsList}>
                {tools.map((tool) => (
                    <div key={tool.id}>
                        <ToolCard tool={tool}/>
                        <LearnMoreButton url={tool.aboutUrl}/>
                        <Delimiter/>
                    </div>
                ))}
            </div>
        </section>
    );
};

export default ToolsSection;
