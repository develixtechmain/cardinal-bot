import styles from "./BriefingExampleModal.module.css";
import {FC} from "react";

import {Question} from "../../../types/finder";
import OverlayModal from "../../common/Alert/OverlayModal";
import WideButton from "../../common/Buttons/WideButton";
import Delimiter from "../../common/Delimiter/Delimiter";
import BriefingQuestionExample from "./BriefingQuestionExample";

interface BriefingExampleProps {
    isOpen: boolean;
    question: Question;
    useHint: () => void;
    onClose: () => void;
}

const BriefingExampleModal: FC<BriefingExampleProps> = ({question, isOpen, onClose, useHint}) => {
    return (
        <OverlayModal isOpen={isOpen} onClose={onClose} centered={false}>
            <div className={styles.overlay} onClick={onClose}>
                <div className={styles.container} onClick={(e) => e.stopPropagation()}>
                    <div className={styles.header}>
                        <span style={{marginRight: 40, marginTop: 11}}>
                            <span>Точность</span>
                            <span className={styles.purple}> в брифе</span>
                            {window.innerWidth <= 390 && <br />}
                            <span className={styles.purple}> =</span>
                            <span> точность</span>
                            <span className={styles.purple}> в заказах</span>
                        </span>
                        <img height="28px" width="31px" src="/assets/finder/briefing/example-exit.svg" alt="CLOSE" onClick={onClose} />
                    </div>
                    <div className={styles.headerDescription}>
                        <span>
                            <span className={styles.purple}>//</span>
                            <span>Чем подробнее и конкретнее ты расскажешь о себе, тем точнее система соберёт облако тегов и подберёт заказы.</span>
                        </span>
                    </div>
                    <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "80%"}} />

                    <BriefingQuestionExample question={question} />

                    {question.hint.example && (
                        <WideButton
                            color="#7211F833"
                            onClick={useHint}
                            text={
                                <div className={styles.useHintButton}>
                                    <img height="17px" width="16px" src="/assets/icons/copy.svg" alt=" " />
                                    <span>Вставить шаблон ответа</span>
                                </div>
                            }
                            buttonStyle={{borderRadius: 12, height: 52, border: "1px solid #7211F8"}}
                            style={{marginTop: 9}}
                        />
                    )}
                </div>
            </div>
        </OverlayModal>
    );
};

export default BriefingExampleModal;
