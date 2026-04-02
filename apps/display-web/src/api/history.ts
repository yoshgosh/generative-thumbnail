import { env } from '../config/env';

export type HistoryApiItem = {
    blob_name: string;
    algorithm: string;
    file_name: string;
    title: string;
    width: number;
    height: number;
    text_token: 'n' | 'c' | 'tl' | 'tr' | 'bl' | 'br';
    last_modified: string | null;
};

type HistoryApiResponse = {
    items: HistoryApiItem[];
    limit: number;
    count: number;
};

export async function getRecentHistory(limit = 12): Promise<HistoryApiItem[]> {
    const query = new URLSearchParams({ limit: String(limit) });
    const res = await fetch(`${env.VITE_API_BASE_URL}/history?${query.toString()}`);
    if (!res.ok) {
        throw new Error(`History request failed with status ${res.status}`);
    }
    const data = (await res.json()) as HistoryApiResponse;
    return data.items ?? [];
}

export function buildHistoryImageUrl(blobName: string): string {
    const query = new URLSearchParams({ blob_name: blobName });
    return `${env.VITE_API_BASE_URL}/history/image?${query.toString()}`;
}
