import styles from "./BriefingQuestionExample.module.css";
import {FC} from "react";

import {Question} from "../../../types/finder";
import Delimiter from "../../common/Delimiter/Delimiter";
import BriefingExamplesSection from "./BriefingExamplesSection";

interface BriefingQuestionExampleProps {
    question: Question;
}

const BriefingQuestionExample: FC<BriefingQuestionExampleProps> = ({question}) => {
    return (
        <div className={styles.container}>
            <span className={styles.blockHeader}>Правильный алгоритм ответа на вопрос:</span>
            <div className={styles.question}>
                <img height="11px" width="10px" src="/assets/finder/briefing/example-question.svg" alt=" " />
                {question.question}
            </div>
            <div className={styles.description}>{question.hint.description}</div>

            <BriefingExamplesSection good={true} examples={question.hint.good} />

            <div className={styles.blockHeader} style={{marginTop: 16, marginBottom: 4}}>
                Чего избегать
            </div>
            <BriefingExamplesSection good={false} examples={question.hint.bad} />

            <Delimiter style={{backgroundColor: "#FFFFFF14", maxWidth: "80%"}} />
            <span className={styles.blockHeader}>Пример правильного ответа:</span>
            <div className={styles.example}>{question.hint.example}</div>
        </div>
    );
};

export default BriefingQuestionExample;
