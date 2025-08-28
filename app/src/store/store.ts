import {create} from 'zustand';
import {Subscription, User} from "../types";

type Store = {
    user: User | undefined;
    setUser: (user: User) => void;

    subscription: Subscription | undefined;
    setSubscription: (subscription: Subscription) => void;
};

export const useStore = create<Store>((set) => ({
    user: undefined,
    setUser: (user) => set({user}),

    subscription: undefined,
    setSubscription: (subscription: Subscription) => set({subscription}),
}));
