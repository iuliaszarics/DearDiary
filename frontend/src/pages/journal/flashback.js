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
    const entry = new Date(entryDate);
    const today = new Date();

    const oneWeekAgo = new Date(today);
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

    if (isSameDate(entry, oneWeekAgo)) {
        return '1 week ago today';
    }

    const oneMonthAgo = new Date(today);
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

    if (isSameDate(entry, oneMonthAgo)) {
        return '1 month ago today';
    }

    const oneYearAgo = new Date(today);
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);

    if (isSameDate(entry, oneYearAgo)) {
        return '1 year ago today';
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