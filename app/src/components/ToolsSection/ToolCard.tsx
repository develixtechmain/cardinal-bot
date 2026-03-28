import styles from "./ToolCard.module.css";
import {FC, useEffect, useRef, useState} from "react";

import {useLocation} from "wouter";

import {Tool} from "../../types/home";

interface ToolCardProps {
    tool: Tool;
}

export const ToolCard: FC<ToolCardProps> = ({tool}) => {
    const [, navigate] = useLocation();
    const imgRef = useRef<HTMLImageElement>(null);
    const [descriptionWidth, setDescriptionWidth] = useState(0);

    const calculateDescriptionWidth = () => {
        if (!imgRef.current) return;

        const imgWidth = imgRef.current.width;
        const containerWidth = imgRef.current.parentElement?.parentElement?.offsetWidth || 0;

        if (containerWidth) setDescriptionWidth(containerWidth - imgWidth - 6);
    };

    useEffect(() => {
        calculateDescriptionWidth();

        window.addEventListener("resize", calculateDescriptionWidth);
        return () => window.removeEventListener("resize", calculateDescriptionWidth);
    }, []);

    return (
        <div className={styles.toolCard} onClick={() => (tool.external ? Telegram.WebApp.openLink(tool.url, {try_instant_view: true}) : navigate(tool.url))}>
            <div className={styles.header}>
                <img height="37px" width="63px" src={`/assets/${tool.id}/icon.svg`} alt=" " />
                <span className={styles.headerText}>
                    <span>{tool.title}</span>
                    <span className={styles.headerSeparator}> // </span>
                    <span>{tool.subtitle}</span>
                </span>
                <img height="27px" width="48px" src={`/assets/${tool.id}/subicon.svg`} alt=" " />
            </div>
            <div className={styles.descriptionText} style={{width: descriptionWidth ? `${descriptionWidth}px` : "auto"}}>
                {tool.description}
            </div>
            <div className={`${styles.toolBackground} ${tool.id === "finder" ? styles.finderBackground : styles.contactCatcherBackground}`}>
                <img ref={imgRef} src={`/assets/${tool.id}/background.svg`} alt=" " onLoad={calculateDescriptionWidth} />
            </div>
        </div>
    );
};
