import {Subscription, User} from "../types";
import {authFetch} from "../utils/api";
import {Bank} from "../utils/consts";

export const fetchUser = async (): Promise<User> => {
    const response = await authFetch("backend", "/users/me");

    if (!response.ok) {
        throw new Error("Failed to fetch user");
    }

    return await response.json();
};

export const patchUser = async (user: User): Promise<User> => {
    const response = await authFetch("backend", "/users/me", {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username: user.tg.username, avatar_url: user.tg.photo_url})
    });

    if (!response.ok) {
        throw new Error("Failed to patch user");
    }

    return await response.json();
};

export const fetchSubscription = async (): Promise<Subscription> => {
    const response = await authFetch("backend", "/subscriptions/me");

    if (!response.ok) {
        throw new Error("Failed to fetch subscription");
    }

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return {
        ...res,
        trial_starts_at: parseDate(res.trial_starts_at),
        trial_ends_at: parseDate(res.trial_ends_at),
        subscription_ends_at: parseDate(res.subscription_ends_at)
    };
};

export const startSubscriptionTrial = async (subId: string): Promise<Subscription> => {
    const response = await authFetch("backend", `/subscriptions/${subId}/trial`, {method: "POST"});

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return {
        ...res,
        trial_starts_at: parseDate(res.trial_starts_at),
        trial_ends_at: parseDate(res.trial_ends_at),
        subscription_ends_at: parseDate(res.subscription_ends_at)
    };
};

export const fetchPurchase = async (months: number, bank: Bank, email: string): Promise<{id: string; url: string}> => {
    const response = await authFetch("backend", `/subscriptions/purchase`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({months: months, email: email.toLowerCase(), payment_system: bank === "ru" ? "robokassa" : "lava"})
    });

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return res;
};

export const checkPurchase = async (trxId: string): Promise<Subscription | string> => {
    const response = await authFetch("backend", `/subscriptions/purchase/${trxId}`);

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    if (res.status) {
        return res.status;
    } else {
        return {
            ...res,
            trial_starts_at: parseDate(res.trial_starts_at),
            trial_ends_at: parseDate(res.trial_ends_at),
            subscription_ends_at: parseDate(res.subscription_ends_at)
        };
    }
};

export const purchaseFromBalance = async (): Promise<Subscription> => {
    const response = await authFetch("backend", `/subscriptions/purchase/balance`, {method: "POST"});

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return {
        ...res,
        trial_starts_at: parseDate(res.trial_starts_at),
        trial_ends_at: parseDate(res.trial_ends_at),
        subscription_ends_at: parseDate(res.subscription_ends_at)
    };
};

export const fetchRecurrency = async (): Promise<boolean> => {
    const response = await authFetch("backend", `/subscriptions/recurrency`);

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return true;
    return res && res.length > 0;
};

export const deleteRecurrency = async () => {
    const response = await authFetch("backend", `/subscriptions/recurrency`, {method: "DELETE"});

    if (!response.ok) {
        throw new Error("Failed to disable recurrency");
    }
};

function parseDate(dateString: string | null): Date | undefined {
    if (dateString === null) return undefined;
    const parsedDate = new Date(dateString);
    return isNaN(parsedDate.getTime()) ? undefined : parsedDate;
}
