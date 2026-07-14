import React from 'react';
import styles from './entry.module.css';

export default function EntryView({ text, setText, onAnalyze, isAnalyzing }) {
    return (
        <div className={styles.entryView}>
            <section className={styles.card}>
                <textarea
                    className={styles.input}
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    placeholder="Dear Diary, "
                    rows={14}
                />
                <div className={styles.actionsContainer}>
                    <button className={styles.button} onClick={onAnalyze} disabled={isAnalyzing}>
                        {isAnalyzing ? 'Saving...' : 'Save'}
                    </button>
                </div>
            </section>
        </div>
    );
}
