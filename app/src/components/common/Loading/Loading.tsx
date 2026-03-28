import styles from "./Loading.module.css";
import {useEffect, useRef, useState} from "react";

export const Loading = () => {
    const [percentage, setPercentage] = useState(0);
    const startTimeRef = useRef<number | null>(null);
    const duration = 3000;
    const max = 99;

    useEffect(() => {
        const step = (timestamp: number) => {
            if (!startTimeRef.current) startTimeRef.current = timestamp;
            const elapsed = timestamp - startTimeRef.current;
            const progress = Math.min(elapsed / duration, 1);
            const value = Math.floor(progress * max);
            setPercentage(value);

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };

        requestAnimationFrame(step);
    }, []);

    return (
        <div className={styles.logo}>
            <img height="111px" width="187px" src="/assets/logo.svg" alt="Loading" color="#FFFFFF" />
            <div className={styles.percentageContainer}>
                <div style={{flex: 1}} />
                <div className={styles.percentage}>{percentage}%</div>
            </div>
        </div>
    );
};
