import {authFetch} from "../utils/api";
import {FinderTask, FinderTaskStatistics} from "../types/finder";

export const fetchUserTasks = async (): Promise<FinderTask[]> => {
    const response = await authFetch("backend", "/finder/tasks/me");

    if (!response.ok) {
        throw new Error("Failed to fetch user tasks");
    }

    return await response.json();
}

export const fetchUserTasksStats = async (): Promise<{ [key: string]: FinderTaskStatistics }> => {
    const response = await authFetch("backend", "/finder/tasks/stats");

    if (!response.ok) {
        throw new Error("Failed to fetch user tasks statistics");
    }

    return await response.json();
}


export const patchUserTask = async (task: FinderTask) => {
    const response = await authFetch("backend", `/finder/tasks/${task.id}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(task)
    });

    if (!response.ok) {
        throw new Error("Failed to patch user task");
    }

    return await response.json();
}

export const deleteUserTask = async (taskId: string) => {
    const response = await authFetch("backend", `/finder/tasks/${taskId}`, {
        method: 'DELETE'
    });

    if (!response.ok) {
        throw new Error("Failed to delete user task");
    }
}