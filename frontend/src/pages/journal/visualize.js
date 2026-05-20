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

  const fluctuationData = (fluctuation || []).map(item => {
    const date = new Date(item.timestamp);
    return {
      time: date.toLocaleString('default', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
      score: item.score
    };
  });

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
          <h3 className={styles.chartTitle}>Emotion Fluctuation Over Time</h3>
          {fluctuationData.length > 0 ? (
            <div className={styles.chartWrapper}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={fluctuationData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
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
              </ResponsiveContainer>
            </div>
          ) : (
            <p className={styles.emptyText}>No fluctuation data available yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
