interface ImportMetaEnv {
    readonly VITE_BACKEND_BASE_URL: string;
    readonly VITE_AI_CORE_BASE_URL: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
