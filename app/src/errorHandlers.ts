import {useErrorStore} from "./store/error";

window.onerror = (message, source, lineno, colno, error) => {
    useErrorStore.getState().setError("exception", String(message), window.location.pathname);
    return false;
};

window.onunhandledrejection = (event) => {
    const reason = event.reason instanceof Error ? event.reason.message : String(event.reason);
    useErrorStore.getState().setError("exception", reason, window.location.pathname);
};
