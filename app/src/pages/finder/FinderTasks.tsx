import styles from "./FinderTasks.module.css";
import {useEffect, useRef, useState} from "react";

import {useLocation} from "wouter";

import {fetchUserTasks, fetchUserTasksStats} from "../../api/finder";
import WideButton from "../../components/common/Buttons/WideButton";
import Header from "../../components/common/Header/Header";
import {Loading} from "../../components/common/Loading/Loading";
import TaskBlock from "../../components/finder/TasksList/TaskBlock";
import {useFinder} from "../../store/finder";

import MoveArrowIcon from "../../assets/icons/move-arrow.svg";

export default function Finder() {
    const [, navigate] = useLocation();

    const isTasksLoading = useRef(false);
    const tasks = useFinder((s) => s.tasks);
    const setTasks = useFinder((s) => s.setTasks);

    const isTasksStatisticsLoading = useRef(false);
    const tasksStats = useFinder((s) => s.tasksStats);
    const setTasksStats = useFinder((s) => s.setTasksStats);

    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (tasksStats && Object.keys(tasksStats).length == tasks.length) {
            setLoading(false);
        }
    }, [tasks, tasksStats]);

    useEffect(() => {
        const tryFetchTasks = async () => {
            try {
                const tasks = await fetchUserTasks();
                setTasks(tasks);
            } catch (e: unknown) {
                const error = e as Error;
                console.error(`Failed to fetch user tasks stats: ${error.message}. Retrying...`);
                await new Promise((resolve) => setTimeout(resolve, 3000));
                await tryFetchTasks();
            }
        };

        const run = async () => {
            if (isTasksLoading.current) return;
            isTasksLoading.current = true;

            try {
                await tryFetchTasks();
            } catch (e: unknown) {
                const error = e as Error;
                console.error(`Failed to fetch user tasks: ${error.message}`);
            } finally {
                isTasksLoading.current = false;
            }
        };
        void run();
    }, [tasks]);

    useEffect(() => {
        const tryFetchTasksStats = async () => {
            try {
                const tasksStats = await fetchUserTasksStats();
                setTasksStats(tasksStats);
            } catch (e: unknown) {
                const error = e as Error;
                console.error(`Failed to fetch user tasks stats: ${error.message}. Retrying...`);
                await new Promise((resolve) => setTimeout(resolve, 3000));
                await tryFetchTasksStats();
            }
        };

        const run = async () => {
            if (isTasksStatisticsLoading.current) return;
            isTasksStatisticsLoading.current = true;

            try {
                await tryFetchTasksStats();
            } catch (e: unknown) {
                const error = e as Error;
                console.error(`Failed to fetch user subscription: ${error.message}`);
            } finally {
                isTasksStatisticsLoading.current = false;
            }
        };
        void run();
    }, [tasksStats]);

    if (loading) {
        return <Loading />;
    }

    return (
        <div className={styles.container}>
            <Header backTo="/finder" />
            <div className={styles.block}>
                <div className={styles.header}>
                    <div className={styles.headerText}>
                        <span>Список заданий </span>
                        <span className={styles.purple}>{">"}</span>
                    </div>
                    <img height="22px" width="24px" src="/assets/finder/exit-marked.svg" alt=" " />
                </div>
                <div className={styles.tasksList}>
                    <div style={{display: "flex", flexDirection: "column", gap: 10}}>
                        {tasks.map((task, index) => {
                            let stats = tasksStats![task.id];
                            if (!stats) stats = {avg: 0, total: 0, today: 0};
                            return <TaskBlock key={index} task={task} stats={stats} />;
                        })}
                    </div>
                </div>

                <WideButton
                    color="#2E2E2E"
                    text={
                        <div className={styles.moveButton}>
                            <MoveArrowIcon color="white" />
                            <span style={{color: "white"}}>Добавить новое задание</span>
                        </div>
                    }
                    buttonStyle={{borderRadius: 19, height: 50}}
                    onClick={tasks.length >= 5 ? undefined : () => navigate("/finder/briefing/alert")}
                />
            </div>
        </div>
    );
}
