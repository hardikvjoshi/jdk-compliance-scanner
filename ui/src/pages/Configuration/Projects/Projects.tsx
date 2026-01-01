import React, { useEffect, useState } from 'react';
import { projectsApi } from '../../../services/api';
import { Project } from '../../../types';
import { Card, Button, Badge } from '../../../components/common';
import styles from './Projects.module.css';

export const Projects: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await projectsApi.list();
      setProjects(data);
    } catch (err: any) {
      setError(err.detail || 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading projects...</div>;
  }

  return (
    <div className={styles.projects}>
      <div className={styles.header}>
        <h2>Projects</h2>
        <Button onClick={() => alert('Project creation form coming soon')}>
          + Add Project
        </Button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.list}>
        {projects.length === 0 ? (
          <Card className={styles.empty}>
            <p>No projects found. Create your first project to get started.</p>
          </Card>
        ) : (
          projects.map((project) => (
            <Card key={project.id} className={styles.projectCard}>
              <div className={styles.projectHeader}>
                <h3>{project.project_name}</h3>
                <div className={styles.badges}>
                  <Badge variant={project.status === 'Active' ? 'success' : 'neutral'}>
                    {project.status}
                  </Badge>
                  <Badge variant="info">{project.tier}</Badge>
                </div>
              </div>
              <div className={styles.projectDetails}>
                <div><strong>Cluster:</strong> {project.cluster_name}</div>
                <div><strong>Technology:</strong> {project.technology}</div>
                <div><strong>Tribe:</strong> {project.tribe}</div>
                {project.console_url && (
                  <div>
                    <strong>Console:</strong>{' '}
                    <a href={project.console_url} target="_blank" rel="noopener noreferrer">
                      {project.console_url}
                    </a>
                  </div>
                )}
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

