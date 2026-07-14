import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../../config';
import {
  Cell, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as BarTooltip, ResponsiveContainer,
  ReferenceLine, AreaChart, Area
} from 'recharts';
import styles from './visualize.module.css';
import InsightsView from './insights';

export default function VisualizeView({ userId, result, setResult, history = [], isHistoryLoading, historyError, onDelete, dateFilter, onDateFilterChange }) {
  const [stats, setStats] = useState(null);
  const [fluctuation, setFluctuation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [timeRange, setTimeRange] = useState('all');
  const [pattern, setPattern] = useState('none');
  const [activeSubTab, setActiveSubTab] = useState('insights');
  const [trendWindow, setTrendWindow] = useState('7');
  const daysOfWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const timesOfDay = ["Morning", "Afternoon", "Evening"];
  const getHeatmapColor = (score, count) => {
    if (count === 0 || score === null || score === undefined) return '#f4f4f7';
    if (score > 0.5) {
      const t = (score - 0.5) / 0.5;
      return `rgba(255, 179, 186, ${0.2 + t * 0.8})`;
    } else if (score < 0.5) {
      const t = (0.5 - score) / 0.5;
      return `rgba(186, 225, 255, ${0.2 + t * 0.8})`;
    } else {
      return '#e2e2e2';
    }
  };
  const heatmapLookup = React.useMemo(() => {
    const lookup = {};
    if (stats && stats.time_heatmap) {
      stats.time_heatmap.forEach(item => {
        lookup[`${item.day}-${item.time}`] = item;
      });
    }
    return lookup;
  }, [stats]);
  const computeMovingAverage = (data, windowSize) => {
    const result = [];
    for (let i = 0; i < data.length; i++) {
      let sum = 0;
      let count = 0;
      const start = Math.max(0, i - windowSize + 1);
      for (let j = start; j <= i; j++) {
        sum += data[j].score;
        count++;
      }
      const avg = count > 0 ? (sum / count) : 0;
      const dateObj = new Date(data[i].date);
      const dateStr = dateObj.toLocaleString('default', { month: 'short', day: 'numeric' });
      result.push({
        date: dateStr,
        score: parseFloat(avg.toFixed(2))
      });
    }
    return result;
  };
  const filteredDailyPositivity = React.useMemo(() => {
    if (!stats || !stats.daily_positivity) return [];
    const now = new Date();
    return stats.daily_positivity.filter(item => {
      const itemDate = new Date(item.date);
      if (timeRange === 'thisWeek') {
        const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        return itemDate >= oneWeekAgo;
      } else if (timeRange === 'lastWeek') {
        const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);
        const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        return itemDate >= twoWeeksAgo && itemDate < oneWeekAgo;
      } else if (timeRange === 'thisMonth') {
        const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        return itemDate >= oneMonthAgo;
      } else if (timeRange === 'thisYear') {
        const oneYearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        return itemDate >= oneYearAgo;
      }
      return true;
    });
  }, [stats, timeRange]);
  const filteredEntityImpact = React.useMemo(() => {
    if (!stats || !stats.entity_impact) return [];
    return stats.entity_impact.filter(item => item.positive > 0 || item.negative > 0 || item.neutral > 0);
  }, [stats]);
  const trendData = React.useMemo(() => {
    if (filteredDailyPositivity.length === 0) return [];
    const windowSize = parseInt(trendWindow);
    if (isNaN(windowSize) || windowSize <= 1) {
      return filteredDailyPositivity.map(item => {
        const dateObj = new Date(item.date);
        const dateStr = dateObj.toLocaleString('default', { month: 'short', day: 'numeric' });
        return {
          date: dateStr,
          score: item.score
        };
      });
    }
    return computeMovingAverage(filteredDailyPositivity, windowSize);
  }, [filteredDailyPositivity, trendWindow]);
  useEffect(() => {
    async function fetchStats() {
      if (!userId) return;
      setIsLoading(true);
      setError('');
      try {
        const response = await axios.get(`${API_URL}/stats`, { params: { user_id: userId } });
        setStats(response.data);
        const flucResponse = await axios.get(`${API_URL}/fluctuation`, { params: { user_id: userId } });
        setFluctuation(flucResponse.data.fluctuation);
      } catch (err) {
        setError('Failed to load visualization data.');
      } finally {
        setIsLoading(false);
      }
    }
    fetchStats();
  }, [userId]);
  useEffect(() => {
    if (result) {
      setActiveSubTab('insights');
    }
  }, [result]);
  const now = new Date();
  let filteredFluctuation = (fluctuation || []).filter(item => {
    const itemDate = new Date(item.timestamp);
    if (timeRange === 'thisWeek') {
      const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      return itemDate >= oneWeekAgo;
    } else if (timeRange === 'lastWeek') {
      const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);
      const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      return itemDate >= twoWeeksAgo && itemDate < oneWeekAgo;
    } else if (timeRange === 'thisMonth') {
      const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      return itemDate >= oneMonthAgo;
    } else if (timeRange === 'thisYear') {
      const oneYearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
      return itemDate >= oneYearAgo;
    }
    return true;
  });
  let chartData = [];
  if (pattern === 'dayNight') {
    let daySum = 0, dayCount = 0;
    let nightSum = 0, nightCount = 0;
    filteredFluctuation.forEach(item => {
      const date = new Date(item.timestamp);
      const hour = date.getHours();
      if (hour >= 6 && hour < 18) {
        daySum += item.score;
        dayCount++;
      } else {
        nightSum += item.score;
        nightCount++;
      }
    });
    chartData = [
      { name: 'Day', score: dayCount > 0 ? (daySum / dayCount) : 0 },
      { name: 'Night', score: nightCount > 0 ? (nightSum / nightCount) : 0 }
    ];
  } else if (pattern === 'season') {
    let sums = { Spring: 0, Summer: 0, Autumn: 0, Winter: 0 };
    let counts = { Spring: 0, Summer: 0, Autumn: 0, Winter: 0 };
    filteredFluctuation.forEach(item => {
      const date = new Date(item.timestamp);
      const month = date.getMonth() + 1;
      let season = '';
      if (month >= 3 && month <= 5) season = 'Spring';
      else if (month >= 6 && month <= 8) season = 'Summer';
      else if (month >= 9 && month <= 11) season = 'Autumn';
      else season = 'Winter';
      sums[season] += item.score;
      counts[season]++;
    });
    chartData = [
      { name: 'Spring', score: counts.Spring > 0 ? (sums.Spring / counts.Spring) : 0 },
      { name: 'Summer', score: counts.Summer > 0 ? (sums.Summer / counts.Summer) : 0 },
      { name: 'Autumn', score: counts.Autumn > 0 ? (sums.Autumn / counts.Autumn) : 0 },
      { name: 'Winter', score: counts.Winter > 0 ? (sums.Winter / counts.Winter) : 0 }
    ];
  } else {
    chartData = filteredFluctuation.map(item => {
      const date = new Date(item.timestamp);
      return {
        time: date.toLocaleString('default', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
        score: item.score
      };
    });
  }
  return (
    <div className={styles.container}>
      <h2 className={styles.header}>Visualize & Insights</h2>
      <div className={styles.subTabs}>
        <button
          className={`${styles.tabBtn} ${activeSubTab === 'insights' ? styles.tabBtnActive : ''}`}
          onClick={() => setActiveSubTab('insights')}
        >
          <span>Insights & Advice</span>
        </button>
        <button
          className={`${styles.tabBtn} ${activeSubTab === 'charts' ? styles.tabBtnActive : ''}`}
          onClick={() => setActiveSubTab('charts')}
        >
          <span>Charts & Trends</span>
        </button>
      </div>
      <div className={styles.tabContent}>
        {activeSubTab === 'charts' && (
          <>
            {isLoading ? (
              <div className={styles.loading}>Loading charts...</div>
            ) : error ? (
              <div className={styles.error}>{error}</div>
            ) : !stats ? (
              <div className={styles.error}>No visualization data available.</div>
            ) : (
              <div className={styles.chartsGrid}>
                <div className={styles.chartCard}>
                  <h3 className={styles.chartTitle}>Entity to Emotion</h3>
                  {filteredEntityImpact && filteredEntityImpact.length > 0 ? (
                    <div className={styles.chartWrapper}>
                      <ResponsiveContainer width="100%" height={400}>
                        <BarChart
                          layout="vertical"
                          data={filteredEntityImpact}
                          margin={{ top: 20, right: 30, left: 10, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#eee" />
                          <XAxis type="number" tick={{ fill: '#666' }} axisLine={false} tickLine={false} />
                          <YAxis dataKey="entity" type="category" tick={{ fill: '#666' }} axisLine={false} tickLine={false} width={80} interval={0} />
                          <BarTooltip cursor={{ fill: '#f5f5f5' }} />
                          <Legend />
                          <Bar dataKey="positive" name="Positive Mentions" fill="#ffb3ba" radius={[0, 4, 4, 0]} />
                          <Bar dataKey="negative" name="Negative Mentions" fill="#bae1ff" radius={[0, 4, 4, 0]} />
                          <Bar dataKey="neutral" name="Neutral Mentions" fill="#e2e2e2" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <p className={styles.emptyText}>No entity mention data available yet. Start mentioning people and places in your diary entries.</p>
                  )}
                </div>
                <div className={styles.chartCard}>
                  <h3 className={styles.chartTitle}>Day and Time</h3>
                  <div className={styles.heatmapWrapper}>
                    <div className={styles.heatmapGrid}>
                      <div className={styles.heatmapHeaderLabel}></div>
                      {daysOfWeek.map(day => (
                        <div key={day} className={styles.heatmapHeaderLabel}>{day}</div>
                      ))}
                      {timesOfDay.map(time => (
                        <React.Fragment key={time}>
                          <div className={styles.heatmapRowLabel}>{time}</div>
                          {daysOfWeek.map(day => {
                            const data = heatmapLookup[`${day}-${time}`] || { score: null, count: 0 };
                            const color = getHeatmapColor(data.score, data.count);
                            return (
                              <div
                                key={`${day}-${time}`}
                                className={styles.heatmapCell}
                                style={{ backgroundColor: color }}
                                title={data.count > 0 ? `${time} ${day}: Avg Positivity ${Math.round(data.score * 100)}% (${data.count} entries)` : `${time} ${day}: No entries`}
                              >
                                {data.count > 0 && <span className={styles.cellCount}>{data.count}</span>}
                              </div>
                            );
                          })}
                        </React.Fragment>
                      ))}
                    </div>
                    <div className={styles.heatmapLegend}>
                      <span className={styles.legendLabel}>Negative (0%)</span>
                      <div className={styles.legendColorBar}></div>
                      <span className={styles.legendLabel}>Positive (100%)</span>
                    </div>
                  </div>
                </div>
                <div className={styles.chartCard} style={{ gridColumn: '1 / -1' }}>
                  <div className={styles.filtersContainer} style={{ justifyContent: 'space-between', marginBottom: '1.2rem', gap: '15px', flexWrap: 'wrap' }}>
                    <h3 className={styles.chartTitle} style={{ margin: 0, textAlign: 'left' }}>Fluctuations</h3>
                    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                      <div className={styles.filterGroup}>
                        <label className={styles.filterLabel}>View Mode:</label>
                        <select className={styles.filterSelect} value={pattern} onChange={e => setPattern(e.target.value)}>
                          <option value="none">Positivity Timeline</option>
                          <option value="dayNight">Day vs Night</option>
                          <option value="season">Seasons</option>
                        </select>
                      </div>
                      <div className={styles.filterGroup}>
                        <label className={styles.filterLabel}>Time Range:</label>
                        <select className={styles.filterSelect} value={timeRange} onChange={e => setTimeRange(e.target.value)}>
                          <option value="all">All Time</option>
                          <option value="thisWeek">Past 7 Days</option>
                          <option value="lastWeek">Previous 7 Days</option>
                          <option value="thisMonth">Past 30 Days</option>
                          <option value="thisYear">Past Year</option>
                        </select>
                      </div>
                      {pattern === 'none' && (
                        <div className={styles.filterGroup}>
                          <label className={styles.filterLabel}>Smoothing:</label>
                          <select
                            className={styles.filterSelect}
                            value={trendWindow}
                            onChange={e => setTrendWindow(e.target.value)}
                          >
                            <option value="1">Daily Score (No Smoothing)</option>
                            <option value="7">7-Day Moving Average</option>
                            <option value="30">30-Day Moving Average</option>
                          </select>
                        </div>
                      )}
                    </div>
                  </div>
                  {pattern === 'none' ? (
                    trendData.length > 0 ? (
                      <div className={styles.chartWrapper}>
                        <ResponsiveContainer width="100%" height={300}>
                          <AreaChart data={trendData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                            <defs>
                              <linearGradient id="positivityGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ffb3ba" stopOpacity={0.6} />
                                <stop offset="95%" stopColor="#ffb3ba" stopOpacity={0.0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                            <XAxis dataKey="date" tick={false} axisLine={false} tickLine={false} />
                            <YAxis
                              tick={{ fill: '#666' }}
                              axisLine={false}
                              tickLine={false}
                              domain={[0, 1.0]}
                              ticks={[0, 0.25, 0.5, 0.75, 1.0]}
                              tickFormatter={(val) => `${Math.round(val * 100)}%`}
                            />
                            <BarTooltip formatter={(value) => [`${Math.round(value * 100)}%`, "Positivity Score"]} />
                            <ReferenceLine y={0.5} stroke="#e2e2e2" strokeDasharray="3 3" label={{ value: 'Neutral (50%)', fill: '#999', position: 'insideBottomLeft' }} />
                            <Area type="monotone" dataKey="score" stroke="#ffb3ba" strokeWidth={3} fillOpacity={1} fill="url(#positivityGrad)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <p className={styles.emptyText}>No daily entry summaries available. Start writing journal entries daily to build a long-term positivity trend.</p>
                    )
                  ) : (
                    chartData.length > 0 ? (
                      <div className={styles.chartWrapper}>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                            <XAxis dataKey="name" tick={{ fill: '#666' }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#666' }} axisLine={false} tickLine={false} domain={[-1.2, 1.2]} ticks={[-1, 0, 1]} tickFormatter={(val) => {
                              if (val === 1) return 'Positive';
                              if (val === 0) return 'Neutral';
                              if (val === -1) return 'Negative';
                              return '';
                            }} />
                            <BarTooltip cursor={{ fill: '#f5f5f5' }} formatter={(value) => [value.toFixed(2), "Avg Score"]} />
                            <ReferenceLine y={0} stroke="#e2e2e2" />
                            <Bar dataKey="score" fill="#ffb3ba" radius={[4, 4, 0, 0]}>
                              {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.score >= 0 ? '#ffb3ba' : '#bae1ff'} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <p className={styles.emptyText}>No fluctuation data available for this range.</p>
                    )
                  )}
                </div>
              </div>
            )}
          </>
        )}
        {activeSubTab === 'insights' && (
          <InsightsView
            result={result}
            history={history}
            isHistoryLoading={isHistoryLoading}
            historyError={historyError}
            onDelete={onDelete}
            onClearResult={() => setResult(null)}
            dateFilter={dateFilter}
            onDateFilterChange={onDateFilterChange}
          />
        )}
      </div>
    </div>
  );
}
