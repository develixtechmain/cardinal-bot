import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import svgr from 'vite-plugin-svgr';
import fs from 'fs';
import path from 'path';

export default defineConfig(() => {
    const env = loadEnv('production', process.cwd(), '');
    const useHttp = env.VITE_USE_HTTPS !== 'true';
    console.log(useHttp)
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
            port: 443,
            ...(useHttp ? {} : {
                https: {
                    key: fs.readFileSync(path.resolve(__dirname, 'cardinal_key.pem')),
                    cert: fs.readFileSync(path.resolve(__dirname, 'cardinal_cert.pem')),
                },
            }),
            hmr: {
                protocol: 'wss',
                host: 'app.cardinal-x.online',
                port: 443,
            }
        },
    };
});
