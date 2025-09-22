import styles from "./TasksLearningSection.module.css";
import {FC} from "react";

import {useLocation} from "wouter";

import WideButton from "../../common/Buttons/WideButton";

import AddTask from "../../../assets/finder/add-task.svg";
import EditTask from "../../../assets/finder/edit-task.svg";
import Info from "../../../assets/icons/info.svg";

interface TasksLearningSectionProps {
    openLearning: () => void;
    isActive: boolean;
    newTaskAvailable: boolean;
}

export const TasksLearningSection: FC<TasksLearningSectionProps> = ({openLearning, isActive, newTaskAvailable}) => {
    const [, navigate] = useLocation();

    const contentColor = isActive ? "#7211F8" : "#232323";

    return (
        <div className={styles.container}>
            <div className={styles.title}>
                <span>Настройки ИИ парсинга </span>
                <span className={styles.purple}>{">"}</span>
            </div>
            <div className={styles.buttonsContainer}>
                <WideButton
                    color="#141414"
                    text={
                        <div className={styles.learningButton}>
                            <div className={styles.learningLabel}>
                                <EditTask height="24px" width="20px" style={{flexShrink: 0, "--content-color": contentColor} as React.CSSProperties} />
                                <div className={styles.learning}>
                                    <span className={styles.learningTitle}>Дообучить ИИ</span>
                                    <span className={styles.learningDescription}>
                                        ИИ сам задаст уточняющие вопросы — это поможет улучшить результаты поиска
                                    </span>
                                </div>
                            </div>
                            <Info height="17px" width="17px" color="#7211F8" />
                        </div>
                    }
                    buttonStyle={{borderRadius: 24, height: 79}}
                    onClick={isActive ? openLearning : undefined}
                />
                {newTaskAvailable && (
                    <WideButton
                        color="#141414"
                        text={
                            <div className={styles.briefingButton}>
                                <AddTask height="25px" width="25px" style={{flexShrink: 0, "--content-color": contentColor} as React.CSSProperties} />
                                <div className={styles.briefing}>
                                    <span>Пройти</span>
                                    <span className={styles.markedText}> новый брифинг</span>
                                </div>
                            </div>
                        }
                        buttonStyle={{borderRadius: 24, height: 79}}
                        onClick={isActive ? () => navigate("/finder/briefing/alert") : undefined}
                    />
                )}
            </div>
        </div>
    );
};
