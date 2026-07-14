import React, { useMemo } from 'react';
import styles from './flashback.module.css';

function isPositiveEntry(item) {
    return item?.insight?.bucket === 'positive' || item?.predicted_emotion === 'positive';
}

function isSameDate(left, right) {
    return left.getFullYear() === right.getFullYear()
        && left.getMonth() === right.getMonth()
        && left.getDate() === right.getDate();
}

function getFlashbackLabel(entryDate) {
    if (!entryDate) return null;
    const entry = new Date(entryDate);
    const today = new Date();
    const entryCal = new Date(entry.getFullYear(), entry.getMonth(), entry.getDate());
    const todayCal = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const diffTime = todayCal - entryCal;
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays <= 0) return null;
    
    if (diffDays === 7) return '1 week ago today';
    if (diffDays === 14) return '2 weeks ago today';
    if (diffDays === 21) return '3 weeks ago today';
    
    if (entryCal.getDate() === todayCal.getDate()) {
        const yearDiff = todayCal.getFullYear() - entryCal.getFullYear();
        const monthDiff = todayCal.getMonth() - entryCal.getMonth();
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

function buildFlashbacks(history) {
    const positiveEntries = (history || [])
        .filter(isPositiveEntry)
        .map((item) => {
            const label = getFlashbackLabel(item?.occured_at);
            return label ? {
                raw: item,
                entry_id: item?.entry_id,
                label,
                title: item?.occured_at,
                summary: item?.text || 'A positive moment was saved in your history.',
                date: item?.occured_at,
            } : null;
        })
        .filter((item) => item !== null)
        .sort((a, b) => new Date(b.date) - new Date(a.date));
    return positiveEntries;
}

function formatDateTime(value) {
    if (!value) {
        return 'Unknown time';
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return value;
    }
    return parsed.toLocaleDateString();
}

export default function FlashbackView({ history, onFlashbackClick }) {
    const flashbacks = useMemo(() => buildFlashbacks(history), [history]);
    return (
        <article className={styles.card}>
            <div className={styles.header}>
                <h2>Recent Flashbacks</h2>
                <p className={styles.subtitle}>Happy moments from last week, last month, and last year</p>
            </div>
            {flashbacks.length === 0 ? (
                <p className={styles.emptyState}>No flashbacks found yet. Try adding positive entries from last week, last month, or last year.</p>
            ) : (
                <div className={styles.memories}>
                    {flashbacks.map((flashback) => (
                        <section
                            key={`${flashback.entry_id}-${flashback.date}`}
                            className={styles.memoryItem}
                            onClick={() => onFlashbackClick?.(flashback.raw || flashback)}
                            role="button"
                            tabIndex={0}
                            onKeyPress={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    onFlashbackClick?.(flashback.raw || flashback);
                                }
                            }}
                        >
                            <div className={styles.memoryHeader}>
                                <h3 className={styles.title}>{formatDateTime(flashback.date)}</h3>
                            </div>
                            <p className={styles.summary}>{flashback.summary}</p>
                            <small className={styles.date}>{flashback.label}</small>
                            <div className={styles.action}>Open this memory in Insights</div>
                        </section>
                    ))}
                </div>
            )}
        </article>
    );
}
