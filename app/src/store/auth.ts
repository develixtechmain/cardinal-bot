import {create} from "zustand/index";
import {BACKEND_BASE_URL} from "../utils/consts";

type AuthStore = {
    accessToken: string | undefined;
    refreshToken: string | undefined;
    clearTokens: () => void;
    refreshAccessToken: () => Promise<string>;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
    accessToken: undefined,
    refreshToken: undefined,
    clearTokens: () => {
        console.log("clearing tokens")
        set({accessToken: undefined, refreshToken: undefined})
        window.location.href = '/'
    },
    refreshAccessToken: async () => {
        const refreshToken = get().refreshToken;
        if (!refreshToken || !isJwtTokenValid(refreshToken)) {
            return await auth(set)
        }

        try {
            let res = await fetch(BACKEND_BASE_URL + '/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({refreshToken}),
            });

            const data = await res.json().catch(() => undefined);
            if (!res.ok || !data || !data.access_token || !data.refresh_token) {
                return await auth(set);
            }

            set({
                accessToken: data.access_token,
                refreshToken: data.refresh_token,
            })

            return data.access_token;
        } catch (error) {
            console.error('refreshAccessToken failed:', error);
            return await auth(set);
        }
    },
}));

const auth = async (set: {
    (partial: AuthStore | Partial<AuthStore> | ((state: AuthStore) => AuthStore | Partial<AuthStore>), replace?: false): void;
    (state: AuthStore | ((state: AuthStore) => AuthStore), replace: true): void;
}) => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
        try {
            const auth = await _auth(tg.initData);

            if (!auth.access_token || !auth.refresh_token) {
                return "";
            }

            set({
                accessToken: auth.access_token,
                refreshToken: auth.refresh_token,
            })
            return auth.access_token;
        } catch (ex) {
            console.error("Authorization failed", ex);
            return "";
        }
    } else {
        return "";
    }
}

const _auth = async (initData: string) => {
    const response = await fetch(BACKEND_BASE_URL + '/auth', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({init_data: initData}),
    });

    const res = await response.json();
    if (!response.ok) {
        throw new Error(res.detail || "unknown auth error");
    }

    return res
}

function isJwtTokenValid(token: string): boolean {
    try {
        const payloadBase64 = token.split('.')[1];
        const payloadJson = atob(payloadBase64);
        const payload = JSON.parse(payloadJson);

        if (!payload.exp) return false;

        const currentTime = Math.floor(Date.now() / 1000);

        return payload.exp > currentTime;
    } catch (error) {
        return false;
    }
}