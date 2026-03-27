import styles from "./TasksStatisticsSection.module.css";
import {CSSProperties, FC} from "react";

import {useLocation} from "wouter";

import {FinderTask, FinderTaskStatistics} from "../../../types/finder";
import {SubscriptionImpl} from "../../../types/subscription";
import {UserImpl} from "../../../types/user";
import {getDaysLeftEnding} from "../../../utils/text";
import Avatar from "../../common/Avatar/Avatar";
import WideButton from "../../common/Buttons/WideButton";

import Eagle from "../../../assets/icons/eagle.svg";
import MoveArrowIcon from "../../../assets/icons/move-arrow.svg";

interface TasksStatisticsSectionProps {
    user: UserImpl;
    tasks: FinderTask[];
    tasksStats: {[key: string]: FinderTaskStatistics};
    subscription: SubscriptionImpl;
}

export const TasksStatisticsSection: FC<TasksStatisticsSectionProps> = ({user, tasks, tasksStats, subscription}) => {
    const [, navigate] = useLocation();
    const isSubscriptionExpired = subscription.isSubscriptionExpired();

    const daysLeft = subscription.daysLeft();
    const isMoreThan3days = daysLeft > 3;
    const contentColor = isSubscriptionExpired ? "#F81B11" : isMoreThan3days ? "#7211F8" : "#F8E811";
    const backgroundColor = isSubscriptionExpired ? "#F81B114D" : isMoreThan3days ? "#7211F84D" : "#F8E8114D";

    return (
        <div className={styles.container} style={{"--bottom-padding": `${isSubscriptionExpired ? 40 : 12}px`} as CSSProperties}>
            <div className={styles.header}>
                <Avatar height="30px" width="30px" src={user!.avatar_url} />
                <div className={styles.usernameContainer}>
                    <span className={styles.username}>{`@${user.getUsername()}`}</span>
                </div>
                <div style={{flex: 1}} />
                <div className={styles.eagleContainer}>
                    <Eagle height="16px" width="16px" />
                </div>
            </div>

            <div className={styles.stats}>
                <div className={styles.block}>
                    <div className={styles.tariffSection} style={{"--border-color": contentColor, "--background-color": backgroundColor} as CSSProperties}>
                        <div className={styles.daysLeftHeader}>
                            <span className={styles.daysLeftHeaderText}>//Тариф истекает</span>
                            <Eagle height="16px" width="16px" color={contentColor} />
                        </div>
                        <div className={styles.daysLeftText} style={{"--color": contentColor} as CSSProperties}>
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
                            <span style={{"--task-color": task.active ? "#FFFFFF" : "#FFFFFF30"} as CSSProperties}>{task.title}</span>
                        </div>
                    ))}
                </div>
                <div className={styles.tasksMoveSection}>
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
