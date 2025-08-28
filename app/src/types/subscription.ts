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
        const now = new Date();

        if (this.subscription_ends_at) {
            const diffMs = this.subscription_ends_at.getTime() - now.getTime();
            return diffMs > 0 ? Math.ceil(diffMs / (1000 * 60 * 60 * 24)) : 0;
        }

        if (this.trial_starts_at && this.trial_ends_at) {
            const diffMs = this.trial_ends_at.getTime() - now.getTime();
            return diffMs > 0 ? Math.ceil(diffMs / (1000 * 60 * 60 * 24)) : 0;
        }

        return 0;
    }

    isTrialUsed(): boolean {
        return !!(this.trial_starts_at || this.trial_ends_at || this.subscription_ends_at);
    }

    isSubscriptionExpired(): boolean {
        return !this.isActive()
    }

    isActive(): boolean {
        const now = new Date();

        if (this.subscription_ends_at && this.subscription_ends_at.getTime() >= now.getTime()) {
            return true;
        }

        if (this.trial_starts_at && this.trial_ends_at) {
            return this.trial_ends_at.getTime() > now.getTime();
        }

        return false;
    }
}