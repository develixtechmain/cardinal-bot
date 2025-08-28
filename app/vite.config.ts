import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import svgr from 'vite-plugin-svgr';
import fs from 'fs';

export default defineConfig({
    plugins: [react(), svgr({
        svgrOptions: {
            exportType: "default",
            ref: true,
            svgo: true,
            titleProp: true,
            svgoConfig: {
                plugins: [
                    {
                        name: 'removeViewBox',
                        active: false,
                    },
                    {
                        name: 'removeDimensions',
                        active: true,
                    },
                ],
            },
        },
        include: "**/*.svg",
    }),],
    server: {
        https: {
            key: fs.readFileSync('/media/user/free/cardinal/app/localhost+2-key.pem'),
            cert: fs.readFileSync('/media/user/free/cardinal/app/localhost+2.pem')
        },
        host: '0.0.0.0',
        port: 5173,
    },
});
