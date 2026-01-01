import React, { useEffect, useState } from 'react';
import { Card } from '../../components/common';
import { projectsApi, clustersApi, targetsApi, jdkApi } from '../../services/api';
import styles from './Dashboard.module.css';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState([
    { label: 'Total Projects', value: '0', icon: '📦' },
    { label: 'Total Clusters', value: '0', icon: '🏢' },
    { label: 'Total Targets', value: '0', icon: '🎯' },
    { label: 'JDK Versions', value: '0', icon: '☕' },
  ]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [projects, clusters, targets, jdkVersions] = await Promise.all([
        projectsApi.list().catch(() => []),
        clustersApi.list().catch(() => []),
        targetsApi.list().catch(() => []),
        jdkApi.list().catch(() => []),
      ]);

      setStats([
        { label: 'Total Projects', value: String(projects.length), icon: '📦' },
        { label: 'Total Clusters', value: String(clusters.length), icon: '🏢' },
        { label: 'Total Targets', value: String(targets.length), icon: '🎯' },
        { label: 'JDK Versions', value: String(jdkVersions.length), icon: '☕' },
      ]);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.dashboard}>
      <div className={styles.welcome}>
        <h1>Welcome to JDK Compliance Scanner</h1>
        <p>Monitor and manage JDK compliance across your infrastructure</p>
      </div>

      {loading ? (
        <div className={styles.loading}>Loading dashboard data...</div>
      ) : (
        <div className={styles.statsGrid}>
          {stats.map((stat) => (
            <Card key={stat.label} className={styles.statCard}>
              <div className={styles.statIcon}>{stat.icon}</div>
              <div className={styles.statContent}>
                <div className={styles.statValue}>{stat.value}</div>
                <div className={styles.statLabel}>{stat.label}</div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <div className={styles.sections}>
        <Card className={styles.sectionCard}>
          <h2>Quick Actions</h2>
          <div className={styles.actions}>
            <button className={styles.actionButton}>
              <span>🔍</span>
              <span>Run Scan</span>
            </button>
            <button className={styles.actionButton}>
              <span>📊</span>
              <span>View Reports</span>
            </button>
            <button className={styles.actionButton}>
              <span>⚙️</span>
              <span>Configure</span>
            </button>
          </div>
        </Card>

        <Card className={styles.sectionCard}>
          <h2>Recent Activity</h2>
          <div className={styles.activity}>
            <p className={styles.emptyState}>No recent activity</p>
          </div>
        </Card>
      </div>
    </div>
  );
};

