import styles from "./StatBlock.module.css";
import {CSSProperties, FC} from "react";

interface StatBlockProps {
    title: string;
    count: number;
    titleColor: string;
    countColor: string;
    backgroundColor: string;
    borderColor: string;
}

export const StatBlock: FC<StatBlockProps> = ({title, count, titleColor, countColor, backgroundColor, borderColor}) => {
    return (
        <div className={styles.container} style={{"--background-color": backgroundColor, "--border-color": borderColor} as CSSProperties}>
            <div className={styles.title} style={{color: titleColor}}>
                {title}
            </div>
            <div className={styles.count} style={{color: countColor}}>
                {count}
            </div>
        </div>
    );
};
