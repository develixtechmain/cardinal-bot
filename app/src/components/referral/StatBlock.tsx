import React from 'react';
import styles from './StatBlock.module.css';

interface StatBlockProps {
    title: string;
    count: number;
    titleColor: string;
    countColor: string;
    backgroundColor: string;
    borderColor: string;
}

export const StatBlock: React.FC<StatBlockProps> = ({title, count, titleColor, countColor, backgroundColor, borderColor}) => {
    return (
        <div className={styles.container} style={{
            "--background-color": backgroundColor,
            "--border-color": borderColor,
        } as React.CSSProperties}>
            <div className={styles.title} style={{color: titleColor}}>
                {title}
            </div>
            <div className={styles.count} style={{color: countColor}}>
                {count}
            </div>
        </div>
    );
};
