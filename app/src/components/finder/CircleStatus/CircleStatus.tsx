import styles from "./CircleStatus.module.css";
import {useLayoutEffect, useRef, useState} from "react";

import {useStore} from "../../../store/store";

import LeadsBackground from "../../../assets/finder/leads-circle-background.svg";

interface Props {
    activeCount: number;
}

const CONTAINER_HEIGH = 180;
const LEADS_CIRCLE_WIDTH = 143;
const CIRCLES_RADIUS = LEADS_CIRCLE_WIDTH / 2 + 22;
const COUNTS_RADIUS = 93;
const COUNTS_ANGLE_OFFSET = 7 * (Math.PI / 180);

const TOTAL_CIRCLES = 33;

export default function CircleStatus({activeCount}: Props) {
    const subscription = useStore((s) => s.subscription);
    const isExpired = subscription!.isSubscriptionExpired();

    const ref = useRef<HTMLDivElement>(null);
    const [width, setWidth] = useState(390);

    useLayoutEffect(() => {
        if (!ref.current) return;
        const ro = new ResizeObserver(([entry]) => {
            setWidth(entry.contentRect.width);
        });
        ro.observe(ref.current);
        return () => ro.disconnect();
    }, []);

    const leadsCircleCenterX = width / 2;
    const leadsCircleCenterY = CONTAINER_HEIGH / 2;

    const angles = Array.from({length: TOTAL_CIRCLES}, (_, i) => (180 - (i * 180) / (TOTAL_CIRCLES - 1)) * (Math.PI / 180));

    const angle0 = Math.PI + COUNTS_ANGLE_OFFSET;
    const angle33 = 0 - COUNTS_ANGLE_OFFSET;

    const points = angles.map((a) => ({x: leadsCircleCenterX + CIRCLES_RADIUS * Math.cos(a), y: leadsCircleCenterY - CIRCLES_RADIUS * Math.sin(a)}));

    return (
        <div ref={ref} className={styles.container}>
            {points.map((p, i) => (
                <div key={i} className={`${styles.smallCircle} ${i < activeCount ? styles.active : styles.disabled}`} style={{left: p.x, top: p.y}} />
            ))}

            <div
                className={styles.leadsCount}
                style={
                    {
                        left: leadsCircleCenterX + COUNTS_RADIUS * Math.cos(angle0),
                        top: leadsCircleCenterY - COUNTS_RADIUS * Math.sin(angle0),
                        transform: "translate(-50%, -50%) rotate(180deg)",
                        "--count-color": "#7211F8"
                    } as React.CSSProperties
                }
            >
                0
            </div>

            <div
                className={styles.leadsCount}
                style={
                    {
                        left: leadsCircleCenterX + (COUNTS_RADIUS + 1) * Math.cos(angle33),
                        top: leadsCircleCenterY - (COUNTS_RADIUS + 1) * Math.sin(angle33),
                        transform: "translate(-50%, -50%)",
                        "--count-color": activeCount >= TOTAL_CIRCLES ? "#7211F8" : "#202020"
                    } as React.CSSProperties
                }
            >
                33
            </div>

            <div
                className={`${styles.leadsCircle} ${!isExpired ? styles.leadsActive : ""}`}
                style={
                    {
                        left: leadsCircleCenterX,
                        top: leadsCircleCenterY,
                        transform: "translate(-50%, -50%)",
                        "--background-color": isExpired ? "#3C3C3C" : "#7211F861"
                    } as React.CSSProperties
                }
            >
                <LeadsBackground
                    height="115px"
                    width="192px"
                    style={{position: "relative", top: 19, left: -24, "--content-color": isExpired ? "#232323" : "#44128A"} as React.CSSProperties}
                />
                <div className={`${styles.coreCount}`} style={{"--count-color": "#F2F2F2"} as React.CSSProperties}>
                    {activeCount}
                </div>
            </div>
        </div>
    );
}
