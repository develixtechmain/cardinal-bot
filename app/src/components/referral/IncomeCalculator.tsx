import React, {useState} from 'react';
import styles from './IncomeCalculator.module.css';

export const IncomeCalculator: React.FC = () => {
    const [count, setCount] = useState(50);

    const digitW = 10;
    const sidePad = 12;
    const minW = 44;
    const bubbleWidth = Math.max(minW, String(count).length * digitW + sidePad * 2);

    return (
        <div className={styles.container}>
            <div className={styles.title}>
                Доход не ограничен
            </div>
            <div className={styles.subtitle}>
                <span>
                    <span>Получайте до</span>
                    <span style={{color: "#BEF811", fontWeight: 500}}> 50% с каждой оплаты </span>
                    <span>приведённых вами пользователей сервиса в течении года</span>
                </span>
            </div>

            <div className={styles.incomeBlock}>
                <div className={styles.count}>
                    <span className={styles.incomeTitle}>
                        <span style={{color: "#BEF811"}}>//</span>
                        <span style={{color: "#767676"}}>Кол-во регистраций</span>
                    </span>
                    <span className={styles.incomeValue}>{count}</span>
                </div>
                <div className={styles.summary}>
                    <span style={{color: "#BEF81199"}} className={styles.incomeTitle}>//Доход за год</span>
                    <span className={styles.incomeValue}>
                        <span>{(count * 14500).toLocaleString("ru-RU")}</span>
                        <span style={{fontSize: 8}}> руб.</span>
                    </span>
                </div>
            </div>

            <div className={styles.incomeSubtitle}>
                Расчет сделан в информационных целях и не является офертой
            </div>

            <div className={styles.sliderWrapper}>
                <div
                    className={styles.sliderBubble}
                    style={{
                        left: `calc(${count}% + (14px - 9.5px))`,
                        width: `${bubbleWidth}px`
                    }}
                >
                    {count}
                </div>
                <input
                    type="range"
                    min={1}
                    max={200}
                    value={count}
                    onChange={(e) => setCount(Number(e.target.value))}
                    className={styles.slider}
                    style={{
                        backgroundImage: `linear-gradient(to right, rgba(190,248,17,0.5) 0%, rgba(190,248,17,0.5) ${count}%, rgba(190,248,17,0.25) ${count}%, rgba(190,248,17,0.25) 100%)`
                    }}
                />

            </div>
        </div>
    );
};
