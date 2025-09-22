import {Component, ReactNode} from "react";

import {useErrorStore} from "../../../store/error";
import GlobalModals from "./GlobalModals";

export class ErrorBoundary extends Component<{children: ReactNode}> {
    static getDerivedStateFromError(error: Error) {
        return null;
    }

    componentDidCatch(error: Error) {
        useErrorStore.getState().setError("exception", error.message, window.location.pathname);
    }

    render() {
        const {type} = useErrorStore.getState();

        if (type !== null) {
            // TODO FIXME
            return (
                <div style={{position: "fixed", top: 0, left: 0, height: "var(--tg-vh)", width: "100%"}}>
                    <GlobalModals />
                </div>
            );
        } else {
            return this.props.children;
        }
    }
}
