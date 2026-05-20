import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { API_URL } from '../../config';
import styles from './entry.module.css';

export default function EntryView({ userId, text, setText, onAnalyze, isAnalyzing }) {
    const [idleState, setIdleState] = useState('active'); 
    const [prompts, setPrompts] = useState([]);
    const [isLoadingPrompts, setIsLoadingPrompts] = useState(false);
    
    const idleTimer = useRef(null);
    const IDLE_TIME = 30000; 

    const fetchPrompts = useCallback(async () => {
        setIsLoadingPrompts(true);
        try {
            const res = await axios.get(`${API_URL}/prompts`, { params: { user_id: userId } });
            setPrompts(res.data.prompts || []);
            setIdleState('showing');
        } catch (err) {
            console.error("Failed to load prompts", err);
            setIdleState('active');
        } finally {
            setIsLoadingPrompts(false);
        }
    }, [userId]);

    const resetIdleTimer = useCallback(() => {
        if (idleTimer.current) clearTimeout(idleTimer.current);
        if (idleState === 'offered') {
            setIdleState('active');
        }
        
        idleTimer.current = setTimeout(() => {

            if (text.length < 50 && idleState !== 'showing') {
                setIdleState('offered');
            }
        }, IDLE_TIME);
    }, [text, idleState]);

    useEffect(() => {
        resetIdleTimer();
        return () => {
            if (idleTimer.current) clearTimeout(idleTimer.current);
        };
    }, [text, resetIdleTimer]);

    const handleAcceptOffer = () => {
        fetchPrompts();
    };

    const handleRejectOffer = () => {
        setIdleState('active');
    };
    
    const handleManualInspiration = () => {
        fetchPrompts();
    };

    const handlePromptClick = (prompt) => {
        const separator = text.trim() ? '\n\n' : '';
        setText(text + separator + prompt + ' ');
        setIdleState('active'); 
    };

    return (
        <div className={styles.entryView}>
            <section className={styles.card}>
            
                <div className={styles.headerArea}>
                    {idleState === 'active' && (
                        <button className={styles.inspirationButton} onClick={handleManualInspiration}>
                             Get Inspiration
                        </button>
                    )}
                    
                    {idleState === 'offered' && (
                        <div className={styles.offerBanner}>
                            <span className={styles.offerText}>You seem a bit stuck. Need some inspiration?</span>
                            <div className={styles.offerActions}>
                                <button className={styles.offerBtnYes} onClick={handleAcceptOffer}>Yes, please!</button>
                                <button className={styles.offerBtnNo} onClick={handleRejectOffer}>No, I'm thinking.</button>
                            </div>
                        </div>
                    )}

                    {idleState === 'showing' && (
                        <div className={styles.promptListContainer}>
                            <div className={styles.promptListHeader}>
                                <span>Try writing about:</span>
                                <button className={styles.closePromptsBtn} onClick={() => setIdleState('active')}>✕</button>
                            </div>
                            {isLoadingPrompts ? (
                                <p className={styles.loadingText}>Fetching ideas...</p>
                            ) : (
                                <div className={styles.promptChips}>
                                    {prompts.map((p, idx) => (
                                        <button key={idx} className={styles.promptChip} onClick={() => handlePromptClick(p)}>
                                            {p}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <textarea
                    className={styles.input}
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    placeholder="Dear Diary, "
                    rows={14}
                />
                <div className={styles.actionsRow}>
                    <button className={styles.button} onClick={onAnalyze} disabled={isAnalyzing}>
                        {isAnalyzing ? 'Saving...' : 'Save Entry'}
                    </button>
                </div>
            </section>
        </div>
    );
}