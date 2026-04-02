import { type CSSProperties, FormEvent, useEffect, useState } from 'react';
import { generateThumbnail } from './api/generate';
import { buildHistoryImageUrl, getRecentHistory } from './api/history';

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
    fileName: string;
    generated: boolean;
    shared: boolean;
};

type HistoryItem = {
    blobName: string;
    url: string;
    title: string;
    fileName: string;
    shared: boolean;
};

type CustomDownloadTarget = {
    title: string;
};

const CUSTOM_OPTIONS_STORAGE_KEY = 'display-web.custom-download-options';

export default function App() {
    const [title, setTitle] = useState('');
    const [agreedToTerms, setAgreedToTerms] = useState(false);
    const [isTermsModalOpen, setIsTermsModalOpen] = useState(false);
    const [currentImage, setCurrentImage] = useState<CurrentImage>({
        url: '/Hello World!.png',
        title: 'Hello World!',
        fileName: 'Hello_World!_w400_h400_br.png',
        generated: false,
        shared: false,
    });
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [historyNextCursor, setHistoryNextCursor] = useState<number | null>(null);
    const [isHistoryLoading, setIsHistoryLoading] = useState(false);
    const [historyLayout, setHistoryLayout] = useState({ columns: 1 });
    const [isLoading, setIsLoading] = useState(false);
    const [isCustomDownloading, setIsCustomDownloading] = useState(false);
    const [isSharing, setIsSharing] = useState(false);
    const [sharingTargetUrl, setSharingTargetUrl] = useState<string | null>(null);
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

    useEffect(() => {
        let alive = true;
        (async () => {
            try {
                const { items, nextCursor } = await getRecentHistory(12);
                if (!alive) {
                    return;
                }
                setHistory(
                    items.map((item) => ({
                        blobName: item.blob_name,
                        url: buildHistoryImageUrl(item.blob_name),
                        title: item.title,
                        fileName: item.file_name,
                        shared: true,
                    })),
                );
                setHistoryNextCursor(nextCursor);
            } catch {
                // keep empty history on initial load failure
            }
        })();
        return () => {
            alive = false;
        };
    }, []);

    const loadMoreHistory = async () => {
        if (!agreedToTerms) {
            setIsTermsModalOpen(true);
            return;
        }
        if (isHistoryLoading || historyNextCursor === null) {
            return;
        }
        setIsHistoryLoading(true);
        try {
            const { items, nextCursor } = await getRecentHistory(12, historyNextCursor);
            const mapped: HistoryItem[] = items.map((item) => ({
                blobName: item.blob_name,
                url: buildHistoryImageUrl(item.blob_name),
                title: item.title,
                fileName: item.file_name,
                shared: true,
            }));
            setHistory((prev) => {
                const seen = new Set(prev.map((it) => it.blobName));
                const merged = [...prev];
                for (const item of mapped) {
                    if (!seen.has(item.blobName)) {
                        merged.push(item);
                        seen.add(item.blobName);
                    }
                }
                return merged;
            });
            setHistoryNextCursor(nextCursor);
        } catch {
            // keep current history on pagination error
        } finally {
            setIsHistoryLoading(false);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!agreedToTerms) {
            setIsTermsModalOpen(true);
            return;
        }
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
                save: false,
            });
            const nextUrl = URL.createObjectURL(blob);
            const nextFileName = buildFileName({
                title: nextTitle,
                width: 400,
                height: 400,
                textToken: 'br',
            });

            if (currentImage.generated) {
                setHistory((prev) => [
                    {
                        blobName: `local:${currentImage.url}`,
                        url: currentImage.url,
                        title: currentImage.title,
                        fileName: currentImage.fileName,
                        shared: currentImage.shared,
                    },
                    ...prev,
                ]);
            }

            setCurrentImage({
                url: nextUrl,
                title: nextTitle,
                fileName: nextFileName,
                generated: true,
                shared: false,
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

    const buildFileName = ({
        title: fileTitle,
        width,
        height,
        textToken,
    }: {
        title: string;
        width: number;
        height: number;
        textToken: 'n' | 'c' | 'tl' | 'tr' | 'bl' | 'br';
    }) => `${sanitizeFileTitle(fileTitle)}_w${width}_h${height}_${textToken}.png`;

    const handleDownload = (item: HistoryItem) => {
        if (!agreedToTerms) {
            setIsTermsModalOpen(true);
            return;
        }
        const a = document.createElement('a');
        a.href = item.url;
        a.download = item.fileName;
        document.body.appendChild(a);
        a.click();
        a.remove();
    };

    const handleDownloadCurrent = () => {
        if (!agreedToTerms) {
            setIsTermsModalOpen(true);
            return;
        }
        const a = document.createElement('a');
        a.href = currentImage.url;
        a.download = currentImage.fileName;
        document.body.appendChild(a);
        a.click();
        a.remove();
    };

    const handleShare = async (item: { title: string; url: string }, kind: 'current' | 'history') => {
        if (!agreedToTerms) {
            setIsTermsModalOpen(true);
            return;
        }
        if (isSharing) {
            return;
        }

        setIsSharing(true);
        setSharingTargetUrl(item.url);
        setError(null);
        try {
            await generateThumbnail({
                title: item.title,
                text: true,
                text_position: 'bottom-right',
                width: 400,
                height: 400,
                algorithm: '001_v1.0.0',
                save: true,
            });
            if (kind === 'current') {
                setCurrentImage((prev) => ({ ...prev, shared: true }));
            } else {
                setHistory((prev) =>
                    prev.map((historyItem) =>
                        historyItem.url === item.url ? { ...historyItem, shared: true } : historyItem,
                    ),
                );
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsSharing(false);
            setSharingTargetUrl(null);
        }
    };

    const openCustomDownload = (target: CustomDownloadTarget) => {
        if (!agreedToTerms) {
            setIsTermsModalOpen(true);
            return;
        }
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
            return { text: false as const, text_position: 'bottom-right' as const, text_token: 'n' as const };
        }
        if (position === 'C') {
            return { text: true as const, text_position: 'center' as const, text_token: 'c' as const };
        }
        if (position === 'TL') {
            return { text: true as const, text_position: 'top-left' as const, text_token: 'tl' as const };
        }
        if (position === 'TR') {
            return { text: true as const, text_position: 'top-right' as const, text_token: 'tr' as const };
        }
        if (position === 'BL') {
            return { text: true as const, text_position: 'bottom-left' as const, text_token: 'bl' as const };
        }
        return { text: true as const, text_position: 'bottom-right' as const, text_token: 'br' as const };
    };

    const handleCustomDownload = async () => {
        if (!agreedToTerms) {
            setIsTermsModalOpen(true);
            return;
        }
        if (!customTarget || isCustomDownloading) {
            return;
        }

        setIsCustomDownloading(true);
        setError(null);
        try {
            const { width, height } = resolveDimensions(customScale, customRatio);
            const { text, text_position, text_token } = resolveTextOption(customTextPosition);
            const blob = await generateThumbnail({
                title: customTarget.title,
                text,
                text_position,
                width,
                height,
                algorithm: '001_v1.0.0',
                save: false,
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = buildFileName({
                title: customTarget.title,
                width,
                height,
                textToken: text_token,
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
                            className="history-share-text"
                            aria-label={`Share ${currentImage.title}`}
                            onClick={() =>
                                handleShare({
                                    title: currentImage.title,
                                    url: currentImage.url,
                                }, 'current')
                            }
                            disabled={isSharing || currentImage.shared}
                        >
                            {currentImage.shared
                                ? 'Shared'
                                : isSharing && sharingTargetUrl === currentImage.url
                                  ? 'Sharing...'
                                  : 'Share'}
                        </button>
                        <div className="history-overlay-actions">
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
                </div>

                <form onSubmit={handleSubmit} className="generate-form" autoComplete="off">
                    <div className="terms-consent">
                        <input
                            type="checkbox"
                            checked={agreedToTerms}
                            onChange={(e) => setAgreedToTerms(e.target.checked)}
                            className="terms-checkbox"
                            aria-label="利用規約に同意する"
                        />
                        <span className="terms-inline-text">
                            <button
                                type="button"
                                className="terms-link"
                                onClick={() => setIsTermsModalOpen(true)}
                            >
                                利用規約
                            </button>
                            に同意します。
                        </span>
                    </div>
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
                            autoComplete="off"
                            autoCorrect="off"
                            autoCapitalize="off"
                            spellCheck={false}
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
                        {history.map((item) => (
                            <div key={item.blobName} className="history-card">
                                <img
                                    src={item.url}
                                    alt={item.title}
                                    className="history-item"
                                />
                                <div className="history-overlay">
                                    <button
                                        type="button"
                                        className="history-share-text"
                                        aria-label={`Share ${item.title}`}
                                        onClick={() =>
                                            handleShare({
                                                title: item.title,
                                                url: item.url,
                                            }, 'history')
                                        }
                                        disabled={isSharing || item.shared}
                                    >
                                        {item.shared
                                            ? 'Shared'
                                            : isSharing && sharingTargetUrl === item.url
                                              ? 'Sharing...'
                                              : 'Share'}
                                    </button>
                                    <div className="history-overlay-actions">
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
                            </div>
                        ))}
                    </div>
                </div>
                {history.length > 0 ? (
                    <div className="history-load-more-wrap">
                        <button
                            type="button"
                            className="history-load-more-button"
                            onClick={loadMoreHistory}
                            disabled={isHistoryLoading || historyNextCursor === null}
                        >
                            {isHistoryLoading ? 'Loading...' : historyNextCursor === null ? 'No more' : 'Load more'}
                        </button>
                    </div>
                ) : null}
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

            {isTermsModalOpen ? (
                <div className="terms-modal-backdrop" role="presentation" onClick={() => setIsTermsModalOpen(false)}>
                    <div
                        className="terms-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-label="利用規約"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h2 className="terms-modal-title">利用規約</h2>
                        <ul className="terms-list">
                            <li>入力内容およびShare内容についての責任は、利用者本人が負います。</li>
                            <li>誹謗中傷、差別、違法行為、公序良俗に反する投稿、第三者の権利侵害を禁止します。</li>
                            <li>入力内容、生成条件、操作履歴などのログを運営者が記録・保管することに同意します。</li>
                            <li>Shareした内容は他の利用者に閲覧・保存・再共有される可能性があり、完全な削除を保証しません。</li>
                            <li>本サービス利用により生じた損害・トラブルについて、運営者の責任は法令上許される範囲で制限されます。</li>
                            <li>運営者は、規約違反コンテンツの削除、利用停止、規約の改定を行うことができます。</li>
                        </ul>
                        <div className="terms-modal-actions">
                            <button
                                type="button"
                                className="custom-action-button ghost"
                                onClick={() => setIsTermsModalOpen(false)}
                            >
                                閉じる
                            </button>
                            <button
                                type="button"
                                className="custom-action-button"
                                onClick={() => {
                                    setAgreedToTerms(true);
                                    setIsTermsModalOpen(false);
                                }}
                            >
                                同意する
                            </button>
                        </div>
                    </div>
                </div>
            ) : null}
        </main>
    );
}
