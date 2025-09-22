import styles from "./Finder.module.css";
import {useEffect, useRef, useState} from "react";

import {useLocation} from "wouter";

import {fetchUserTasks, fetchUserTasksStats} from "../../api/finder";
import ActionButtons from "../../components/ActionButtons/ActionButtons";
import ClubSection from "../../components/ClubSection/ClubSection";
import ToolsSection from "../../components/ToolsSection/ToolsSection";
import BottomSection from "../../components/common/BottomSection/BottomSection";
import WideButton from "../../components/common/Buttons/WideButton";
import Delimiter from "../../components/common/Delimiter/Delimiter";
import Header from "../../components/common/Header/Header";
import {Loading} from "../../components/common/Loading/Loading";
import ToolSelectionModal from "../../components/common/ToolSelection/ToolSelectionModal";
import ToolSelector from "../../components/common/ToolSelection/ToolSelector";
import AboutContactCatcherModal from "../../components/contact-catcher/AboutModal/AboutContactCatcherModal";
import CircleStatus from "../../components/finder/CircleStatus/CircleStatus";
import TasksLearningModal from "../../components/finder/TasksLearningModal/TasksLearningModal";
import {TasksLearningSection} from "../../components/finder/TasksLearningSection/TasksLearningSection";
import {TasksStatisticsSection} from "../../components/finder/TasksStatisticsSection/TasksStatisticsSection";
import {useFinder} from "../../store/finder";
import {useStore} from "../../store/store";
import {actionButtons, tools} from "../../utils/consts";

import MoveArrowIcon from "../../assets/icons/move-arrow.svg";

export default function Finder() {
    const [location, navigate] = useLocation();
    const [loading, setLoading] = useState(true);
    const isTasksLoading = useRef(false);
    const isTasksStatisticsLoading = useRef(false);

    const user = useStore((s) => s.user);
    const subscription = useStore((s) => s.subscription);

    const tasks = useFinder((s) => s.tasks);
    const setTasks = useFinder((s) => s.setTasks);

    const tasksStats = useFinder((s) => s.tasksStats);
    const setTasksStats = useFinder((s) => s.setTasksStats);

    const [isToolSelectionOpen, setIsToolSelectionOpen] = useState(false);
    const [isAboutCatcherOpen, setIsAboutContactCatcherOpen] = useState(false);
    const [isTasksLearningModalOpen, setIsTasksLearningModalOpen] = useState(false);

    useEffect(() => {
        if (tasks.length >= 0 && tasksStats) {
            setLoading(false);
        }
    }, [tasks, tasksStats]);

    useEffect(() => {
        const run = async () => {
            if (isTasksLoading.current) return;
            isTasksLoading.current = true;

            const tasks = await fetchUserTasks();

            if (tasks.length < 1) {
                navigate("/finder/briefing");
            } else {
                setTasks(tasks);
            }
        };
        void run();
    }, [tasks]);

    useEffect(() => {
        const run = async () => {
            if (isTasksStatisticsLoading.current) return;
            isTasksStatisticsLoading.current = true;

            const tasksStats = await fetchUserTasksStats();
            setTasksStats(tasksStats);
        };
        void run();
    }, [tasksStats]);

    if (loading) {
        return <Loading />;
    }

    return (
        <div className={styles.container}>
            <AboutContactCatcherModal isOpen={isAboutCatcherOpen} onClose={() => setIsAboutContactCatcherOpen(false)} />
            <Header />
            <ToolSelector tool={tools.finder} onClick={() => setIsToolSelectionOpen(true)} />
            <ToolSelectionModal toolId={tools.finder.id} isOpen={isToolSelectionOpen} onClose={() => setIsToolSelectionOpen(false)} />

            <div className={styles.leadsTitle}>
                <span>Получено </span>
                <span className={styles.purple}>лидов</span>
                <span> сегодня</span>
            </div>

            <CircleStatus activeCount={subscription?.isActive() ? Object.values(tasksStats!).reduce((sum, stats) => sum + stats.today, 0) : 0} />

            {/*TODO URL to channel*/}
            <WideButton
                color="#7211F833"
                text={
                    <div className={styles.moveButton}>
                        <MoveArrowIcon color="#7211F8" />
                        <span style={{color: "#7211F8"}}>Перейти в канал</span>
                    </div>
                }
                buttonStyle={{borderRadius: 12, height: 54, maxWidth: "70%", margin: "0 auto"}}
                onClick={() => navigate("https://google.com")}
            />

            <TasksStatisticsSection user={user!} tasks={tasks} tasksStats={tasksStats!} subscription={subscription!} />

            <ActionButtons
                buttons={actionButtons}
                isSubscriptionExpired={subscription!.isSubscriptionExpired()}
                isMoreThan3days={subscription!.daysLeft() > 3}
            />
            <TasksLearningSection
                openLearning={() => setIsTasksLearningModalOpen(true)}
                isActive={subscription!.isActive()}
                newTaskAvailable={tasks.length < 5}
            />
            <TasksLearningModal tasks={tasks} isOpen={isTasksLearningModalOpen} onClose={() => setIsTasksLearningModalOpen(false)} />

            <Delimiter />
            <ToolsSection
                tools={Object.values(tools).filter((it) => it.id !== "finder")}
                showTitle={false}
                showModal={{"contact-catcher": () => setIsAboutContactCatcherOpen(true)}}
            />

            <ClubSection />
            <Delimiter />
            <BottomSection />
        </div>
    );
}
