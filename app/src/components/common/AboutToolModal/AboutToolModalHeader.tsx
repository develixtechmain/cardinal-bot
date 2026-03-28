import styles from "./AboutToolModalHeader.module.css";
import {FC} from "react";

import {TextPart} from "../../../types";
import Delimiter from "../Delimiter/Delimiter";

interface AboutToolModalHeaderProps {
    title: TextPart[];
    description: string;
    infoTitle: string;
    infoDescription: TextPart[];
}

const AboutToolModalHeader: FC<AboutToolModalHeaderProps> = ({title, description, infoTitle, infoDescription}) => {
    return (
        <>
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
