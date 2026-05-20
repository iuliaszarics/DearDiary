import React, { useMemo } from 'react';
import styles from './happyMemoriesCollection.module.css';

function isPositiveEntry(item) {
    return item?.insight?.bucket === 'positive' || item?.predicted_emotion === 'positive';
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

export default function HappyMemoriesCollection({ history, onMemoryClick }) {
    const memories = useMemo(() => buildHappyMemories(history), [history]);

    return (
        <article className={styles.card}>
            <div className={styles.header}>
                <h2>Happy Memories Collection</h2>
                <p className={styles.subtitle}>All your positive moments in one place</p>
            </div>

            {memories.length === 0 ? (
                <p className={styles.emptyState}>No happy memories yet. Start journaling to collect positive moments!</p>
            ) : (
                <div className={styles.memoriesList}>
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
                                </div>
                                <p className={styles.summary}>{memory.summary}</p>
                                <small className={styles.date}>Open insight: {memory.title}</small>
                            </section>
                        ))}
                    </div>
                </div>
            )}
        </article>
    );
}
