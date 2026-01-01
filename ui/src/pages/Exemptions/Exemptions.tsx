import React, { useState } from 'react';
import { Card, Button, Badge } from '../../components/common';
import { projectsApi } from '../../services/api';
import { Project } from '../../types';
import styles from './Exemptions.module.css';

export const Exemptions: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    project_id: '',
    application_name: '',
    jdk_version: '',
    exemption_reason: '',
    exemption_type: 'Temporary' as 'Temporary' | 'Permanent',
    start_date: '',
    end_date: '',
  });

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement exemption creation API
    alert('Exemption creation will be available soon.');
    setShowForm(false);
    setFormData({
      project_id: '',
      application_name: '',
      jdk_version: '',
      exemption_reason: '',
      exemption_type: 'Temporary',
      start_date: '',
      end_date: '',
    });
  };

  return (
    <div className={styles.exemptions}>
      <div className={styles.header}>
        <h1>Exemptions Management</h1>
        <p>Manage JDK compliance exemptions for applications</p>
      </div>

      <div className={styles.actions}>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Create Exemption'}
        </Button>
      </div>

      {showForm && (
        <Card className={styles.formCard}>
          <h2>Create New Exemption</h2>
          <form onSubmit={handleSubmit}>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>Project *</label>
                <select
                  value={formData.project_id}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  required
                >
                  <option value="">Select a project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.project_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className={styles.formGroup}>
                <label>Application Name *</label>
                <input
                  type="text"
                  value={formData.application_name}
                  onChange={(e) => setFormData({ ...formData, application_name: e.target.value })}
                  required
                  placeholder="e.g., my-app-service"
                />
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>JDK Version *</label>
                <input
                  type="text"
                  value={formData.jdk_version}
                  onChange={(e) => setFormData({ ...formData, jdk_version: e.target.value })}
                  required
                  placeholder="e.g., JDK 8"
                />
              </div>
              <div className={styles.formGroup}>
                <label>Exemption Type *</label>
                <select
                  value={formData.exemption_type}
                  onChange={(e) => setFormData({ ...formData, exemption_type: e.target.value as any })}
                  required
                >
                  <option value="Temporary">Temporary</option>
                  <option value="Permanent">Permanent</option>
                </select>
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>Start Date *</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  required
                />
              </div>
              {formData.exemption_type === 'Temporary' && (
                <div className={styles.formGroup}>
                  <label>End Date *</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    required
                  />
                </div>
              )}
            </div>
            <div className={styles.formGroup}>
              <label>Exemption Reason *</label>
              <textarea
                value={formData.exemption_reason}
                onChange={(e) => setFormData({ ...formData, exemption_reason: e.target.value })}
                required
                rows={4}
                placeholder="Explain why this exemption is needed..."
              />
            </div>
            <div className={styles.formActions}>
              <Button type="submit">Create Exemption</Button>
            </div>
          </form>
        </Card>
      )}

      <Card className={styles.exemptionsList}>
        <h2>Active Exemptions</h2>
        <div className={styles.list}>
          <div className={styles.emptyState}>
            <p>No exemptions found. Create an exemption to see it here.</p>
            <p className={styles.note}>
              Exemption management will be available soon.
            </p>
          </div>
        </div>
      </Card>

      <Card className={styles.statsCard}>
        <h2>Exemption Statistics</h2>
        <div className={styles.statsGrid}>
          <div className={styles.stat}>
            <div className={styles.statValue}>0</div>
            <div className={styles.statLabel}>Active Exemptions</div>
          </div>
          <div className={styles.stat}>
            <div className={styles.statValue}>0</div>
            <div className={styles.statLabel}>Temporary</div>
          </div>
          <div className={styles.stat}>
            <div className={styles.statValue}>0</div>
            <div className={styles.statLabel}>Permanent</div>
          </div>
          <div className={styles.stat}>
            <div className={styles.statValue}>0</div>
            <div className={styles.statLabel}>Expiring Soon</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

