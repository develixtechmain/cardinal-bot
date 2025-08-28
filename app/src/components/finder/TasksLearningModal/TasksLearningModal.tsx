import React, {useState} from "react";
import OverlayModal from "../../common/Alert/OverlayModal";
import styles from "./TasksLearningModal.module.css"
import {FinderTask} from "../../../types/finder";
import {useLocation} from "wouter";
import WideButton from "../../common/Buttons/WideButton";

import Mark from "../../../assets/icons/mark.svg";
import EmptyMark from "../../../assets/icons/empty-mark.svg";
import MoveArrowIcon from "../../../assets/icons/move-arrow.svg";

interface TasksLearningModalProps {
    tasks: FinderTask[];
    isOpen: boolean;
    onClose: () => void;
}

const TasksLearningModal: React.FC<TasksLearningModalProps> = ({tasks, isOpen, onClose}) => {
    const [, navigate] = useLocation();
    const [selected, setSelected] = useState<string | undefined>(undefined);

    const handleSelection = (id: string) => {
        if (id === selected) setSelected(undefined)
        else setSelected(id)
    }

    return (
        <OverlayModal
            isOpen={isOpen}
            onClose={onClose}
        >
            <div className={styles.container}>
                <div className={styles.header}>
                    <div className={styles.headerText}>
                        <span>Выберите задачу для дообучения  </span>
                        <span className={styles.purple}>{">"}</span>
                    </div>
                    <img height="22px" width="24px" src="/assets/finder/exit.svg" alt=" " onClick={onClose}/>
                </div>
                <div className={styles.tasksList}>
                    {tasks.length > 0 ?
                        <div style={{display: "flex", flexDirection: "column", gap: 10}}>
                            {tasks.map((task, index) => (
                                <div key={index} className={styles.taskBlock} onClick={() => handleSelection(task.id)}>
                                    <div className={`${styles.dot} ${task.active ? styles.active : styles.disabled}`}/>
                                    <span>{task.title}</span>
                                    <div style={{flex: 1}}/>
                                    {task.id === selected ? <Mark height="22px" width="22px" color="#7211F8"/> :
                                        <EmptyMark height="22px" width="22px" color="#C8C7CB"/>}
                                </div>
                            ))}
                            <div className={styles.footer}>
                                Система автоматически проанализирует твои предыдущие ответы по выбранной задачи, выделит пробелы или недостающие детали и задаст
                                дополнительные вопросы.
                            </div>
                        </div> : <div>
                            <div className={styles.taskBlock} style={{marginBottom: 9}}>
                                <div className={`${styles.dot} ${styles.disabled}`}/>
                                <span>//нет созданных задач</span>
                            </div>
                            <WideButton color="#7211F833" text={
                                <div className={styles.moveButton}>
                                    <MoveArrowIcon color="#7211F8"/>
                                    <span style={{color: "#7211F8"}}>Создать задачу</span>
                                </div>
                            } buttonStyle={{borderRadius: 12, height: 50}} onClick={() => navigate("/finder/briefing/alert")}/>
                        </div>}
                </div>
            </div>
        </OverlayModal>
    );
};

export default TasksLearningModal;