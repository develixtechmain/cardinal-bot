import React from "react";
import styles from "./BriefingExampleBlock.module.css"

interface BriefingExampleBlockProps {
    good: boolean;
    title: string;
    description: string;
}

const BriefingExampleBlock: React.FC<BriefingExampleBlockProps> = ({good, title, description}) => {
    return (
        <div className={styles.container}>
            <img height="15px" width="15px" src={good ? "/assets/finder/briefing/hint-good.svg" : "/assets/finder/briefing/hint-bad.svg"} alt=" "/>
            <div className={styles.text}>
                <span className={styles.title}>{title}</span>
                <span className={styles.description}>{description}</span>
            </div>
        </div>
    );
};

export default BriefingExampleBlock;