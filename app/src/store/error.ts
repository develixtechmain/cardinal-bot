import {create} from "zustand";

export type ErrorType = "exception" | "subscription" | null;

interface ErrorState {
    type: ErrorType;
    message?: string;
    location?: string;
    setError: (type: ErrorType, message?: string, location?: string) => void;
    clearError: () => void;
}

export const useErrorStore = create<ErrorState>((set) => ({
    type: null,
    message: undefined,
    location: undefined,
    setError: (type, message, location) => set({type, message, location}),
    clearError: () => set({type: null, message: undefined, location: undefined}),
}));
