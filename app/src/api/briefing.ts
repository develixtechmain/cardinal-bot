import {QuestionAnswer} from "../types/finder";
import {Briefing} from "../types/finder/briefing";
import {authFetch} from "../utils/api";

export const fetchBriefing = async (userId: string): Promise<Briefing> => {
    const response = await authFetch("ai_core", "/onboarding/start", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({user_id: userId})
    });

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return res;
};

export const answerQuestions = async (briefingId: string, answer: QuestionAnswer[]): Promise<string[]> => {
    const response = await authFetch("ai_core", `/onboarding/${briefingId}/answer`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(answer)
    });

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return res;
};

export const completeBriefing = async (briefingId: string, totalAnswers: QuestionAnswer[]): Promise<{title: string; tags: string[]}> => {
    const response = await authFetch("ai_core", `/onboarding/${briefingId}/complete`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(totalAnswers)
    });

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return res;
};

export const createTask = async (cloudTask: {title: string; tags: string[]}) => {
    const response = await authFetch("backend", `/finder/tasks`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({cloudTask})
    });

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return res;
};
