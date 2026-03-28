import styles from "./BottomSection.module.css";
import {FC} from "react";

import {DOCS_URL, SUPPORT_URL} from "../../../utils/consts";
import WideButton from "../Buttons/WideButton";

import MoveArrowIcon from "../../../assets/icons/move-arrow.svg";

interface HelpButton {
    label: string;
    id: string;
    description: string;
    buttonLabel: string;
    url: string;
}

const helpButtons: HelpButton[] = [
    {id: "support", label: "Тех поддержка", description: "Напишите нам — отвечаем в течение минуты и решаем всё.", buttonLabel: "Написать", url: SUPPORT_URL},
    {id: "docs", label: "База знаний", description: "Всё о работе с сервисом: инструкции, советы, фишки", buttonLabel: "Перейти", url: DOCS_URL}
];

const handleOpen = (filePath: string) => {
    window.Telegram.WebApp.openLink(filePath);
};

const BottomSection: FC = () => {
    return (
        <>
            <div className={styles.footer}>
                <div className={styles.infoCards}>
                    {helpButtons.map(({description, label, id, buttonLabel, url}) => (
                        <div key={id} className={styles.infoCard} onClick={() => Telegram.WebApp.openLink(url, {try_instant_view: true})}>
                            <div className={styles.title}>
                                <span className={styles.titleSeparator}>//</span>
                                <span>{label} </span>
                                <img height={id === "support" ? 12 : 11} width={id === "support" ? 11 : 14} src={`/assets/icons/${id}.svg`} alt=" " />
                            </div>
                            <div className={styles.description}>{description}</div>
                            <div style={{flex: 1}} />
                            <WideButton
                                color="#31125C"
                                compact={true}
                                text={
                                    <div className={styles.moveButton}>
                                        <MoveArrowIcon height="19px" width="19px" color="#7211F8" />
                                        {buttonLabel}
                                    </div>
                                }
                                buttonStyle={{borderRadius: 11, height: 52, border: "2px solid #7211F8"}}
                            />
                        </div>
                    ))}
                </div>
                <div className={styles.offers}>
                    <div className={styles.offer} style={{flex: 3}} onClick={() => handleOpen("/docs/public_offer.doc")}>
                        Публичная оферта
                    </div>
                    <div className={styles.offer} style={{flex: 4}} onClick={() => handleOpen("/docs/conf.doc")}>
                        Политика конфиденциальности
                    </div>
                </div>
            </div>
            <div className={styles.footerIcon}>
                <img src="/assets/footer.svg" alt=" " />
            </div>
        </>
    );
};

export default BottomSection;
