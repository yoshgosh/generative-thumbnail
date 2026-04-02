import { type CSSProperties, FormEvent, useEffect, useState } from 'react';
import { generateThumbnail } from './api/generate';

type CurrentImage = {
    url: string;
    title: string;
    generated: boolean;
};

type HistoryItem = {
    url: string;
    title: string;
};

export default function App() {
    const [title, setTitle] = useState('');
    const [currentImage, setCurrentImage] = useState<CurrentImage>({
        url: '/helloworld.png',
        title: 'Hello World',
        generated: false,
    });
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [historyLayout, setHistoryLayout] = useState({ columns: 1 });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const gap = 6;
        const minTile = 250;
        const maxTile = 350;

        const recalc = () => {
            const available = Math.max(0, window.innerWidth - gap * 2);

            // Pick the smallest column count that keeps each tile <= maxTile.
            // This makes tile width expand/shrink with viewport while preserving edge gutters.
            const columnsByMax = Math.max(1, Math.ceil((available + gap) / (maxTile + gap)));
            const columnsByMin = Math.max(1, Math.floor((available + gap) / (minTile + gap)));
            const columns = Math.min(columnsByMax, columnsByMin + 1);

            setHistoryLayout({ columns });
        };

        recalc();
        window.addEventListener('resize', recalc);
        return () => window.removeEventListener('resize', recalc);
    }, []);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!title.trim() || isLoading) {
            return;
        }

        setIsLoading(true);
        setError(null);
        try {
            const nextTitle = title.trim();
            const blob = await generateThumbnail({
                title: nextTitle,
                text: true,
                text_position: 'bottom-right',
                width: 400,
                height: 400,
                algorithm: '001_v1.0.0',
            });
            const nextUrl = URL.createObjectURL(blob);

            if (currentImage.generated) {
                setHistory((prev) => [{ url: currentImage.url, title: currentImage.title }, ...prev]);
            }

            setCurrentImage({ url: nextUrl, title: nextTitle, generated: true });
            setTitle('');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDownload = (item: HistoryItem, index: number) => {
        const a = document.createElement('a');
        a.href = item.url;
        a.download = `${item.title || 'thumbnail'}-${index + 1}.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    };

    const handleDownloadCurrent = () => {
        const a = document.createElement('a');
        a.href = currentImage.url;
        a.download = `${currentImage.title || 'thumbnail'}-latest.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    };

    return (
        <main className="page">
            <h1 className="page-title">Generative Thumbnail</h1>

            <section className="hero">
                <div className="hero-image-card">
                    <img src={currentImage.url} alt={currentImage.title} className="hero-image" />
                    <div className="history-overlay">
                        <button
                            type="button"
                            className="history-download-text"
                            aria-label={`Download ${currentImage.title}`}
                            onClick={handleDownloadCurrent}
                        >
                            Download
                        </button>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="generate-form">
                    <label className="sr-only" htmlFor="title-input">
                        Title
                    </label>
                    <div className="input-row">
                        <input
                            id="title-input"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="title-input"
                            placeholder="e.g. Hello World!"
                            required
                        />
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="submit-button"
                            aria-label="Generate"
                        >
                            →
                        </button>
                    </div>
                </form>

                {error ? <p className="error-text">{error}</p> : null}
            </section>

            <section className="history-section">
                <div className="section-head">
                    <span>History</span>
                </div>
                <div className="history-grid">
                    <div
                        className="history-grid-inner"
                        style={
                            {
                                ['--history-columns' as string]: historyLayout.columns,
                            } as CSSProperties
                        }
                    >
                        {history.map((item, index) => (
                            <div key={`${item.url}-${index}`} className="history-card">
                                <img
                                    src={item.url}
                                    alt={item.title}
                                    className="history-item"
                                />
                                <div className="history-overlay">
                                    <button
                                        type="button"
                                        className="history-download-text"
                                        aria-label={`Download ${item.title}`}
                                        onClick={() => handleDownload(item, index)}
                                    >
                                        Download
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>
        </main>
    );
}
