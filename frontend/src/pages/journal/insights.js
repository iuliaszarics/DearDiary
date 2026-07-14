import React, { useState, useMemo, useEffect } from 'react';
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

export default function InsightsView({ result, history = [], isHistoryLoading, historyError, onDelete, onClearResult, dateFilter, onDateFilterChange }) {
    const [selectedDate, setSelectedDate] = useState(dateFilter || '');
    useEffect(() => {
        if (dateFilter !== undefined) {
            setSelectedDate(dateFilter || '');
        }
    }, [dateFilter]);
    const handleDateChange = (e) => {
        const val = e.target.value;
        setSelectedDate(val);
        if (onDateFilterChange) {
            onDateFilterChange(val);
        }
    };
    const handleClearDate = () => {
        setSelectedDate('');
        if (onDateFilterChange) {
            onDateFilterChange('');
        }
    };
    const filteredHistory = useMemo(() => {
        if (!selectedDate) return history;
        return history.filter(item => {
            const itemDate = new Date(item.occured_at).toISOString().split('T')[0];
            return itemDate === selectedDate;
        });
    }, [history, selectedDate]);

    const renderHistoryItem = (item) => {
        if (!item) return null;
        return (
            <article key={item.entry_id} className={styles.historyItem}>
                <div className={styles.historyItemHeader}>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
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
                <div className={styles.resultContent}>
                    <div className={styles.subsection}>
                        <h3>Your entry</h3>
                        <p className={styles.resultText}>{item.text}</p>
                    </div>
                    <p className={styles.resultHeadline}>{item?.insight?.title}</p>
                    <p className={styles.resultText}>{item?.insight?.explanation}</p>
                    {Array.isArray(item?.advice) && item.advice.length > 0 && (
                        <div className={styles.subsection}>
                            <h3>Personalized advice</h3>
                            <div className={styles.adviceList}>
                                {item.advice.map((advice) => (
                                    <article className={styles.adviceCard} key={`${item.entry_id}-${advice.advice_key}`}>
                                        <h4>{advice.title}</h4>
                                        <p>{advice.advice_text}</p>
                                    </article>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </article>
        );
    };

    const disclaimerCard = (
        <article className={styles.disclaimerCard}>
            This application is designed for self-reflection and personal insight. It does not replace professional medical advice, diagnosis, treatment, psychotherapy, or other mental health services. If you are experiencing distress or a mental health crisis, please consult a qualified healthcare professional or reach out to local support services.
        </article>
    );

    return (
        <section className={styles.stackedSection}>
            {result && (
                <article className={styles.card}>
                    <div className={styles.sectionHeader}>
                        <h2>New Insight</h2>
                        {onClearResult && (
                            <button className={styles.closeButton} onClick={onClearResult} aria-label="Dismiss insight">
                                ✕ Dismiss
                            </button>
                        )}
                    </div>
                    <div className={styles.resultContent}>
                        <div className={styles.subsection}>
                            <h3>Your entry</h3>
                            <p className={styles.resultText}>{result.text}</p>
                        </div>
                        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                            <p className={styles.resultHeadline}>{result?.insight?.title || 'Analysis complete'}</p>
                            {result.predicted_emotion && (
                                <span className={styles.emotionPill}>{result.predicted_emotion}</span>
                            )}
                        </div>
                        <p className={styles.resultText}>{result?.insight?.explanation}</p>
                        <div className={styles.subsection}>
                            <h3>Personalized advice</h3>
                            <div className={styles.adviceList}>
                                {Array.isArray(result?.advice) && result.advice.length > 0 ? (
                                    result.advice.map((item) => (
                                        <article className={styles.adviceCard} key={item.advice_key}>
                                            <h4>{item.title}</h4>
                                            <p>{item.advice_text}</p>
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

            {result && disclaimerCard}

            <article className={styles.card}>
                <div className={styles.sectionHeader} style={{ flexWrap: 'wrap' }}>
                    <h2>Past Insights</h2>
                    <div className={styles.filterControls}>
                        <label className={styles.dateLabel}>Filter by Date:</label>
                        <input
                            type="date"
                            value={selectedDate}
                            onChange={handleDateChange}
                            className={styles.datePicker}
                        />
                        {selectedDate && (
                            <button className={styles.clearFilterBtn} onClick={handleClearDate}>
                                Clear
                            </button>
                        )}
                    </div>
                </div>
                {isHistoryLoading ? (
                    <p className={styles.emptyState}>Loading past insights...</p>
                ) : historyError ? (
                    <p className={styles.emptyState}>{historyError}</p>
                ) : filteredHistory.length === 0 ? (
                    <p className={styles.emptyState}>
                        {selectedDate
                            ? "No insights found for this date."
                            : "Analyze an entry from your Diary to generate your first insight."}
                    </p>
                ) : (
                    <div className={styles.historyList}>
                        {!result ? (
                            <>
                                {renderHistoryItem(filteredHistory[0])}
                                {disclaimerCard}
                                {filteredHistory.slice(1).map((item) => renderHistoryItem(item))}
                            </>
                        ) : (
                            filteredHistory.map((item) => renderHistoryItem(item))
                        )}
                    </div>
                )}
            </article>
        </section>
    );
}
