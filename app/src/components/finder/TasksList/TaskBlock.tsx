import styles from "./TaskBlock.module.css";
import {CSSProperties, ChangeEvent, FC, useRef, useState} from "react";

import {navigate} from "wouter/use-hash-location";

import {deleteUserTask, patchUserTask} from "../../../api/finder";
import {useFinder} from "../../../store/finder";
import {FinderTask, FinderTaskStatistics} from "../../../types/finder";
import {openLink} from "../../../utils/common";
import OverlayModal from "../../common/Alert/OverlayModal";
import WideButton from "../../common/Buttons/WideButton";

import ActionImg from "../../../assets/finder/action-task.svg";

interface TaskBlockProps {
    task: FinderTask;
    stats: FinderTaskStatistics;
}

const TaskBlock: FC<TaskBlockProps> = ({task, stats}) => {
    const [showRename, setShowRename] = useState(false);
    const [showDelete, setShowDelete] = useState(false);
    const isRenaming = useRef(false);
    const isActiveChanging = useRef(false);
    const isDeleting = useRef(false);

    const updateTask = useFinder((s) => s.updateTask);
    const removeTask = useFinder((s) => s.removeTask);

    const [titleText, setTitleText] = useState("");
    const [titleError, setTitleError] = useState("");

    const handleRename = async () => {
        if (isRenaming.current) return;
        isRenaming.current = true;

        try {
            updateTask(await patchUserTask({...task, title: titleText}));
            setShowRename(false);
        } finally {
            isRenaming.current = false;
        }
    };

    const handleTitleChange = (event: ChangeEvent<HTMLInputElement>) => {
        changeTitle(event.target.value);
    };

    const changeTitle = (title: string) => {
        if (title.trim() === "") {
            setTitleError("Введите название задачи");
        } else {
            setTitleError("");
        }
        setTitleText(title);
    };

    const handleChangeActive = async () => {
        if (isActiveChanging.current) return;
        isActiveChanging.current = true;

        try {
            updateTask(await patchUserTask({...task, active: !task.active}));
        } finally {
            isActiveChanging.current = false;
        }
    };

    const handleDelete = async () => {
        if (isDeleting.current) return;
        isDeleting.current = true;

        try {
            await deleteUserTask(task.id);
            setShowDelete(false);
            removeTask(task.id);
        } finally {
            isDeleting.current = false;
        }
    };

    return (
        <div className={styles.container}>
            <OverlayModal isOpen={showRename} onClose={() => setShowRename(false)}>
                <div className={styles.renameContainer}>
                    <div className={styles.renameBlock}>
                        <div className={styles.renameTitle}>
                            <img height="15px" width="15px" style={{flexShrink: 0}} src="/assets/finder/task/rename.svg" alt=" " />
                            <span>Переименовать задачу</span>
                        </div>
                        <input
                            type="text"
                            id="task_title"
                            value={titleText}
                            onChange={handleTitleChange}
                            autoComplete={"off"}
                            placeholder={titleError || "Название задачи"}
                            className={`${styles.titleInput} ${titleError ? styles.titleInputError : ""}`}
                        />
                    </div>
                    <div className={styles.actionButtons}>
                        <button className={`${styles.cancelButton} ${styles.buttonText}`} onClick={() => setShowRename(false)}>
                            Отмена
                        </button>
                        <button className={`${styles.confirmRenameButton} ${styles.buttonText}`} onClick={handleRename}>
                            Переименовать
                        </button>
                    </div>
                </div>
            </OverlayModal>
            <OverlayModal isOpen={showDelete} onClose={() => setShowDelete(false)}>
                <div className={styles.deleteContainer}>
                    <div className={styles.deleteName}>
                        <div className={`${styles.dot} ${styles.active}`} />
                        <span>{task.title}</span>
                    </div>
                    <div className={styles.deleteText}>
                        <span className={styles.deleteTitle}>Вы действительно хотите удалить задачу?</span>
                        <span className={styles.deleteDescription}>Это действие нельзя будет отменить</span>
                    </div>
                    <div className={styles.actionButtons}>
                        <button className={`${styles.cancelButton} ${styles.buttonText}`} onClick={() => setShowDelete(false)}>
                            Отмена
                        </button>
                        <button className={`${styles.confirmDeleteButton} ${styles.buttonText}`} onClick={handleDelete}>
                            Да, удалить
                        </button>
                    </div>
                </div>
            </OverlayModal>
            <div className={styles.titleRow}>
                <div className={styles.title}>
                    <div className={`${styles.dot} ${task.active ? styles.active : styles.disabled}`} />
                    <span color={task.active ? "#FFFFFF" : "#FFFFFF66"}>{task.title}</span>
                </div>
                <div
                    className={styles.renameButton}
                    onClick={() => {
                        changeTitle(task.title);
                        setShowRename(true);
                    }}
                >
                    <img height="10px" width="11px" src="/assets/finder/task/rename.svg" alt=" " />
                    <span>Переименовать задачу</span>
                </div>
            </div>
            <div className={styles.statsBlock}>
                <div className={styles.row}>
                    <div className={styles.statusBlock}>Статус задачи</div>
                    {task.active ? (
                        <div className={styles.enabledBlock}>
                            <img height="10px" width="15px" src="/assets/finder/task/enabled.svg" alt=" " />
                            РАБОТАЕТ
                        </div>
                    ) : (
                        <div className={styles.disabledBlock}>
                            <img height="14px" width="14px" src="/assets/finder/task/disabled.svg" alt=" " />
                            ВЫКЛ
                        </div>
                    )}
                </div>
                <div className={styles.row}>
                    <div className={`${styles.foundLeads} ${task.active ? "" : styles.grey}`}>
                        <span className={`${task.active ? styles.purple : styles.grey}`}>//</span>
                        <span>Найдено лидов</span>
                    </div>
                    <div
                        className={styles.totalBlock}
                        style={
                            {"--block-color": task.active ? "#7211F8" : "#2E2E2E", "--content-color": task.active ? "#FFFFFF" : "#FFFFFF70"} as CSSProperties
                        }
                    >
                        {stats.total}
                    </div>
                    <div className={styles.dailyText}>Новых за сутки</div>
                    <div
                        className={styles.dailyCount}
                        style={
                            {
                                "--content-color": task.active ? "#BEF811" : "#FFFFFF70",
                                "--block-color": task.active ? "#BEF81133" : "#2E2E2E33",
                                "--border-color": task.active ? "#BEF811" : "#2E2E2E"
                            } as CSSProperties
                        }
                    >
                        {stats.today === 0 ? "-" : stats.today}
                    </div>
                    <div />
                </div>
                <div className={styles.row}>
                    <div className={`${styles.productivity} ${task.active ? "" : styles.grey}`}>
                        <span>
                            <span className={`${task.active ? styles.purple : styles.grey}`}>//</span>
                            <span>Продуктивность</span>
                        </span>
                    </div>
                    <div
                        className={styles.avgBlock}
                        style={
                            {"--block-color": task.active ? "#7211F833" : "#2E2E2E33", "--border-color": task.active ? "#7211F8" : "#2E2E2E"} as CSSProperties
                        }
                    >
                        <span>
                            <span className={styles.avgCount}>~ {stats.avg} </span>
                            <span className={styles.avgText}>лид/день</span>
                        </span>
                    </div>
                </div>
            </div>

            <div className={styles.buttons}>
                <div
                    className={styles.playPauseButton}
                    onClick={handleChangeActive}
                    style={
                        {
                            "--content-color": task.active ? "#888888" : "#BEF811",
                            "--block-color": task.active ? "#A1A1A133" : "#BEF81133",
                            "--border-color": task.active ? "#FFFFFF66" : "#BEF811"
                        } as CSSProperties
                    }
                >
                    <img height="26px" width="26px" src={`/assets/finder/task/${task.active ? "pause" : "play"}.svg`} alt=" " />
                    {task.active ? "Пауза" : "Запуск"}
                    <ActionImg height="7px" width="8px" color={task.active ? "#FFFFFF66" : "#BEF811"} />
                </div>
                {/*TODO URL learn*/}
                <div className={styles.editButton} onClick={() => navigate("https://google.com")}>
                    <img height="24px" width="20px" src={`/assets/finder/task/edit.svg`} alt=" " />
                    Дообучить
                    <ActionImg height="7px" width="8px" color="#7211F8" />
                </div>
                <div className={styles.deleteButton} onClick={() => setShowDelete(true)}>
                    <img height="24px" width="22px" src="/assets/finder/task/delete.svg" alt="DEL" />
                </div>
            </div>

            <WideButton
                color="#7211F8"
                text={
                    <div className={styles.moveButton}>
                        <img height="15px" width="17px" src="/assets/finder/task/forward.svg" alt=" " />
                        <span style={{color: "#FFFFFF"}}>Перейти к лидам</span>
                    </div>
                }
                buttonStyle={{borderRadius: 14, height: 50}}
                onClick={() => openLink("https://t.me/cardinal_leadfinder_bot")}
            />
        </div>
    );
};

export default TaskBlock;
