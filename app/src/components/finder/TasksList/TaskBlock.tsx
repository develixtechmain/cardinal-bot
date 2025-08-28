import {FinderTask, FinderTaskStatistics} from "../../../types/finder";
import React, {useRef} from "react";

import styles from "./TaskBlock.module.css";
import WideButton from "../../common/Buttons/WideButton";
import {navigate} from "wouter/use-hash-location";

import ActionImg from "../../../assets/finder/action-task.svg";
import {deleteUserTask, patchUserTask} from "../../../api/finder";
import {useFinder} from "../../../store/finder";

interface TaskBlockProps {
    task: FinderTask;
    stats: FinderTaskStatistics;
}

const TaskBlock: React.FC<TaskBlockProps> = ({task, stats}) => {
    const isActiveChanging = useRef(false);
    const isDeleting = useRef(false);

    const updateTask = useFinder(s => s.updateTask)
    const removeTask = useFinder(s => s.removeTask)

    const handleChangeActive = async (task: FinderTask) => {
        if (isActiveChanging.current) return;
        isActiveChanging.current = true;

        try {
            updateTask(await patchUserTask({...task, active: !task.active}))
        } finally {
            isActiveChanging.current = false;
        }
    };

    const handleDelete = async (task: FinderTask) => {
        if (isDeleting.current) return;
        isDeleting.current = true;

        try {
            await deleteUserTask(task.id)
            removeTask(task.id)
        } finally {
            isDeleting.current = false;
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.title}>
                <div className={`${styles.dot} ${task.active ? styles.active : styles.disabled}`}/>
                <span color={task.active ? "white" : "#FFFFFF66"}>{task.title}</span>
            </div>
            <div className={styles.statsBlock}>
                <div className={styles.row}>
                    <div className={styles.statusBlock}>
                        Статус задачи
                    </div>
                    {task.active ?
                        <div className={styles.enabledBlock}>
                            <img height="10px" width="15px" src="/assets/finder/task/enabled.svg" alt=" "/>
                            РАБОТАЕТ
                        </div> :
                        <div className={styles.disabledBlock}>
                            <img height="14px" width="14px" src="/assets/finder/task/disabled.svg" alt=" "/>
                            ВЫКЛ
                        </div>
                    }
                </div>
                <div className={styles.row}>
                    <div className={`${styles.foundLeads} ${task.active ? "" : styles.grey}`}>
                        <span className={`${task.active ? styles.purple : styles.grey}`}>//</span>
                        <span>Найдено лидов</span>
                    </div>
                    <div className={styles.totalBlock} style={{
                        "--block-color": task.active ? "#7211F833" : "#2E2E2E33",
                        "--content-color": task.active ? "white" : "#FFFFFF70"
                    } as React.CSSProperties}>
                        {stats.total}
                    </div>
                    <div className={styles.dailyText}>
                        Новых за сутки
                    </div>
                    <div className={styles.dailyCount} style={{
                        "--content-color": task.active ? "#BEF811" : "#FFFFFF70",
                        "--block-color": task.active ? "#BEF81133" : "#2E2E2E33",
                        "--border-color": task.active ? "#BEF811" : "#2E2E2E"
                    } as React.CSSProperties}>
                        {stats.today === 0 ? "-" : stats.today}
                    </div>
                </div>
                <div className={styles.row}>
                    <div className={`${styles.productivity} ${task.active ? "" : styles.grey}`}>
                        <span>
                            <span className={`${task.active ? styles.purple : styles.grey}`}>//</span>
                            <span>Продуктивность</span>
                        </span>
                    </div>
                    <div className={styles.avgBlock} style={{
                        "--block-color": task.active ? "#7211F833" : "#2E2E2E33",
                        "--border-color": task.active ? "#7211F8" : "#2E2E2E"
                    } as React.CSSProperties}>
                        <span>
                            <span className={styles.avgCount}>~ {stats.avg} </span>
                            <span className={styles.avgText}>лид/день</span>
                        </span>
                    </div>
                </div>
            </div>


            <div className={styles.buttons}>
                <div className={styles.playPauseButton} onClick={() => handleChangeActive(task)} style={{
                    "--content-color": task.active ? "#888888" : "#BEF811",
                    "--block-color": task.active ? "#A1A1A133" : "#BEF81133",
                    "--border-color": task.active ? "#FFFFFF66" : "#BEF811"
                } as React.CSSProperties}>
                    <img height="26px" width="26px" src={`/assets/finder/task/${task.active ? "pause" : "play"}.svg`} alt=" "/>
                    {task.active ? "Пауза" : "Запуск"}
                    <ActionImg height="7px" width="8px" color={task.active ? "#FFFFFF66" : "#BEF811"}/>
                </div>
                <div className={styles.editButton} onClick={() => navigate("https://google.com")}>
                    <img height="24px" width="20px" src={`/assets/finder/task/edit.svg`} alt=" "/>
                    Дообучить
                    <ActionImg height="7px" width="8px" color="#7211F8"/>
                </div>
                <div className={styles.deleteButton} onClick={() => handleDelete(task)}>
                    <img height="24px" width="22px" src="/assets/finder/task/delete.svg" alt="DEL"/>
                </div>
            </div>


            <WideButton color="#7211F8" text={
                <div className={styles.moveButton}>
                    <img height="15px" width="17px" src="/assets/finder/task/forward.svg" alt=" "/>
                    <span style={{color: "white"}}>Перейти к лидам</span>
                </div>
            } buttonStyle={{borderRadius: 14, height: 50}} onClick={() => navigate("https://google.com")}/>
        </div>
    )
}

export default TaskBlock;