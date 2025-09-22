export type User = {
    id: string;
    user_id: number;
    first_name: string;
    last_name: string;
    username: string;
    avatar_url: string;
    referrer_id: string;
    balance: number;
    created_at: string;

    tg: WebAppUser;
};

export type Subscription = {
    id: string;

    trial_starts_at: Date | undefined;
    trial_ends_at: Date | undefined;

    subscription_ends_at: Date | undefined;

    daysLeft(): number;
    isTrialUsed(): boolean;
    isSubscriptionExpired(): boolean;
    isActive(): boolean;
};

export type Benefit = {
    title: {icon: {height: number; width: number}; text: PartialText};
    text: PartialText[];
    button: {height: number; width: number; label: string};
};

export interface PartialText {
    id: string;
    textParts: TextPart[];
    extraPadding?: number;
}

export interface TextPart {
    text: string;
    bold?: boolean;
    styles?: RC.CSSProperties;
}
