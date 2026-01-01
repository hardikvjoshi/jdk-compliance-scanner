import React, { useState } from 'react';
import { Card, Button, Badge } from '../../components/common';
import { projectsApi } from '../../services/api';
import { Project } from '../../types';
import styles from './Scanner.module.css';

export const Scanner: React.FC = () => {
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);

  React.useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await projectsApi.list();
      setProjects(data.filter(p => p.status === 'Active'));
    } catch (err: any) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    if (selectedProjects.length === 0) {
      alert('Please select at least one project to scan');
      return;
    }
    setScanning(true);
    // TODO: Implement scan API call
    setTimeout(() => {
      setScanning(false);
      alert(`Scan initiated for ${selectedProjects.length} project(s). This feature will be available soon.`);
    }, 1000);
  };

  const toggleProject = (id: number) => {
    setSelectedProjects(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

  return (
    <div className={styles.scanner}>
      <div className={styles.header}>
        <h1>JDK Compliance Scanner</h1>
        <p>Select projects to scan for JDK compliance</p>
      </div>

      <Card className={styles.scanCard}>
        <div className={styles.scanHeader}>
          <h2>Run Scan</h2>
          <Button
            onClick={handleScan}
            disabled={scanning || selectedProjects.length === 0}
          >
            {scanning ? 'Scanning...' : `Scan ${selectedProjects.length} Project(s)`}
          </Button>
        </div>
        <div className={styles.scanInfo}>
          <p>Select one or more projects from the list below to scan for JDK compliance.</p>
        </div>
      </Card>

      <div className={styles.projectsSection}>
        <h2>Available Projects</h2>
        {loading ? (
          <div className={styles.loading}>Loading projects...</div>
        ) : projects.length === 0 ? (
          <Card className={styles.empty}>
            <p>No active projects found. Create projects in Configuration to scan them.</p>
          </Card>
        ) : (
          <div className={styles.projectsList}>
            {projects.map((project) => (
              <Card
                key={project.id}
                className={`${styles.projectCard} ${
                  selectedProjects.includes(project.id) ? styles.selected : ''
                }`}
                onClick={() => toggleProject(project.id)}
              >
                <div className={styles.projectCheckbox}>
                  <input
                    type="checkbox"
                    checked={selectedProjects.includes(project.id)}
                    onChange={() => toggleProject(project.id)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                <div className={styles.projectInfo}>
                  <h3>{project.project_name}</h3>
                  <div className={styles.projectMeta}>
                    <Badge variant="info">{project.tier}</Badge>
                    <Badge variant="neutral">{project.technology}</Badge>
                    <span>{project.cluster_name}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Card className={styles.jobsCard}>
        <h2>Recent Scan Jobs</h2>
        <div className={styles.jobsList}>
          <div className={styles.emptyState}>
            <p>No scan jobs yet. Run a scan to see results here.</p>
            <p className={styles.note}>Scan job tracking will be available soon.</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

