import styles from "./TaskLimitReachedModal.module.css";
import {FC} from "react";

import OverlayModal from "../../common/Alert/OverlayModal";
import WideButton from "../../common/Buttons/WideButton";

interface TaskLimitReachedModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const TaskLimitReachedModal: FC<TaskLimitReachedModalProps> = ({isOpen, onClose}) => {
    return (
        <OverlayModal isOpen={isOpen} onClose={onClose}>
            <div className={styles.wrapper}>
                <div className={styles.container}>
                    <div className={styles.backgroundLogo}>
                        <img src="/assets/finder/task-limit-background.svg" alt=" " />
                    </div>
                    <div className={styles.text}>
                        <div className={styles.title}>
                            <span>
                                <span className={styles.red}>//</span>
                                <span>Вы достигли лимита активных задач</span>
                            </span>
                        </div>
                        <div className={styles.description}>
                            В Cardinal можно вести одновременно до 5 профилей/специальностей.Чтобы добавить новую задачу - пожалуйста, удалите одну из активных.
                        </div>
                    </div>
                    <WideButton
                        color="#F81B1133"
                        textColor="#F81B11"
                        text="Закрыть"
                        buttonStyle={{border: "1px solid #F81B11", borderRadius: 19, minHeight: 43, maxHeight: 43, marginTop: 11}}
                        onClick={onClose}
                    />
                </div>
            </div>
        </OverlayModal>
    );
};

export default TaskLimitReachedModal;
