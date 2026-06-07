import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../../config';
import {
  PieChart, Pie, Cell, Tooltip as PieTooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as BarTooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine
} from 'recharts';
import styles from './visualize.module.css';

const EMOTION_COLORS = {
  positive: '#ffb3ba',
  negative: '#bae1ff',
  neutral: '#e2e2e2'
};

export default function VisualizeView({ userId }) {
  const [stats, setStats] = useState(null);
  const [fluctuation, setFluctuation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [timeRange, setTimeRange] = useState('all');
  const [pattern, setPattern] = useState('none');

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

  if (isLoading) {
    return <div className={styles.loading}>Loading charts...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  if (!stats) {
    return null;
  }

  // Format Emotion Data
  const emotionData = [
    { name: 'Positive', value: stats.emotion_distribution.positive || 0, color: EMOTION_COLORS.positive },
    { name: 'Negative', value: stats.emotion_distribution.negative || 0, color: EMOTION_COLORS.negative },
    { name: 'Neutral', value: stats.emotion_distribution.neutral || 0, color: EMOTION_COLORS.neutral }
  ].filter(item => item.value > 0);

  // Format Occurrences Data
  const occurrencesData = stats.writing_occurrences.map(item => {
    // Format "2026-05" to "May 2026"
    const [year, month] = item.month.split('-');
    const date = new Date(year, parseInt(month) - 1);
    const monthName = date.toLocaleString('default', { month: 'short' });
    return {
      name: `${monthName} ${year}`,
      Entries: item.count
    };
  });

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
  let isPatternChart = false;

  if (pattern === 'dayNight') {
    isPatternChart = true;
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
    isPatternChart = true;
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
      <h2 className={styles.header}>Your Journal in Numbers</h2>

      <div className={styles.chartsGrid}>
        <div className={styles.chartCard}>
          <h3 className={styles.chartTitle}>Emotion Distribution</h3>
          {emotionData.length > 0 ? (
            <div className={styles.chartWrapper}>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={emotionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {emotionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <PieTooltip />
                  <Legend verticalAlign="bottom" height={36}/>
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className={styles.emptyText}>No emotion data available yet.</p>
          )}
        </div>

        <div className={styles.chartCard}>
          <h3 className={styles.chartTitle}>Writing Occurrences</h3>
          {occurrencesData.length > 0 ? (
            <div className={styles.chartWrapper}>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={occurrencesData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                  <XAxis dataKey="name" tick={{fill: '#666'}} axisLine={false} tickLine={false} />
                  <YAxis tick={{fill: '#666'}} axisLine={false} tickLine={false} />
                  <BarTooltip cursor={{fill: '#f5f5f5'}} />
                  <Bar dataKey="Entries" fill="#a2d2ff" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className={styles.emptyText}>No writing data available yet.</p>
          )}
        </div>
        
        <div className={styles.chartCard} style={{ gridColumn: '1 / -1' }}>
          <div className={styles.filtersContainer}>
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
            <div className={styles.filterGroup}>
              <label className={styles.filterLabel}>Pattern View:</label>
              <select className={styles.filterSelect} value={pattern} onChange={e => setPattern(e.target.value)}>
                <option value="none">None (Timeline)</option>
                <option value="dayNight">Day vs Night</option>
                <option value="season">Seasons</option>
              </select>
            </div>
          </div>
          
          <h3 className={styles.chartTitle}>Emotion Fluctuation Over Time</h3>
          {chartData.length > 0 ? (
            <div className={styles.chartWrapper}>
              <ResponsiveContainer width="100%" height={300}>
                {isPatternChart ? (
                  <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                    <XAxis dataKey="name" tick={{fill: '#666'}} axisLine={false} tickLine={false} />
                    <YAxis tick={{fill: '#666'}} axisLine={false} tickLine={false} domain={[-1.2, 1.2]} ticks={[-1, 0, 1]} tickFormatter={(val) => {
                        if (val === 1) return 'Positive';
                        if (val === 0) return 'Neutral';
                        if (val === -1) return 'Negative';
                        return '';
                    }} />
                    <BarTooltip cursor={{fill: '#f5f5f5'}} formatter={(value) => [value.toFixed(2), "Avg Score"]} />
                    <ReferenceLine y={0} stroke="#e2e2e2" />
                    <Bar dataKey="score" fill="#ffb3ba" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.score >= 0 ? '#ffb3ba' : '#bae1ff'} />
                      ))}
                    </Bar>
                  </BarChart>
                ) : (
                  <LineChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                    <XAxis dataKey="time" tick={{fill: '#666'}} axisLine={false} tickLine={false} />
                    <YAxis tick={{fill: '#666'}} axisLine={false} tickLine={false} domain={[-1.2, 1.2]} ticks={[-1, 0, 1]} tickFormatter={(val) => {
                        if (val === 1) return 'Positive';
                        if (val === 0) return 'Neutral';
                        if (val === -1) return 'Negative';
                        return '';
                    }} />
                    <BarTooltip cursor={{fill: '#f5f5f5'}} />
                    <ReferenceLine y={0} stroke="#e2e2e2" />
                    <Line type="monotone" dataKey="score" stroke="#a2d2ff" strokeWidth={3} dot={{ r: 4, fill: '#a2d2ff' }} activeDot={{ r: 6 }} />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>
          ) : (
            <p className={styles.emptyText}>No fluctuation data available for this range.</p>
          )}
        </div>
      </div>
    </div>
  );
}
