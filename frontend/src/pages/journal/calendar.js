import React from 'react';
import styles from './calendar.module.css';

const weekdayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function CalendarView({
    calendar,
    selectedMonth,
    setSelectedMonth,
    calendarCells,
    isCalendarLoading,
    calendarError,
    onDayClick,
}) {
    return (
        <article className={styles.card}>
            <div className={styles.header}>
                <div>
                    <h2>Calendar</h2>
                </div>
                <label className={styles.monthPickerWrap}>
                    <span>Month</span>
                    <input
                        className={styles.monthPicker}
                        type="month"
                        value={selectedMonth}
                        onChange={(event) => setSelectedMonth(event.target.value)}
                    />
                </label>
            </div>

            {calendar?.stats && (
                <div className={styles.calendarStats}>
                    <span>{calendar.stats.positive_days} positive days</span>
                    <span>{calendar.stats.neutral_days} neutral days</span>
                    <span>{calendar.stats.negative_days} negative days</span>
                </div>
            )}

            {isCalendarLoading ? (
                <p className={styles.emptyState}>Loading calendar...</p>
            ) : calendarError ? (
                <p className={styles.errorText}>{calendarError}</p>
            ) : (
                <div className={styles.calendarGridWrap}>
                    <div className={styles.weekdayRow}>
                        {weekdayLabels.map((label) => (
                            <div key={label} className={styles.weekdayCell}>
                                {label}
                            </div>
                        ))}
                    </div>

                    <div className={styles.calendarGrid}>
                        {calendarCells.map((day, index) =>
                            day.empty ? (
                                <div key={day.key || index} className={styles.calendarCellPlaceholder} />
                            ) : (
                                <article 
                                    key={day.date} 
                                    className={styles.calendarCell} 
                                    style={{ '--day-color': day.color }}
                                    onClick={() => onDayClick?.(day.date)}
                                >
                                    <span className={styles.calendarDayNumber}>{day.day}</span>
                                    <span className={styles.calendarEmotion}>{day.dominant_emotion}</span>
                                    {day.entry_count > 0 && <span className={styles.calendarCount}>{day.entry_count} entries</span>}
                                    <p className={styles.calendarSummary}>{day.summary_text}</p>
                                </article>
                            )
                        )}
                    </div>
                </div>
            )}
        </article>
    );
}