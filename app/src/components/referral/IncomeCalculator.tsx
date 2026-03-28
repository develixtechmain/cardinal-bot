import styles from "./IncomeCalculator.module.css";
import {FC, useLayoutEffect, useRef, useState} from "react";

import Eagle from "../../assets/icons/eagle.svg";

export const IncomeCalculator: FC = () => {
    const [count, setCount] = useState(50);

    const countRef = useRef<SVGTextElement>(null);
    const sliderRef = useRef<HTMLInputElement>(null);
    const [bubbleLeft, setBubbleLeft] = useState(0);
    const [bubbleWidth, setBubbleWidth] = useState(44);
    const [bubbleScale, setBubbleScale] = useState(44);

    const updateBubblePosition = () => {
        if (!countRef.current || !sliderRef.current) return;

        const slider = sliderRef.current;
        const sliderWidth = slider.offsetWidth;

        const baseWidth = 44;
        const thumbWidth = 19;
        const min = Number(slider.min);
        const max = Number(slider.max);

        const percent = (count - min) / (max - min);
        const bubblePos = percent * (sliderWidth - thumbWidth);

        const wrapper = slider.parentElement;
        const wrapperPaddingLeft = wrapper ? parseFloat(getComputedStyle(wrapper).paddingLeft) : 0;

        const textWidth = countRef.current.getComputedTextLength();
        const svgWidth = Math.max(44, textWidth + 5 * 2);

        setBubbleLeft(wrapperPaddingLeft + bubblePos + thumbWidth / 2 - svgWidth / 2 + 2);
        setBubbleWidth(svgWidth);
        setBubbleScale(svgWidth / baseWidth);
    };

    useLayoutEffect(() => {
        updateBubblePosition();
    }, [count]);

    return (
        <div className={styles.container}>
            <div className={styles.title}>
                Доход не ограничен
                <img height="26px" width="26px" src="/assets/referral/calculator-info.svg" alt=" " />
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
                    <div className={styles.summaryEagle}>
                        <Eagle height="16px" width="16px" color="#BEF811" />
                    </div>
                    <span style={{color: "#BEF81199"}} className={styles.incomeTitle}>
                        //Доход за год
                    </span>
                    <span className={styles.incomeValue}>
                        <span>{(count * 14500).toLocaleString("ru-RU").replace(/\u00A0/g, " ")}</span>
                        <span style={{fontSize: 8}}> руб.</span>
                    </span>
                </div>
            </div>

            <div className={styles.incomeSubtitle}>
                <span>Расчет сделан в информационных целях и не является офертой</span>
            </div>

            <div className={styles.sliderWrapper}>
                <svg
                    className={styles.sliderBubble}
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    height="43"
                    width={bubbleWidth}
                    viewBox={`0 0 ${bubbleWidth} 43`}
                    style={{left: `${bubbleLeft}px`, fontFamily: "var(--font-secondary)", fontSize: 14, fontWeight: 700, letterSpacing: "-0.03em"}}
                >
                    <path
                        d="M26.0018 39.7146L24.8363 41.6837C23.7975 43.4388 20.2024 43.4388 19.1636 41.6837L17.9981 39.7146C17.0941 38.1873 16.6421 37.4236 15.916 37.0013C15.19 36.579 14.2758 36.5633 12.4476 36.5318C9.74857 36.4853 8.05581 36.3199 6.63615 35.7319C4.0021 34.6408 1.90936 32.548 0.818295 29.914C0 27.9384 0 25.434 0 20.4251V18.2751C0 11.2372 0 7.71822 1.58412 5.13316C2.47052 3.68668 3.68667 2.47053 5.13314 1.58413C7.71819 0 11.2371 0 18.275 0H25.725C32.7629 0 36.2818 0 38.8669 1.58413C40.3133 2.47053 41.5295 3.68668 42.4159 5.13316C44 7.71822 44 11.2372 44 18.2751V20.4251C44 25.434 44 27.9384 43.1817 29.914C42.0906 32.548 39.9979 34.6408 37.3638 35.7319C35.9442 36.3199 34.2514 36.4853 31.5523 36.5318C29.7241 36.5633 28.81 36.579 28.0839 37.0013C27.3579 37.4236 26.9058 38.1873 26.0018 39.7146Z"
                        fill="#BEF811"
                        transform={`scale(${bubbleScale}, 1)`}
                    />

                    <text ref={countRef} x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" fill="#141414" dy="-2">
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
