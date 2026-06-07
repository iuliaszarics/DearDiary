import React from 'react';
import styles from './insights.module.css';

function formatDateTime(value) {
    if (!value) {
        return 'Unknown time';
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return value;
    }
    return parsed.toLocaleString();
}

export default function InsightsView({ result, history = [], isHistoryLoading, historyError, onDelete }) {
    return (
        <section className={styles.stackedSection}>
            {result && (
                <article className={styles.card}>
                    <div className={styles.sectionHeader}>
                        <h2>New Insight</h2>
                    </div>

                    <div className={styles.resultContent}>
                        <div className={styles.subsection}>
                            <h3>Your entry</h3>
                            <p className={styles.resultText}>{result.text}</p>
                        </div>
                        <p className={styles.resultHeadline}>{result?.insight?.title || 'Analysis complete'}</p>
                        <p className={styles.resultText}>{result?.insight?.explanation}</p>

                        <div className={styles.subsection}>
                            <h3>Personalized advice</h3>
                            <div className={styles.adviceList}>
                                {Array.isArray(result?.advice) && result.advice.length > 0 ? (
                                    result.advice.map((item) => (
                                        <article className={styles.adviceCard} key={item.advice_key}>
                                            <h4>{item.title}</h4>
                                            <p>{item.advice_text}</p>
                                            {item.rationale_text && <small>{item.rationale_text}</small>}
                                        </article>
                                    ))
                                ) : (
                                    <p className={styles.emptyState}>No advice available yet.</p>
                                )}
                            </div>
                        </div>
                    </div>
                </article>
            )}

            <article className={styles.card}>
                <div className={styles.sectionHeader}>
                    <h2>Past Insights</h2>
                </div>
                
                {isHistoryLoading ? (
                    <p className={styles.emptyState}>Loading past insights...</p>
                ) : historyError ? (
                    <p className={styles.emptyState}>{historyError}</p>
                ) : history.length === 0 ? (
                    <p className={styles.emptyState}>Analyze an entry from your Diary to generate your first insight.</p>
                ) : (
                    <div className={styles.historyList}>
                        {history.map((item) => (
                            <article key={item.entry_id} className={styles.historyItem}>
                                <div className={styles.historyItemHeader}>
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                        <span className={styles.historyDate}>{formatDateTime(item.occured_at)}</span>
                                        <span className={styles.emotionPill}>{item.predicted_emotion}</span>
                                    </div>
                                    {onDelete && (
                                        <button
                                            className={styles.deleteButton}
                                            onClick={() => onDelete(item.entry_id)}
                                            aria-label="Delete entry"
                                        >
                                            Delete
                                        </button>
                                    )}
                                </div>
                                <p className={styles.historyInsightTitle}>{item?.insight?.title}</p>
                                <p className={styles.historyInsightBody}>{item?.insight?.explanation}</p>

                                {Array.isArray(item?.advice) && item.advice.length > 0 && (
                                    <div className={styles.adviceList}>
                                        {item.advice.map((advice) => (
                                            <div className={styles.adviceCard} key={`${item.entry_id}-${advice.advice_key}`}>
                                                <h4>{advice.title}</h4>
                                                <p>{advice.advice_text}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </article>
                        ))}
                    </div>
                )}
            </article>
        </section>
    );
}