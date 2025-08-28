import React from "react";
import styles from "./BriefingExamplesSection.module.css"
import BriefingExampleBlock from "./BriefingExampleBlock";

interface BriefingExamplesSectionProps {
    good: boolean;
    examples: { title: string; description: string }[]
}

const BriefingExamplesSection: React.FC<BriefingExamplesSectionProps> = ({good, examples}) => {
    return (
        <div className={styles.container}>
            {examples.map(example => (
                <BriefingExampleBlock good={good} title={example.title} description={example.description}/>
            ))}
        </div>
    );
};

export default BriefingExamplesSection;