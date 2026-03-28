import {create} from "zustand";

import {Answer, FinderTask, FinderTaskStatistics, QuestionAnswer} from "../types/finder";

type FinderStore = {
    tasks: FinderTask[];
    setTasks: (tasks: FinderTask[]) => void;
    tasksStats: {[key: string]: FinderTaskStatistics} | undefined;
    setTasksStats: (tasks: {[key: string]: FinderTaskStatistics}) => void;
    updateTask: (task: FinderTask) => void;
    removeTask: (taskId: string) => void;
};

type BriefingStore = {
    id: string | undefined;
    setId: (id: string) => void;
    answers: Answer[] | undefined;
    setAnswers: (answers: Answer[]) => void;
    additionalQuestions: QuestionAnswer[] | undefined;
    setAdditionalQuestions: (additionalQuestions: QuestionAnswer[]) => void;
    reset: () => void;
};

export const useFinder = create<FinderStore>((set) => ({
    tasks: [],
    setTasks: (tasks: FinderTask[]) => set({tasks}),
    tasksStats: undefined,
    setTasksStats: (tasksStats: {[key: string]: FinderTaskStatistics}) => set({tasksStats}),
    updateTask: (task: FinderTask) => {
        set((state) => {
            let updatedTasks = [...state.tasks];
            const taskIndex = updatedTasks.findIndex((t) => t.id === task.id);
            if (taskIndex !== -1) {
                updatedTasks[taskIndex] = task;
            }

            return {tasks: updatedTasks};
        });
    },

    removeTask: (taskId: string) => {
        set((state) => {
            let updatedTasks = state.tasks.filter((t) => t.id !== taskId);
            let updatedTasksStats = {...state.tasksStats};
            delete updatedTasksStats[taskId];
            return {tasks: updatedTasks, tasksStats: updatedTasksStats};
        });
    }
}));

export const useBriefingStore = create<BriefingStore>((set) => ({
    id: undefined,
    setId: (id: string) => set({id}),
    answers: undefined,
    setAnswers: (answers) => set({answers}),
    additionalQuestions: undefined,
    setAdditionalQuestions: (additionalQuestions) => set({additionalQuestions}),
    reset: () => set({id: undefined, answers: undefined, additionalQuestions: undefined})
}));
