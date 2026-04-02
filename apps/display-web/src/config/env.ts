function normalizeBaseUrl(value: string): string {
    return value.replace(/\/+$/, '');
}

const fallbackBaseUrl = 'http://localhost:7071/api';

export const env = {
    VITE_API_BASE_URL: normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL ?? fallbackBaseUrl),
};
