import React, { useState, useEffect } from 'react';
import styles from './history.module.css';
import EntryView from './entry';

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

export default function HistoryView({ history, isHistoryLoading, historyError, onDelete, userId, text, setText, onAnalyze, isAnalyzing }) {
    const [currentPageIndex, setCurrentPageIndex] = useState(0);
    const [selectedDate, setSelectedDate] = useState('');
    const [emptyDateMessage, setEmptyDateMessage] = useState(null);

    useEffect(() => {
        if (selectedDate) {
            const today = new Date();
            const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
            
            if (selectedDate === todayStr) {
                setCurrentPageIndex(0);
                setEmptyDateMessage(null);
                return;
            }

            if (history.length > 0) {
                const index = history.findIndex(item => {
                    const itemDate = new Date(item.occured_at).toISOString().split('T')[0];
                    return itemDate === selectedDate;
                });
                if (index !== -1) {
                    setCurrentPageIndex(index + 1);
                    setEmptyDateMessage(null);
                } else {
                    setEmptyDateMessage(`You did not write in the diary on ${selectedDate}`);
                }
            } else {
                setEmptyDateMessage(`You did not write in the diary on ${selectedDate}`);
            }
        }
    }, [selectedDate, history]);

    const handleNext = () => {
        setEmptyDateMessage(null);
        if (currentPageIndex < history.length) {
            setCurrentPageIndex(prev => prev + 1);
        }
    };

    const handlePrev = () => {
        setEmptyDateMessage(null);
        if (currentPageIndex > 0) {
            setCurrentPageIndex(prev => prev - 1);
        }
    };

    if (isHistoryLoading) {
        return <p className={styles.emptyState}>Loading diary...</p>;
    }
    
    if (historyError) {
        return <p className={styles.errorText}>{historyError}</p>;
    }

    return (
        <div className={styles.bookContainer}>
            <div className={styles.controls}>
                <button onClick={handlePrev} disabled={currentPageIndex === 0} className={styles.navBtn}>
                    &larr; Newer
                </button>
                <input 
                    type="date" 
                    value={selectedDate} 
                    onChange={(e) => setSelectedDate(e.target.value)} 
                    className={styles.datePicker}
                />
                <button onClick={handleNext} disabled={currentPageIndex === history.length} className={styles.navBtn}>
                    Older &rarr;
                </button>
            </div>
            
            {emptyDateMessage ? (
                <div className={styles.pageCard}>
                    <div className={styles.pageHeader}>
                        <span className={styles.date}>{selectedDate}</span>
                    </div>
                    <div className={styles.pageContent}>
                        <p className={styles.text}>{emptyDateMessage}</p>
                    </div>
                </div>
            ) : currentPageIndex === 0 ? (
                <div className={styles.pageCard}>
                    <div className={styles.pageHeader}>
                        <span className={styles.date}>{new Date().toLocaleDateString()}</span>
                    </div>
                    <div className={styles.pageContent}>
                        <EntryView
                            userId={userId}
                            text={text}
                            setText={setText}
                            onAnalyze={onAnalyze}
                            isAnalyzing={isAnalyzing}
                        />
                    </div>
                </div>
            ) : (
                <div className={styles.pageCard} key={history[currentPageIndex - 1].entry_id}>
                    <div className={styles.pageHeader}>
                        <span className={styles.date}>{formatDateTime(history[currentPageIndex - 1].occured_at)}</span>
                        {onDelete && (
                            <button
                                className={styles.deleteButton}
                                onClick={() => {
                                    onDelete(history[currentPageIndex - 1].entry_id);
                                    if (currentPageIndex > 1) setCurrentPageIndex(currentPageIndex - 1);
                                    else if (history.length <= 1) setCurrentPageIndex(0);
                                }}
                                aria-label="Delete entry"
                            >
                                Delete
                            </button>
                        )}
                    </div>
                    <div className={styles.pageContent}>
                        <p className={styles.text}>{history[currentPageIndex - 1].text}</p>
                    </div>
                </div>
            )}
        </div>
    );
}