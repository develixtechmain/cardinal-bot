import {authFetch} from "../utils/api";
import {Subscription, User} from "../types";
import {SubscriptionImpl} from "../types/subscription";
import {Bank} from "../utils/consts";

export const fetchUser = async (): Promise<User> => {
    const response = await authFetch("backend", "/users/me");

    if (!response.ok) {
        throw new Error("Failed to fetch user");
    }

    return await response.json();
}

export const patchUser = async (user: User): Promise<User> => {
    const response = await authFetch("backend", "/users/me", {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({username: user.tg.username, avatar_url: user.tg.photo_url}),
    });

    if (!response.ok) {
        throw new Error("Failed to patch user");
    }

    return await response.json();
}

export const fetchSubscription = async (): Promise<Subscription> => {
    const response = await authFetch("backend", "/subscriptions/me");

    if (!response.ok) {
        throw new Error("Failed to fetch subscription");
    }

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return new SubscriptionImpl({
        ...res,
        trial_starts_at: parseDate(res.trial_starts_at),
        trial_ends_at: parseDate(res.trial_ends_at),
        subscription_ends_at: parseDate(res.subscription_ends_at),
    });
}

export const startSubscriptionTrial = async (subId: string): Promise<Subscription> => {
    const response = await authFetch("backend", `/subscriptions/${subId}/trial`, {
        method: 'POST',
    });


    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return new SubscriptionImpl({
        ...res,
        trial_starts_at: parseDate(res.trial_starts_at),
        trial_ends_at: parseDate(res.trial_ends_at),
        subscription_ends_at: parseDate(res.subscription_ends_at),
    });
};


export const fetchPurchaseLink = async (months: number, bank: Bank, email: string): Promise<string> => {
    const response = await authFetch("backend", `/subscriptions/purchase`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            months: months,
            email: email,
            payment_system: bank === "ru" ? "lava" : "alpha",
        })
    });


    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return res.url;
}


export const purchaseFromBalance = async (): Promise<Subscription> => {
    const response = await authFetch("backend", `/subscriptions/purchase/balance`, {
        method: 'POST'
    });


    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown error");
    }

    return new SubscriptionImpl({
        ...res,
        trial_starts_at: parseDate(res.trial_starts_at),
        trial_ends_at: parseDate(res.trial_ends_at),
        subscription_ends_at: parseDate(res.subscription_ends_at),
    });
}


function parseDate(dateString: string | null): Date | undefined {
    if (dateString === null) return undefined;
    const parsedDate = new Date(dateString);
    return isNaN(parsedDate.getTime()) ? undefined : parsedDate;
}