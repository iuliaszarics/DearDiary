import React, { useMemo, useState } from 'react';
import styles from './happyMemoriesCollection.module.css';

function isPositiveEntry(item) {
    return item?.insight?.bucket === 'positive' || item?.predicted_emotion === 'positive';
}

function getFlashbackLabel(entryDateStr) {
    if (!entryDateStr) return null;
    const entry = new Date(entryDateStr);
    const today = new Date();
    const entryDate = new Date(entry.getFullYear(), entry.getMonth(), entry.getDate());
    const todayDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const diffTime = todayDate - entryDate;
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays <= 0) return null;
    
    if (diffDays === 7) return '1 week ago today';
    if (diffDays === 14) return '2 weeks ago today';
    if (diffDays === 21) return '3 weeks ago today';
    
    if (entryDate.getDate() === todayDate.getDate()) {
        const yearDiff = todayDate.getFullYear() - entryDate.getFullYear();
        const monthDiff = todayDate.getMonth() - entryDate.getMonth();
        const totalMonths = yearDiff * 12 + monthDiff;
        
        if (totalMonths > 0) {
            if (totalMonths < 12) {
                return totalMonths === 1 ? '1 month ago today' : `${totalMonths} months ago today`;
            } else if (totalMonths % 12 === 0) {
                const years = totalMonths / 12;
                return years === 1 ? '1 year ago today' : `${years} years ago today`;
            }
        }
    }
    return null;
}

function buildHappyMemories(history) {
    const positiveEntries = (history || [])
        .filter(isPositiveEntry)
        .sort((a, b) => new Date(b.occured_at) - new Date(a.occured_at));
    return positiveEntries.map((item) => ({
        raw: item,
        entry_id: item?.entry_id,
        title: item?.insight?.title || 'Positive moment',
        summary: item?.text || 'A positive moment was saved in your history.',
        date: item?.occured_at,
        emotion: item?.predicted_emotion,
        confidence: item?.confidence,
    }));
}

function formatDateTime(value) {
    if (!value) {
        return 'Unknown time';
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return value;
    }
    return parsed.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}

function formatTime(value) {
    if (!value) return '';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return '';
    return parsed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function HappyMemoriesCollection({ history, onMemoryClick }) {
    const [selectedFlashback, setSelectedFlashback] = useState(null);
    const memories = useMemo(() => buildHappyMemories(history), [history]);
    const flashbacks = useMemo(() => {
        const groups = {};
        (history || []).forEach((item) => {
            if (!isPositiveEntry(item)) return;
            const label = getFlashbackLabel(item.occured_at);
            if (label) {
                const dateKey = new Date(item.occured_at).toDateString();
                if (!groups[dateKey]) {
                    groups[dateKey] = {
                        label,
                        date: item.occured_at,
                        entries: []
                    };
                }
                groups[dateKey].entries.push(item);
            }
        });
        return Object.values(groups).sort((a, b) => new Date(b.date) - new Date(a.date));
    }, [history]);
    return (
        <article className={styles.card}>
            <div className={styles.header}>
                <h2>Happy Memories Collection</h2>
                <p className={styles.subtitle}>All your positive moments in one place</p>
            </div>
            {}
            {flashbacks.length > 0 && (
                <div className={styles.memoriesList}>
                    <h3 className={styles.sectionTitle}>Flashbacks</h3>
                    <div className={styles.memories}>
                        {flashbacks.map((fb) => (
                            <section
                                key={fb.label + fb.date}
                                className={styles.memoryItem}
                                onClick={() => {
                                    if (fb.entries && fb.entries.length > 0) {
                                        onMemoryClick?.(fb.entries[0]);
                                    }
                                }}
                                role="button"
                                tabIndex={0}
                                onKeyPress={(e) => {
                                    if ((e.key === 'Enter' || e.key === ' ') && fb.entries && fb.entries.length > 0) {
                                        onMemoryClick?.(fb.entries[0]);
                                    }
                                }}
                            >
                                <div className={styles.memoryHeader}>
                                    <h3 className={styles.title}>{formatDateTime(fb.date)}</h3>
                                    <span className={styles.emotion} style={{ background: '#d66dd1' }}>{fb.label}</span>
                                </div>
                                <p className={styles.summary}>
                                    "{fb.entries[0]?.text || 'No text'}"
                                </p>
                                <small className={styles.date}>
                                    {fb.entries.length} positive moment{fb.entries.length !== 1 ? 's' : ''} on this day &bull; Click to View
                                </small>
                            </section>
                        ))}
                    </div>
                </div>
            )}
            {memories.length === 0 ? (
                <p className={styles.emptyState}>No happy memories yet. Start journaling to collect positive moments!</p>
            ) : (
                <div className={styles.memoriesList}>
                    <h3 className={styles.sectionTitle}>Happy Memories</h3>
                    <p className={styles.count}>{memories.length} positive moment{memories.length !== 1 ? 's' : ''} saved</p>
                    <div className={styles.memories}>
                        {memories.map((memory) => (
                            <section
                                key={`${memory.entry_id}-${memory.date}`}
                                className={styles.memoryItem}
                                onClick={() => onMemoryClick?.(memory.raw || memory)}
                                role="button"
                                tabIndex={0}
                                onKeyPress={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ') {
                                        onMemoryClick?.(memory.raw || memory);
                                    }
                                }}
                            >
                                <div className={styles.memoryHeader}>
                                    <h3 className={styles.title}>{formatDateTime(memory.date)}</h3>
                                    <span className={styles.emotion}>{memory.emotion}</span>
                                </div>
                                <p className={styles.summary}>{memory.summary}</p>
                                <small className={styles.date}>Open insight: {memory.title}</small>
                            </section>
                        ))}
                    </div>
                </div>
            )}
            {}
            {selectedFlashback && (
                <div className={styles.modalOverlay} onClick={() => setSelectedFlashback(null)}>
                    <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
                        <header className={styles.modalHeader}>
                            <div>
                                <h3 className={styles.modalTitle}>Flashback: {selectedFlashback.label}</h3>
                                <span className={styles.modalDate}>{formatDateTime(selectedFlashback.date)}</span>
                            </div>
                            <button className={styles.closeModalBtn} onClick={() => setSelectedFlashback(null)}>✕</button>
                        </header>
                        <div className={styles.modalBody}>
                            {selectedFlashback.entries.map((entry) => (
                                <article key={entry.entry_id} className={styles.modalEntryCard}>
                                    <div className={styles.modalEntryHeader}>
                                        <span className={styles.modalEntryTime}>{formatTime(entry.occured_at)}</span>
                                        <span className={styles.modalEntryEmotion}>{entry.predicted_emotion}</span>
                                    </div>
                                    <p className={styles.modalEntryText}>{entry.text}</p>
                                    <div className={styles.modalEntryActions}>
                                        <button
                                            className={styles.modalViewInsightsBtn}
                                            onClick={() => {
                                                setSelectedFlashback(null);
                                                onMemoryClick?.(entry);
                                            }}
                                        >
                                            View full insights & advice
                                        </button>
                                    </div>
                                </article>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </article>
    );
}
