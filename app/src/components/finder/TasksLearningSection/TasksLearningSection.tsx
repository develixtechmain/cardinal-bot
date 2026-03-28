import styles from "./TasksLearningSection.module.css";
import {CSSProperties, FC} from "react";

import {useLocation} from "wouter";

import WideButton from "../../common/Buttons/WideButton";

import AddTask from "../../../assets/finder/add-task.svg";

interface TasksLearningSectionProps {
    openTaskLimit: () => void;
    isActive: boolean;
    newTaskAvailable: boolean;
}

export const TasksLearningSection: FC<TasksLearningSectionProps> = ({openTaskLimit, isActive, newTaskAvailable}) => {
    const [, navigate] = useLocation();

    const contentColor = isActive ? "#7211F8" : "#232323";
    const action = newTaskAvailable ? () => navigate("/finder/briefing/alert") : openTaskLimit;

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
                        <div className={styles.briefingButton}>
                            <AddTask height="25px" width="25px" style={{flexShrink: 0, "--content-color": contentColor} as CSSProperties} />
                            <div className={styles.briefing}>
                                <span className={styles.briefingTitle}>Создать новое задание</span>
                                <div className={styles.briefingDescription}>
                                    <span>
                                        <span>Пройти </span>
                                        <span style={{fontWeight: 700}}>
                                            новый
                                            <br /> брифинг
                                        </span>
                                    </span>
                                </div>
                            </div>
                        </div>
                    }
                    buttonStyle={{borderRadius: 24, height: 79}}
                    onClick={isActive ? action : undefined}
                />
            </div>
        </div>
    );
};
