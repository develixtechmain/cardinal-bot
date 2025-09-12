import React, {useLayoutEffect, useRef, useState} from 'react';
import styles from './IncomeCalculator.module.css';

export const IncomeCalculator: React.FC = () => {
    const [count, setCount] = useState(50);

    const sliderRef = useRef<HTMLInputElement>(null);
    const bubbleRef = useRef<SVGSVGElement>(null);
    const [bubbleLeft, setBubbleLeft] = useState(0);
    const [bubbleWidth, setBubbleWidth] = useState(44);

    const updateBubblePosition = () => {
        if (!sliderRef.current || !bubbleRef.current) return;
        const slider = sliderRef.current;
        const bubble = bubbleRef.current;

        const sliderWidth = slider.offsetWidth;
        const bubbleWidth = bubble.getBoundingClientRect().width;
        const thumbWidth = 19;

        const min = Number(slider.min);
        const max = Number(slider.max);

        const percent = (count - min) / (max - min);
        const bubblePos = percent * (sliderWidth - thumbWidth);

        const wrapper = slider.parentElement;
        const wrapperPaddingLeft = wrapper ? parseFloat(getComputedStyle(wrapper).paddingLeft) : 0;

        setBubbleLeft(wrapperPaddingLeft + bubblePos + thumbWidth / 2 - bubbleWidth / 2);
        setBubbleWidth(count < 100 ? 44 : 50);
    };

    useLayoutEffect(() => {
        updateBubblePosition();
    }, [count]);

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
                <svg ref={bubbleRef} className={styles.sliderBubble} style={{left: `${bubbleLeft}px`}} fill="none" xmlns="http://www.w3.org/2000/svg"
                     height="43" width={bubbleWidth} viewBox={`0 0 ${bubbleWidth} 43`}>
                    {count < 100 ?
                        <path
                            d="M26.0018 39.7146L24.8363 41.6837C23.7975 43.4388 20.2024 43.4388 19.1636 41.6837L17.9981 39.7146C17.0941 38.1873 16.6421 37.4236 15.916 37.0013C15.19 36.579 14.2758 36.5633 12.4476 36.5318C9.74857 36.4853 8.05581 36.3199 6.63615 35.7319C4.0021 34.6408 1.90936 32.548 0.818295 29.914C0 27.9384 0 25.434 0 20.4251V18.2751C0 11.2372 0 7.71822 1.58412 5.13316C2.47052 3.68668 3.68667 2.47053 5.13314 1.58413C7.71819 0 11.2371 0 18.275 0H25.725C32.7629 0 36.2818 0 38.8669 1.58413C40.3133 2.47053 41.5295 3.68668 42.4159 5.13316C44 7.71822 44 11.2372 44 18.2751V20.4251C44 25.434 44 27.9384 43.1817 29.914C42.0906 32.548 39.9979 34.6408 37.3638 35.7319C35.9442 36.3199 34.2514 36.4853 31.5523 36.5318C29.7241 36.5633 28.81 36.579 28.0839 37.0013C27.3579 37.4236 26.9058 38.1873 26.0018 39.7146Z"
                            fill="#BEF811"/> :
                        <path
                            d="M29.547 39.7146L28.274 41.6837C27.186 43.4388 23.014 43.4388 21.926 41.6837L20.653 39.7146C19.693 38.1873 19.197 37.4236 18.437 37.0013C17.677 36.579 16.746 36.5633 14.598 36.5318C11.446 36.4853 9.423 36.3199 7.755 35.7319C4.671 34.6408 2.229 32.548 0.955 29.914C0 27.9384 0 25.434 0 20.4251V18.2751C0 11.2372 0 7.71822 1.8 5.13316C2.805 3.68668 4.19 2.47053 5.85 1.58413C8.79 0 12.8 0 20.8 0H29.2C37.2 0 41.21 0 44.15 1.58413C45.81 2.47053 47.195 3.68668 48.2 5.13316C50 7.71822 50 11.2372 50 18.2751V20.4251C50 25.434 50 27.9384 49.045 29.914C47.771 32.548 45.329 34.6408 42.245 35.7319C40.577 36.3199 38.554 36.4853 35.402 36.5318C33.254 36.5633 32.323 36.579 31.563 37.0013C30.803 37.4236 30.307 38.1873 29.547 39.7146Z"
                            fill="#BEF811"
                        />
                    }
                    <text
                        x="50%" y="50%" dominantBaseline="middle" textAnchor="middle"
                        fontFamily="var(--font-secondary)"
                        fontSize="14"
                        fontWeight="700"
                        fill="#141414"
                    >
                        {count}
                    </text>
                </svg>
                <input
                    ref={sliderRef}
                    type="range"
                    min={1}
                    max={200}
                    value={count}
                    onChange={(e) => setCount(Number(e.target.value))}
                    className={styles.slider}
                    style={{
                        backgroundImage: `linear-gradient(to right, rgba(190,248,17,0.5) 0%, rgba(190,248,17,0.5) ${count / 2}%, rgba(190,248,17,0.25) ${count / 2}%, rgba(190,248,17,0.25) 100%)`
                    }}
                />
            </div>
        </div>
    );
};
