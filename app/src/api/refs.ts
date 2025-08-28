import {RefUser} from "../types/referral";
import {authFetch} from "../utils/api";

export const fetchRefs = async (): Promise<RefUser[]> => {
    const response = await authFetch("backend", "/refs/me");

    if (!response.ok) {
        throw new Error("Failed to fetch user refs");
    }

    return await response.json();
}