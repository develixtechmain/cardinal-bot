import React, {useEffect, useState} from "react";
import {useErrorStore} from "../../../store/error";
import ExceptionModal from "./ExceptionModal";
import {useLocation} from "wouter";
import SubscriptionModal from "./SubscriptionModal";

export default function GlobalModals() {
    const [currentLocation] = useLocation();
    const {type, location, clearError} = useErrorStore();
    const [canShow, setCanShow] = useState(false);

    useEffect(() => {
        setCanShow(false);
        const id = setTimeout(() => setCanShow(true), 0);
        return () => clearTimeout(id);
    }, [currentLocation, location, type]);

    if (!canShow) return null;
    if (currentLocation !== location) return null;

    if (type === "exception") {
        return <ExceptionModal isOpen={true} onClose={clearError}/>;
    }

    if (type === "subscription") {
        return <SubscriptionModal isOpen={true} onClose={clearError}/>;
    }

    return null;
}
