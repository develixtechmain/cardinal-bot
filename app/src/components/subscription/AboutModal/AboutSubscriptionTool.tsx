import styles from "./AboutSubscriptionTool.module.css";
import {FC, ReactElement} from "react";

import {TextPart} from "../../../types";
import WideButton from "../../common/Buttons/WideButton";

import Mark from "../../../assets/icons/mark.svg";
import MoveArrowIcon from "../../../assets/icons/move-arrow.svg";
import FullEagle from "../../../assets/subscription/full-eagle.svg";

interface AboutToolProps {
    icon: ReactElement;
    title: string;
    description: TextPart[];
    about: TextPart[][];
    summary: TextPart[][];
    openAboutToolModal: () => void;
    close: () => void;
    first?: boolean;
}

const AboutSubscriptionTool: FC<AboutToolProps> = ({icon, title, description, about, summary, openAboutToolModal, close, first = false}) => {
    return (
        <div className={styles.container} style={first ? undefined : {marginTop: 29}}>
            <div className={styles.header}>
                {icon}
                <div className={styles.headerTitle}>{title}</div>
            </div>

            <div className={styles.description}>
                <span>
                    {description.map(({text, bold}, index) => (
                        <span key={index} style={bold ? {fontWeight: 700} : undefined}>
                            {text}
                        </span>
                    ))}
                </span>
            </div>

            <div className={styles.aboutSection}>
                <div className={styles.title}>
                    <span>
                        <span className={styles.purple}>//</span>
                        <span>Коротко о инструменте</span>
                    </span>
                </div>
                {about.map((aboutParts, index) => (
                    <div key={index} className={styles.markBlock}>
                        <Mark height="15px" width="15px" className={styles.purple} style={{flexShrink: 0}} />
                        <span>
                            {aboutParts.map(({text, bold}, i) => (
                                <span key={i} className={styles.markText}>
                                    <span style={bold ? {fontWeight: 700, color: "white"} : undefined}>{text}</span>
                                    {i < aboutParts.length - 1 && <span> </span>}
                                </span>
                            ))}
                        </span>
                    </div>
                ))}
            </div>

            <div style={{padding: "14px 12px 10px 12px"}}>
                <WideButton
                    color="#2E1B49"
                    text={
                        <div className={styles.aboutButton}>
                            <MoveArrowIcon color="#7211F8" />
                            <span style={{color: "#7211F8"}}>Узнать больше</span>
                        </div>
                    }
                    buttonStyle={{borderRadius: 12, height: 48, border: "1px solid #7211F8"}}
                    onClick={openAboutToolModal}
                />
            </div>

            <div className={styles.summarySection}>
                <div className={styles.title}>
                    <span>
                        <span className={styles.green}>//</span>
                        <span>Что ты получаешь в итоге</span>
                    </span>
                </div>
                {summary.map((summaryParts, index) => (
                    <div key={index} className={styles.markBlock}>
                        <Mark height="15px" width="15px" className={styles.green} style={{flexShrink: 0}} />
                        <span>
                            {summaryParts.map(({text, bold}, i) => (
                                <span key={i} className={styles.markText}>
                                    <span style={bold ? {fontWeight: 700, color: "white"} : undefined}>{text}</span>
                                    {i < summaryParts.length - 1 && <span> </span>}
                                </span>
                            ))}
                        </span>
                    </div>
                ))}
            </div>

            <div style={{padding: "16px 12px 0 12px"}}>
                <WideButton
                    color="#7211F8"
                    text={
                        <div className={styles.subscriptionButton}>
                            <FullEagle height="19px" width="33px" color="white" />
                            <span>Офоромить подписку</span>
                        </div>
                    }
                    buttonStyle={{borderRadius: 12, height: 47}}
                    onClick={close}
                />
            </div>
        </div>
    );
};

export default AboutSubscriptionTool;
