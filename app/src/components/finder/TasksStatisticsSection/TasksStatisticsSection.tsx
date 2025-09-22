import styles from "./TasksStatisticsSection.module.css";
import {FC} from "react";

import {useLocation} from "wouter";

import {Subscription, User} from "../../../types";
import {FinderTask, FinderTaskStatistics} from "../../../types/finder";
import {getDaysLeftEnding} from "../../../utils/text";
import WideButton from "../../common/Buttons/WideButton";

import Eagle from "../../../assets/icons/eagle.svg";
import Info from "../../../assets/icons/info.svg";
import MoveArrowIcon from "../../../assets/icons/move-arrow.svg";

interface TasksStatisticsSectionProps {
    user: User;
    tasks: FinderTask[];
    tasksStats: {[key: string]: FinderTaskStatistics};
    subscription: Subscription;
}

export const TasksStatisticsSection: FC<TasksStatisticsSectionProps> = ({user, tasks, tasksStats, subscription}) => {
    const [, navigate] = useLocation();
    const isSubscriptionExpired = subscription.isSubscriptionExpired();

    const daysLeft = subscription.daysLeft();
    const isMoreThan3days = daysLeft > 3;
    const goodColor = isMoreThan3days ? "#7211F8" : "#F8E811";

    return (
        <div className={styles.container} style={{"--bottom-padding": `${isSubscriptionExpired ? 40 : 12}px`} as React.CSSProperties}>
            <div className={styles.header}>
                <img height="30px" width="30px" src={user.avatar_url} alt=" " />
                <div className={styles.usernameContainer}>
                    <span className={styles.username}>{`@${user.username}`}</span>
                </div>
                <div style={{flex: 1}} />
                <div className={styles.eagleContainer}>
                    <Eagle height="16px" width="16px" />
                </div>
            </div>

            <div className={styles.stats}>
                <div className={styles.block}>
                    <div
                        className={styles.tariffSection}
                        style={{"--border-color": goodColor, "--background-color": isMoreThan3days ? "#7211F84D" : "#F8E8114D"} as React.CSSProperties}
                    >
                        <div className={styles.daysLeftHeader}>
                            <span className={styles.daysLeftHeaderText}>//Тариф истекает</span>
                            <Eagle height="16px" width="16px" color={goodColor} />
                        </div>
                        <div className={styles.daysLeftText} style={{"--color": goodColor} as React.CSSProperties}>
                            <span>{daysLeft}</span>
                            <div className={styles.daysLeftSubtext}>/{getDaysLeftEnding(daysLeft)}</div>
                        </div>
                    </div>
                </div>

                <div className={styles.block}>
                    <div className={styles.statsSection}>
                        <div className={styles.leadsCountSection}>
                            <span className={styles.leadsCountTitle}>//Получено лидов</span>
                            <span className={styles.leadsCount}>{Object.values(tasksStats).reduce((sum, stats) => sum + stats.total, 0)}</span>
                        </div>
                        <div style={{flex: 1}} />
                        <img height="39px" width="28px" src="/assets/finder/leads-stats.svg" alt=" " />
                    </div>
                </div>
            </div>

            <div className={styles.tasksSection} onClick={() => navigate("/finder/tasks")}>
                <div className={styles.tasksListSection}>
                    <div className={styles.tasksListSectionTitle}>
                        <span>Список заданий </span>
                        <span className={styles.purple}>{">"}</span>
                    </div>
                    {tasks.slice(0, 2).map((task, index) => (
                        <div key={index} className={styles.taskBlock}>
                            <div className={`${styles.dot} ${task.active ? styles.active : styles.disabled}`} />
                            <span style={{"--task-color": task.active ? "white" : "#FFFFFF30"} as React.CSSProperties}>{task.title}</span>
                        </div>
                    ))}
                </div>
                <div className={styles.tasksMoveSection}>
                    <Info height="17px" width="17px" color="#7211F8" />
                    <div style={{flex: 1}} />
                    <WideButton
                        color="#7211F8"
                        text={
                            <div className={styles.moveButton}>
                                <MoveArrowIcon color="#F2F2F2" />
                                <span style={{color: "#F2F2F2"}}>Перейти в список</span>
                            </div>
                        }
                        buttonStyle={{borderRadius: 11, height: 54, maxWidth: "100%"}}
                    />
                </div>
            </div>
        </div>
    );
};
