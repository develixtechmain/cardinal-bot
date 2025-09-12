import React, {ReactElement} from 'react';
import styles from './VerifyBlock.module.css';

interface VerifyBlockProps {
    icon: ReactElement;
    title: string;
    value: string;
}

export const VerifyBlock: React.FC<VerifyBlockProps> = ({icon, title, value}) => {
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
