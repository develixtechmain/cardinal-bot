import styles from "./BriefingFullExampleModal.module.css";
import {FC, useState} from "react";

import {baseQuestions} from "../../../store/questions";
import OverlayModal from "../../common/Alert/OverlayModal";
import WideButton from "../../common/Buttons/WideButton";
import Delimiter from "../../common/Delimiter/Delimiter";
import BriefingQuestionExample from "./BriefingQuestionExample";

interface BriefingFullExampleProps {
    isOpen: boolean;
    onClose: () => void;
}

const BriefingFullExampleModal: FC<BriefingFullExampleProps> = ({isOpen, onClose}) => {
    const [selected, setSelected] = useState<number | undefined>(undefined);

    const handleSelect = (index: number) => {
        if (selected == index) setSelected(undefined);
        else setSelected(index);
    };

    return (
        <OverlayModal isOpen={isOpen} onClose={onClose} centered={false}>
            <div className={styles.overlay} onClick={onClose}>
                <div className={styles.container} onClick={(e) => e.stopPropagation()}>
                    <div className={styles.header}>
                        <span style={{marginRight: 54}}>
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

                    <div className={styles.blockHeader}>Нажмите на вопрос, чтобы увидеть примеры и шаблон качественного ответа</div>
                    <div className={styles.blockAdvice}>Не трать время на догадки — бери готовый пример и адаптируй под себя.</div>

                    <div className={styles.questions}>
                        {baseQuestions.map((question, index) => {
                            const isSelected = selected == index;
                            return (
                                <>
                                    <WideButton
                                        color={`linear-gradient(to right, ${isSelected ? "#7211F8, #040404" : "#7211F8, #430A92"})`}
                                        text={
                                            <div className={`${styles.questionButton} }`}>
                                                <span>{question.question}</span>
                                                <img
                                                    height="23px"
                                                    width="23px"
                                                    src={`/assets/finder/briefing/example_${isSelected ? "open" : "closed"}.svg`}
                                                    alt=" "
                                                />
                                            </div>
                                        }
                                        buttonStyle={{borderRadius: 11, minHeight: 44}}
                                        onClick={() => handleSelect(index)}
                                    />
                                    {isSelected && (
                                        <div key={index} className={styles.question}>
                                            <BriefingQuestionExample question={question} />
                                        </div>
                                    )}
                                </>
                            );
                        })}
                    </div>
                </div>
            </div>
        </OverlayModal>
    );
};

export default BriefingFullExampleModal;
