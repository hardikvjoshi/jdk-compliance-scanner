import React, { useEffect, useState } from 'react';
import { clustersApi } from '../../../services/api';
import { Cluster, ClusterCreate } from '../../../types';
import { Card, Button, Badge } from '../../../components/common';
import styles from './Clusters.module.css';

export const Clusters: React.FC = () => {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<ClusterCreate>({
    cluster_name: '',
    console_url: '',
    api_url: '',
    environment: '',
  });

  useEffect(() => {
    loadClusters();
  }, []);

  const loadClusters = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await clustersApi.list();
      setClusters(data);
    } catch (err: any) {
      setError(err.detail || 'Failed to load clusters');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      await clustersApi.create(formData);
      setShowForm(false);
      setFormData({ cluster_name: '', console_url: '', api_url: '', environment: '' });
      await loadClusters();
    } catch (err: any) {
      setError(err.detail || 'Failed to create cluster');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this cluster?')) return;
    try {
      await clustersApi.delete(id);
      await loadClusters();
    } catch (err: any) {
      setError(err.detail || 'Failed to delete cluster');
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading clusters...</div>;
  }

  return (
    <div className={styles.clusters}>
      <div className={styles.header}>
        <h2>Clusters</h2>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add Cluster'}
        </Button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {showForm && (
        <Card className={styles.formCard}>
          <h3>Create New Cluster</h3>
          <form onSubmit={handleSubmit}>
            <div className={styles.formGroup}>
              <label>Cluster Name *</label>
              <input
                type="text"
                value={formData.cluster_name}
                onChange={(e) => setFormData({ ...formData, cluster_name: e.target.value })}
                required
              />
            </div>
            <div className={styles.formGroup}>
              <label>Console URL</label>
              <input
                type="url"
                value={formData.console_url}
                onChange={(e) => setFormData({ ...formData, console_url: e.target.value })}
              />
            </div>
            <div className={styles.formGroup}>
              <label>API URL</label>
              <input
                type="url"
                value={formData.api_url}
                onChange={(e) => setFormData({ ...formData, api_url: e.target.value })}
              />
            </div>
            <div className={styles.formGroup}>
              <label>Environment</label>
              <input
                type="text"
                value={formData.environment}
                onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                placeholder="Dev, UAT, Production"
              />
            </div>
            <div className={styles.formActions}>
              <Button type="submit">Create Cluster</Button>
            </div>
          </form>
        </Card>
      )}

      <div className={styles.list}>
        {clusters.length === 0 ? (
          <Card className={styles.empty}>
            <p>No clusters found. Create your first cluster to get started.</p>
          </Card>
        ) : (
          clusters.map((cluster) => (
            <Card key={cluster.id} className={styles.clusterCard}>
              <div className={styles.clusterHeader}>
                <h3>{cluster.cluster_name}</h3>
                <Badge variant={cluster.environment ? 'info' : 'neutral'}>
                  {cluster.environment || 'N/A'}
                </Badge>
              </div>
              <div className={styles.clusterDetails}>
                {cluster.console_url && (
                  <div>
                    <strong>Console:</strong>{' '}
                    <a href={cluster.console_url} target="_blank" rel="noopener noreferrer">
                      {cluster.console_url}
                    </a>
                  </div>
                )}
                {cluster.api_url && (
                  <div>
                    <strong>API:</strong> {cluster.api_url}
                  </div>
                )}
                <div className={styles.clusterMeta}>
                  <span>Created: {new Date(cluster.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              <div className={styles.clusterActions}>
                <Button variant="danger" size="sm" onClick={() => handleDelete(cluster.id)}>
                  Delete
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

