import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import styles from './Configuration.module.css';

const configTabs = [
  { path: '/configuration/clusters', label: 'Clusters', icon: '🏢' },
  { path: '/configuration/projects', label: 'Projects', icon: '📦' },
  { path: '/configuration/targets', label: 'Targets', icon: '🎯' },
  { path: '/configuration/jdk-versions', label: 'JDK Versions', icon: '☕' },
];

export const Configuration: React.FC = () => {
  const location = useLocation();

  return (
    <div className={styles.configuration}>
      <div className={styles.header}>
        <h1>Configuration</h1>
        <p>Manage clusters, projects, targets, and JDK versions</p>
      </div>
      <div className={styles.tabs}>
        {configTabs.map((tab) => (
          <Link
            key={tab.path}
            to={tab.path}
            className={`${styles.tab} ${
              location.pathname === tab.path ? styles.tabActive : ''
            }`}
          >
            <span className={styles.tabIcon}>{tab.icon}</span>
            <span className={styles.tabLabel}>{tab.label}</span>
          </Link>
        ))}
      </div>
      <div className={styles.content}>
        <Outlet />
      </div>
    </div>
  );
};

