import { env } from '../config/env';

export type GenerateRequest = {
    title: string;
    text?: boolean;
    text_position?: 'center' | 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
    font_scale?: number;
    size?: number;
    width?: number;
    height?: number;
    algorithm?: string;
    save?: boolean;
};

export async function generateThumbnail(request: GenerateRequest): Promise<Blob> {
    const res = await fetch(`${env.VITE_API_BASE_URL}/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    if (!res.ok) {
        let message = `Request failed with status ${res.status}`;
        try {
            const errorBody = (await res.json()) as { error?: string };
            if (errorBody.error) {
                message = errorBody.error;
            }
        } catch {
            // ignore parse error
        }
        throw new Error(message);
    }

    return res.blob();
}
