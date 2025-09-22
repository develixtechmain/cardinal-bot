import {useAuthStore} from "../store/auth";
import {SERVICE_LOCATOR, Service} from "./consts";

export async function authFetch(service: Service, input: RequestInfo, init?: RequestInit): Promise<Response> {
    const {accessToken, refreshAccessToken, clearTokens} = useAuthStore.getState();

    const authHeaders: Record<string, string> = {};

    if (accessToken) {
        authHeaders["Authorization"] = `Bearer ${accessToken}`;
    }

    const fetchInit: RequestInit = {...init, headers: {...(init?.headers || {}), ...authHeaders}};

    let url: RequestInfo = input;

    if (typeof input === "string" && input.startsWith("/")) {
        url = SERVICE_LOCATOR[service] + input;
    }

    let response = await fetch(url, fetchInit);

    if (response.status === 401) {
        const refreshed = await refreshAccessToken();

        if (refreshed !== "") {
            const retryHeaders = {...(init?.headers || {}), Authorization: `Bearer ${refreshed}`};

            response = await fetch(url, {...init, headers: retryHeaders});
        } else {
            clearTokens();
        }
    }

    return response;
}
