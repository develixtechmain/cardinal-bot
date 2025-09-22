import {PropsWithChildren, useEffect} from "react";

import {Redirect, useLocation} from "wouter";

import {useErrorStore} from "./store/error";
import {useStore} from "./store/store";

export const ProtectedRoute = ({children}: PropsWithChildren) => {
    const [location] = useLocation();

    const user = useStore((s) => s.user);
    const subscription = useStore((s) => s.subscription);

    if (!user || !subscription) {
        console.log("Protection caught user or subscription is missing. Redirecting to homepage");
        return <Redirect to={"/"} />;
    }

    useEffect(() => {
        if (subscription.isSubscriptionExpired()) useErrorStore.getState().setError("subscription", "expired", location);
    }, [subscription]);

    return children;
};
