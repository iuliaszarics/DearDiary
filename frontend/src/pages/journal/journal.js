import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { API_URL } from '../../config';
import styles from './journal.module.css';
import EntryView from './entry';
import InsightsView from './insights';
import FlashbackView from './flashback';
import CalendarView from './calendar';
import HistoryView from './history';
import HappyMemoriesCollection from './happyMemoriesCollection';
import VisualizeView from './visualize';

const VIEW_HOME = 'home';
const VIEW_FLASHBACKS = 'flashbacks';
const VIEW_CALENDAR = 'calendar';
const VIEW_DAY_DETAILS = 'day_details';
const VIEW_HAPPY_MEMORIES = 'happy_memories';
const VIEW_DIARY = 'diary';
const VIEW_VISUALIZE = 'visualize';

function toMonthInputValue(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return `${year}-${month}`;
}

function splitMonthValue(monthValue) {
    const [year, month] = monthValue.split('-').map(Number);
    return { year, month };
}

export default function Journal({ userId }) {
    const [text, setText] = useState('');
    const [result, setResult] = useState(null);
    const [selectedMonth, setSelectedMonth] = useState(toMonthInputValue(new Date()));
    const [activeView, setActiveView] = useState(VIEW_HOME);
    const [calendar, setCalendar] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isCalendarLoading, setIsCalendarLoading] = useState(false);
    const [calendarError, setCalendarError] = useState('');
    const [history, setHistory] = useState([]);
    const [isHistoryLoading, setIsHistoryLoading] = useState(false);
    const [historyError, setHistoryError] = useState('');
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [selectedDayEntries, setSelectedDayEntries] = useState([]);
    const [selectedDayDate, setSelectedDayDate] = useState('');
    const [isDayEntriesLoading, setIsDayEntriesLoading] = useState(false);
    const [dayEntriesError, setDayEntriesError] = useState('');


    const loadDayEntries = useCallback(async (date) => {
        if (!userId) {
            return;
        }
        setIsDayEntriesLoading(true);
        setDayEntriesError('');
        try {
            const response = await axios.get(`${API_URL}/history`, {
                params: {
                    user_id: userId,
                    limit: 100,
                    offset: 0,
                    date: date,
                },
            });
            setSelectedDayEntries(response.data?.items || []);
            setSelectedDayDate(date);
            setActiveView(VIEW_DAY_DETAILS);
        } catch (error) {
            setDayEntriesError('The entries could not be loaded right now.');
        } finally {
            setIsDayEntriesLoading(false);
        }
    }, [userId]);



    const loadCalendar = useCallback(async (monthValue) => {
        if (!userId) {
            return;
        }

        const { year, month } = splitMonthValue(monthValue);
        setIsCalendarLoading(true);
        setCalendarError('');

        try {
            const response = await axios.get(`${API_URL}/calendar`, {
                params: {
                    user_id: userId,
                    year,
                    month,
                },
            });
            setCalendar(response.data);
        } catch (error) {
            setCalendarError('The calendar could not be loaded right now.');
        } finally {
            setIsCalendarLoading(false);
        }
    }, [userId]);

    useEffect(() => {
        loadCalendar(selectedMonth);
    }, [loadCalendar, selectedMonth]);

    const loadHistory = useCallback(async () => {
        if (!userId) {
            return;
        }
        setIsHistoryLoading(true);
        setHistoryError('');
        try {
            const response = await axios.get(`${API_URL}/history`, {
                params: {
                    user_id: userId,
                    limit: 100,
                    offset: 0,
                },
            });
            setHistory(response.data?.items || []);
        } catch (error) {
            setHistoryError('The history could not be loaded right now.');
        } finally {
            setIsHistoryLoading(false);
        }
    }, [userId]);

    useEffect(() => {
        loadHistory();
    }, [loadHistory]);

    const deleteEntry = useCallback(async (entryId) => {
        if (!window.confirm('Are you sure you want to delete this entry?')) return;
        try {
            await axios.delete(`${API_URL}/history/${entryId}`, { params: { user_id: userId } });
            
            if (result && result.entry_id === entryId) {
                setResult(null);
            }

            await loadHistory();
            await loadCalendar(selectedMonth);
            if (activeView === VIEW_DAY_DETAILS) {
                await loadDayEntries(selectedDayDate);
            }
        } catch (error) {
            alert('Failed to delete the entry. Please try again.');
        }
    }, [userId, loadHistory, loadCalendar, selectedMonth, activeView, loadDayEntries, selectedDayDate, result]);

    const analyze = async () => {
        if (!text.trim()) {
            return;
        }

        setIsAnalyzing(true);

        try {
            const response = await axios.post(`${API_URL}/analyze`, { user_id: userId, text });
            const analysisResult = response.data?.analysis ?? response.data;
            setResult(analysisResult);
            setText('');
            await loadCalendar(selectedMonth);
            await loadHistory();
            setActiveView(VIEW_HOME);
        } catch (error) {
            alert('Analysis failed. Please try again.');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const calendarCells = useMemo(() => {
        if (!calendar?.days?.length) {
            return [];
        }

        const firstDay = new Date(`${calendar.days[0].date}T00:00:00`);
        const blanks = Array.from({ length: firstDay.getDay() }, (_, index) => ({
            empty: true,
            key: `blank-${index}`,
        }));

        return [...blanks, ...calendar.days];
    }, [calendar]);

    const handleFlashbackClick = useCallback((flashback) => {
        setResult(flashback);
        setActiveView(VIEW_HOME);
    }, []);

    const handleMemoryClick = useCallback((memory) => {
        if (!memory) {
            return;
        }
        setResult(memory);
        setActiveView(VIEW_HOME);
    }, []);

    return (
        <div className={styles.page}>
            <div className={styles.wordmark}>Dear Diary,</div>
            <div className={`${styles.appShell} ${sidebarCollapsed ? styles.appShellCollapsed : ''}`}>
                <aside className={`${styles.sidebar} ${sidebarCollapsed ? styles.sidebarCollapsed : ''}`}>
                    <button
                        className={styles.sidebarToggle}
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                    >
                        ☰
                    </button>
                    <nav className={styles.navList}>
                        <button
                            className={`${styles.navButton} ${activeView === VIEW_HOME ? styles.navButtonActive : ''}`}
                            onClick={() => setActiveView(VIEW_HOME)}
                        >
                            <span className={styles.navButtonIcon}>H</span>
                            {!sidebarCollapsed && <span>Home</span>}
                        </button>
                        <button
                            className={`${styles.navButton} ${activeView === VIEW_DIARY ? styles.navButtonActive : ''}`}
                            onClick={() => setActiveView(VIEW_DIARY)}
                        >
                            <span className={styles.navButtonIcon}>D</span>
                            {!sidebarCollapsed && <span>Diary</span>}
                        </button>
                        <button
                            className={`${styles.navButton} ${activeView === VIEW_FLASHBACKS ? styles.navButtonActive : ''}`}
                            onClick={() => setActiveView(VIEW_FLASHBACKS)}
                        >
                            <span className={styles.navButtonIcon}>F</span>
                            {!sidebarCollapsed && <span>Flashbacks</span>}
                        </button>
                        <button
                            className={`${styles.navButton} ${activeView === VIEW_HAPPY_MEMORIES ? styles.navButtonActive : ''}`}
                            onClick={() => setActiveView(VIEW_HAPPY_MEMORIES)}
                        >
                            <span className={styles.navButtonIcon}>H</span>
                            {!sidebarCollapsed && <span>Happy Memories</span>}
                        </button>
                        <button
                            className={`${styles.navButton} ${activeView === VIEW_CALENDAR ? styles.navButtonActive : ''}`}
                            onClick={() => setActiveView(VIEW_CALENDAR)}
                        >
                            <span className={styles.navButtonIcon}>C</span>
                            {!sidebarCollapsed && <span>Calendar</span>}
                        </button>
                        <button
                            className={`${styles.navButton} ${activeView === VIEW_VISUALIZE ? styles.navButtonActive : ''}`}
                            onClick={() => setActiveView(VIEW_VISUALIZE)}
                        >
                            <span className={styles.navButtonIcon}>V</span>
                            {!sidebarCollapsed && <span>Visualize</span>}
                        </button>
                        {activeView === VIEW_DAY_DETAILS && (
                            <button
                                className={`${styles.navButton} ${styles.navButtonActive}`}
                                onClick={() => setActiveView(VIEW_DAY_DETAILS)}
                            >
                                <span className={styles.navButtonIcon}>D</span>
                                {!sidebarCollapsed && <span>{selectedDayDate}</span>}
                            </button>
                        )}
                        <button
                            className={styles.navButton}
                            onClick={() => {
                                window.location.href = '/login';
                            }}
                            style={{ marginTop: 'auto' }}
                        >
                            <span className={styles.navButtonIcon}>L</span>
                            {!sidebarCollapsed && <span>Logout</span>}
                        </button>
                    </nav>
                </aside>

                <main className={styles.contentPane}>
                    {activeView === VIEW_HOME && (
                        <InsightsView
                            result={result}
                            history={history}
                            isHistoryLoading={isHistoryLoading}
                            historyError={historyError}
                            onDelete={deleteEntry}
                        />
                    )}

                    {activeView === VIEW_DIARY && (
                        <div style={{ width: '100%', maxWidth: '900px', margin: '0 auto' }}>
                            <div className={styles.sectionHeader}>
                                <h2>Your Diary</h2>
                            </div>
                            <HistoryView
                                history={history}
                                isHistoryLoading={isHistoryLoading}
                                historyError={historyError}
                                onDelete={deleteEntry}
                                userId={userId}
                                text={text}
                                setText={setText}
                                onAnalyze={analyze}
                                isAnalyzing={isAnalyzing}
                            />
                        </div>
                    )}

                    {activeView === VIEW_FLASHBACKS && (
                        <FlashbackView history={history} onFlashbackClick={handleFlashbackClick} />
                    )}

                    {activeView === VIEW_CALENDAR && (
                        <CalendarView
                            calendar={calendar}
                            selectedMonth={selectedMonth}
                            setSelectedMonth={setSelectedMonth}
                            calendarCells={calendarCells}
                            isCalendarLoading={isCalendarLoading}
                            calendarError={calendarError}
                            onDayClick={loadDayEntries}
                        />
                    )}

                    {activeView === VIEW_DAY_DETAILS && (
                        <div style={{ width: '100%', maxWidth: '900px', margin: '0 auto' }}>
                            <div className={styles.sectionHeader}>
                                <h2>Entries for {selectedDayDate}</h2>
                                <button className={styles.analyzeButton} onClick={() => setActiveView(VIEW_CALENDAR)}>
                                    Back to Calendar
                                </button>
                            </div>
                            <HistoryView
                                history={selectedDayEntries}
                                isHistoryLoading={isDayEntriesLoading}
                                historyError={dayEntriesError}
                                onDelete={deleteEntry}
                            />
                        </div>
                    )}

                    {activeView === VIEW_HAPPY_MEMORIES && (
                        <HappyMemoriesCollection history={history} onMemoryClick={handleMemoryClick} />
                    )}

                    {activeView === VIEW_VISUALIZE && (
                        <VisualizeView userId={userId} />
                    )}
                </main>
            </div>
        </div>
    );

}