import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const environment = loadEnv(mode, process.cwd(), 'VITE_');
    const port = Number(environment.VITE_PORT || 5173);
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
        throw new Error('VITE_PORT must be an integer from 1 to 65535');
    }

    return {
        plugins: [react()],
        server: {
            host: environment.VITE_HOST || '0.0.0.0',
            port,
            strictPort: true,
        },
    };
});
