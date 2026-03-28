import {Subscription} from "./index";

export class SubscriptionImpl implements Subscription {
    id: string;
    trial_starts_at: Date | undefined;
    trial_ends_at: Date | undefined;
    subscription_ends_at: Date | undefined;

    constructor(subscription: Subscription) {
        this.id = subscription.id;
        this.trial_starts_at = subscription.trial_starts_at;
        this.trial_ends_at = subscription.trial_ends_at;
        this.subscription_ends_at = subscription.subscription_ends_at;
    }

    daysLeft(): number {
        const endDate = this.subscription_ends_at ?? (this.trial_starts_at && this.trial_ends_at ? this.trial_ends_at : null);
        if (!endDate) return 0;

        const now = new Date();
        const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());

        const end = Date.UTC(endDate.getUTCFullYear(), endDate.getUTCMonth(), endDate.getUTCDate());

        const diffDays = (end - today) / (1000 * 60 * 60 * 24);
        return diffDays > 0 ? diffDays : 0;
    }

    isTrialUsed(): boolean {
        return !!(this.trial_starts_at || this.trial_ends_at || this.subscription_ends_at);
    }

    isSubscriptionExpired(): boolean {
        return !this.isActive();
    }

    isActive(withTrial: boolean = true): boolean {
        const now = new Date();

        if (this.subscription_ends_at && this.subscription_ends_at.getTime() >= now.getTime()) {
            return true;
        }

        if (withTrial && this.trial_starts_at && this.trial_ends_at) {
            return this.trial_ends_at.getTime() > now.getTime();
        }

        return false;
    }
}
