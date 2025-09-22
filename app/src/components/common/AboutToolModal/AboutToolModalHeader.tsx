import styles from "./AboutToolModalHeader.module.css";
import {FC, ReactElement} from "react";

import {TextPart} from "../../../types";
import Delimiter from "../Delimiter/Delimiter";

interface AboutToolModalHeaderProps {
    icon: ReactElement;
    title: TextPart[];
    description: string;
    infoTitle: string;
    infoDescription: TextPart[];
    onClose: () => void;
}

const AboutToolModalHeader: FC<AboutToolModalHeaderProps> = ({icon, title, description, infoTitle, infoDescription, onClose}) => {
    return (
        <>
            <div className={styles.header}>
                {icon}
                <span>как работает этот инструмент</span>
                <img height="23px" width="25px" src="/assets/about-exit.svg" alt="CLOSE" onClick={onClose} />
            </div>

            <div className={styles.title}>
                <span>
                    {title.map(({text, styles}, index) => (
                        <span key={index} style={styles}>
                            {text}
                        </span>
                    ))}
                </span>
            </div>

            <div className={styles.description}>{description}</div>

            <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "100%", marginLeft: 2, marginRight: 2}} />

            <div className={styles.infoBlock}>
                <div className={styles.infoTitle}>
                    <span>
                        <span className={styles.purple}>//</span>
                        <span>{infoTitle}</span>
                    </span>
                </div>
                <div className={styles.infoDescription}>
                    {infoDescription.map(({text, bold, styles}, index) => (
                        <span key={index} style={bold ? {...styles, fontWeight: 700} : styles}>
                            {text}
                        </span>
                    ))}
                </div>
            </div>
        </>
    );
};

export default AboutToolModalHeader;
