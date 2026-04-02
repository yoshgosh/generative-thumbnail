import { type CSSProperties, FormEvent, useEffect, useState } from 'react';
import { generateThumbnail } from './api/generate';

type DownloadScale = 'x1' | 'x2' | 'x4';
type DownloadRatio = '1:1' | '4:3' | '16:9';
type DownloadTextPosition = 'N' | 'C' | 'TL' | 'TR' | 'BL' | 'BR';

type DownloadOptions = {
    scale: DownloadScale;
    ratio: DownloadRatio;
    textPosition: DownloadTextPosition;
};

type StoredDownloadOptions = {
    scale?: DownloadScale;
    ratio?: DownloadRatio;
    textPosition?: DownloadTextPosition;
};

type CurrentImage = {
    url: string;
    title: string;
    generated: boolean;
    options: DownloadOptions;
};

type HistoryItem = {
    url: string;
    title: string;
    options: DownloadOptions;
};

type CustomDownloadTarget = {
    title: string;
};

const CUSTOM_OPTIONS_STORAGE_KEY = 'display-web.custom-download-options';

export default function App() {
    const [title, setTitle] = useState('');
    const [currentImage, setCurrentImage] = useState<CurrentImage>({
        url: '/Hello World!.png',
        title: 'Hello World!',
        generated: false,
        options: {
            scale: 'x1',
            ratio: '1:1',
            textPosition: 'BR',
        },
    });
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [historyLayout, setHistoryLayout] = useState({ columns: 1 });
    const [isLoading, setIsLoading] = useState(false);
    const [isCustomDownloading, setIsCustomDownloading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [customTarget, setCustomTarget] = useState<CustomDownloadTarget | null>(null);
    const [customScale, setCustomScale] = useState<DownloadScale>('x1');
    const [customRatio, setCustomRatio] = useState<DownloadRatio>('1:1');
    const [customTextPosition, setCustomTextPosition] = useState<DownloadTextPosition>('BR');

    useEffect(() => {
        try {
            const raw = window.localStorage.getItem(CUSTOM_OPTIONS_STORAGE_KEY);
            if (!raw) {
                return;
            }
            const parsed = JSON.parse(raw) as StoredDownloadOptions;
            if (parsed.scale === 'x1' || parsed.scale === 'x2' || parsed.scale === 'x4') {
                setCustomScale(parsed.scale);
            }
            if (parsed.ratio === '1:1' || parsed.ratio === '4:3' || parsed.ratio === '16:9') {
                setCustomRatio(parsed.ratio);
            }
            if (
                parsed.textPosition === 'N' ||
                parsed.textPosition === 'C' ||
                parsed.textPosition === 'TL' ||
                parsed.textPosition === 'TR' ||
                parsed.textPosition === 'BL' ||
                parsed.textPosition === 'BR'
            ) {
                setCustomTextPosition(parsed.textPosition);
            }
        } catch {
            // ignore invalid localStorage value
        }
    }, []);

    useEffect(() => {
        const stored: DownloadOptions = {
            scale: customScale,
            ratio: customRatio,
            textPosition: customTextPosition,
        };
        window.localStorage.setItem(CUSTOM_OPTIONS_STORAGE_KEY, JSON.stringify(stored));
    }, [customScale, customRatio, customTextPosition]);

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
                setHistory((prev) => [{ url: currentImage.url, title: currentImage.title, options: currentImage.options }, ...prev]);
            }

            setCurrentImage({
                url: nextUrl,
                title: nextTitle,
                generated: true,
                options: {
                    scale: 'x1',
                    ratio: '1:1',
                    textPosition: 'BR',
                },
            });
            setTitle('');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsLoading(false);
        }
    };

    const sanitizeFileTitle = (value: string) => {
        const trimmed = value.trim();
        const safe = trimmed.replace(/[\\/:*?"<>|]/g, '_').replace(/\s+/g, '_');
        return safe || 'thumbnail';
    };

    const ratioToken = (ratio: DownloadRatio) => {
        if (ratio === '1:1') {
            return '11';
        }
        if (ratio === '4:3') {
            return '43';
        }
        return '169';
    };

    const buildFileName = (name: string, options: DownloadOptions) =>
        `${sanitizeFileTitle(name)}_${options.scale}_${ratioToken(options.ratio)}_${options.textPosition}.png`;

    const handleDownload = (item: HistoryItem) => {
        const a = document.createElement('a');
        a.href = item.url;
        a.download = buildFileName(item.title, item.options);
        document.body.appendChild(a);
        a.click();
        a.remove();
    };

    const handleDownloadCurrent = () => {
        const a = document.createElement('a');
        a.href = currentImage.url;
        a.download = buildFileName(currentImage.title, currentImage.options);
        document.body.appendChild(a);
        a.click();
        a.remove();
    };

    const openCustomDownload = (target: CustomDownloadTarget) => {
        setCustomTarget(target);
    };

    const closeCustomDownload = () => {
        if (isCustomDownloading) {
            return;
        }
        setCustomTarget(null);
    };

    const resolveDimensions = (scale: DownloadScale, ratio: DownloadRatio) => {
        const multiplier = scale === 'x1' ? 1 : scale === 'x2' ? 2 : 4;
        const longSide = 400 * multiplier;
        if (ratio === '1:1') {
            return { width: longSide, height: longSide };
        }
        if (ratio === '4:3') {
            return { width: longSide, height: Math.round((longSide * 3) / 4) };
        }
        return { width: longSide, height: Math.round((longSide * 9) / 16) };
    };

    const resolveTextOption = (position: DownloadTextPosition) => {
        if (position === 'N') {
            return { text: false as const, text_position: 'bottom-right' as const };
        }
        if (position === 'C') {
            return { text: true as const, text_position: 'center' as const };
        }
        if (position === 'TL') {
            return { text: true as const, text_position: 'top-left' as const };
        }
        if (position === 'TR') {
            return { text: true as const, text_position: 'top-right' as const };
        }
        if (position === 'BL') {
            return { text: true as const, text_position: 'bottom-left' as const };
        }
        return { text: true as const, text_position: 'bottom-right' as const };
    };

    const handleCustomDownload = async () => {
        if (!customTarget || isCustomDownloading) {
            return;
        }

        setIsCustomDownloading(true);
        setError(null);
        try {
            const { width, height } = resolveDimensions(customScale, customRatio);
            const { text, text_position } = resolveTextOption(customTextPosition);
            const blob = await generateThumbnail({
                title: customTarget.title,
                text,
                text_position,
                width,
                height,
                algorithm: '001_v1.0.0',
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = buildFileName(customTarget.title, {
                scale: customScale,
                ratio: customRatio,
                textPosition: customTextPosition,
            });
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            setCustomTarget(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsCustomDownloading(false);
        }
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
                        <button
                            type="button"
                            className="history-custom-download-text"
                            aria-label={`Custom download ${currentImage.title}`}
                            onClick={() =>
                                openCustomDownload({
                                    title: currentImage.title,
                                })
                            }
                        >
                            Custom Download
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
                                        onClick={() => handleDownload(item)}
                                    >
                                        Download
                                    </button>
                                    <button
                                        type="button"
                                        className="history-custom-download-text"
                                        aria-label={`Custom download ${item.title}`}
                                        onClick={() =>
                                            openCustomDownload({
                                                title: item.title,
                                            })
                                        }
                                    >
                                        Custom Download
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {customTarget ? (
                <div className="custom-modal-backdrop" role="presentation" onClick={closeCustomDownload}>
                    <div
                        className="custom-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-label="Custom Download"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h2 className="custom-modal-title">Custom Download</h2>

                        <div className="custom-field">
                            <span className="custom-field-label">Title</span>
                            <p className="custom-title-value">{customTarget.title || '-'}</p>
                        </div>

                        <div className="custom-field">
                            <span className="custom-field-label">Long Side</span>
                            <div className="custom-options-row">
                                {(['x1', 'x2', 'x4'] as const).map((value) => (
                                    <button
                                        key={value}
                                        type="button"
                                        className={`custom-option-button ${customScale === value ? 'is-selected' : ''}`}
                                        onClick={() => setCustomScale(value)}
                                    >
                                        {value}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="custom-field">
                            <span className="custom-field-label">Aspect</span>
                            <div className="custom-options-row">
                                {(['1:1', '4:3', '16:9'] as const).map((value) => (
                                    <button
                                        key={value}
                                        type="button"
                                        className={`custom-option-button ${customRatio === value ? 'is-selected' : ''}`}
                                        onClick={() => setCustomRatio(value)}
                                    >
                                        {value}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="custom-field">
                            <span className="custom-field-label">Text</span>
                            <div className="custom-options-row wrap">
                                {(['N', 'C', 'TL', 'TR', 'BL', 'BR'] as const).map((value) => (
                                    <button
                                        key={value}
                                        type="button"
                                        className={`custom-option-button ${customTextPosition === value ? 'is-selected' : ''}`}
                                        onClick={() => setCustomTextPosition(value)}
                                    >
                                        {value}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="custom-modal-actions">
                            <button
                                type="button"
                                className="custom-action-button ghost"
                                onClick={closeCustomDownload}
                                disabled={isCustomDownloading}
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                className="custom-action-button"
                                onClick={handleCustomDownload}
                                disabled={isCustomDownloading}
                            >
                                {isCustomDownloading ? 'Generating...' : 'Download'}
                            </button>
                        </div>
                    </div>
                </div>
            ) : null}
        </main>
    );
}
