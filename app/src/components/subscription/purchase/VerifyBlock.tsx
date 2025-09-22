import styles from "./VerifyBlock.module.css";
import {FC, ReactElement} from "react";

interface VerifyBlockProps {
    icon: ReactElement;
    title: string;
    value: string;
}

export const VerifyBlock: FC<VerifyBlockProps> = ({icon, title, value}) => {
    return (
        <div className={styles.container}>
            <div className={styles.header}>
                {icon}
                {title}
            </div>
            <div className={styles.value}>{value}</div>
        </div>
    );
};
