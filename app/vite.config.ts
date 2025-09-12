import {defineConfig, loadEnv} from 'vite';
import react from '@vitejs/plugin-react';
import svgr from 'vite-plugin-svgr';
import fs from 'fs';
import path from 'path';

export default defineConfig(({mode}) => {
    const env = loadEnv(mode, process.cwd(), '');
    const useHttp = env.VITE_USE_HTTPS !== 'true';
    return {
        plugins: [react(), svgr({
            svgrOptions: {
                exportType: 'default',
                ref: true,
                svgo: true,
                titleProp: true,
                svgoConfig: {
                    plugins: [
                        {name: 'removeViewBox', active: false},
                        {name: 'removeDimensions', active: true},
                    ],
                },
            },
            include: '**/*.svg',
        })],
        server: {
            host: '0.0.0.0',
            port: 5173,
            ...(useHttp ? {} : {
                https: {
                    key: fs.readFileSync(path.resolve(__dirname, 'key.pem')),
                    cert: fs.readFileSync(path.resolve(__dirname, 'cert.pem')),
                },
            }),
        },
    };
});
