import styles from "./AboutToolBlock.module.css";
import {CSSProperties, FC, ReactElement, ReactNode} from "react";

import {TextPart} from "../../../types";

interface AboutToolBlockProps {
    icon: ReactElement;
    title: TextPart[];
    description: TextPart[][];
    button?: ReactNode;
    background?: ReactNode;
    backgroundRight?: number;
    backgroundBottom?: number;
    backgroundColor?: string;
    borderColor?: string;
    headerColor?: string;
}

const AboutToolBlock: FC<AboutToolBlockProps> = ({
    icon,
    title,
    description,
    button,
    background,
    backgroundRight,
    backgroundBottom,
    backgroundColor = "#0E0E0E",
    borderColor = "#7211F8",
    headerColor = "#202020"
}) => {
    return (
        <div className={styles.container} style={{"--background-color": backgroundColor, "--border-color": borderColor} as CSSProperties}>
            {background && (
                <div
                    className={styles.background}
                    style={
                        {
                            "--background-right": backgroundRight ? `${backgroundRight}px` : "0",
                            "--background-bottom": backgroundBottom ? `${backgroundBottom}px` : "0"
                        } as CSSProperties
                    }
                >
                    {background}
                </div>
            )}
            <div className={styles.header} style={{"--header-color": headerColor} as CSSProperties}>
                {icon}
                <span>
                    {title.map(({text, bold, styles}, index) => (
                        <span key={index} style={bold ? {...styles, fontWeight: 700} : styles}>
                            {text}
                        </span>
                    ))}
                </span>
            </div>
            <div className={styles.description} style={{marginBottom: button ? 33 : 12}}>
                {description.map((descriptionParts, index) => (
                    <span key={index}>
                        {descriptionParts.map(({text, bold, styles}, i) => (
                            <span key={i}>
                                <span style={bold ? {...styles, fontWeight: 700} : styles}>{text}</span>
                                {i < descriptionParts.length - 1 && <span> </span>}
                            </span>
                        ))}
                    </span>
                ))}
            </div>
            {button}
        </div>
    );
};

export default AboutToolBlock;
