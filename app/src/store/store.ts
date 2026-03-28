import {create} from "zustand";

import {Subscription, User} from "../types";
import {SubscriptionImpl} from "../types/subscription";
import {UserImpl} from "../types/user";

type Store = {
    user: UserImpl | undefined;
    setUser: (user: User) => void;

    subscription: SubscriptionImpl | undefined;
    setSubscription: (subscription: Subscription) => void;
};

export const useStore = create<Store>((set) => ({
    user: undefined,
    setUser: (user: User) => set({user: new UserImpl(user)}),

    subscription: undefined,
    setSubscription: (subscription: Subscription) => set({subscription: new SubscriptionImpl(subscription)})
}));
