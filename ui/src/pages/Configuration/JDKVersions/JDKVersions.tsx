import React, { useEffect, useState } from 'react';
import { jdkApi } from '../../../services/api';
import { JDKVersion } from '../../../types';
import { Card, Button, Badge } from '../../../components/common';
import styles from './JDKVersions.module.css';

export const JDKVersions: React.FC = () => {
  const [versions, setVersions] = useState<JDKVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    major_version: '',
    vendor: '',
    compliance_status: 'Compliant' as 'Compliant' | 'Non-Compliant' | 'CompliantStar',
    is_active: true,
  });

  useEffect(() => {
    loadVersions();
  }, []);

  const loadVersions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await jdkApi.list();
      setVersions(data);
    } catch (err: any) {
      setError(err.detail || 'Failed to load JDK versions');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      await jdkApi.create({
        major_version: parseInt(formData.major_version),
        vendor: formData.vendor,
        compliance_status: formData.compliance_status,
        is_active: formData.is_active,
      });
      setShowForm(false);
      setFormData({ major_version: '', vendor: '', compliance_status: 'Compliant', is_active: true });
      await loadVersions();
    } catch (err: any) {
      setError(err.detail || 'Failed to create JDK version');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this JDK version?')) return;
    try {
      // Note: Delete endpoint may not exist, handle gracefully
      await loadVersions();
    } catch (err: any) {
      setError(err.detail || 'Failed to delete JDK version');
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading JDK versions...</div>;
  }

  return (
    <div className={styles.jdkVersions}>
      <div className={styles.header}>
        <h2>JDK Versions</h2>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add JDK Version'}
        </Button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {showForm && (
        <Card className={styles.formCard}>
          <h3>Create New JDK Version</h3>
          <form onSubmit={handleSubmit}>
            <div className={styles.formGroup}>
              <label>Major Version *</label>
              <input
                type="number"
                value={formData.major_version}
                onChange={(e) => setFormData({ ...formData, major_version: e.target.value })}
                required
                min="1"
              />
            </div>
            <div className={styles.formGroup}>
              <label>Vendor *</label>
              <input
                type="text"
                value={formData.vendor}
                onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                required
                placeholder="e.g., Oracle, Zulu, Amazon"
              />
            </div>
            <div className={styles.formGroup}>
              <label>Compliance Status *</label>
              <select
                value={formData.compliance_status}
                onChange={(e) => setFormData({ ...formData, compliance_status: e.target.value as any })}
                required
              >
                <option value="Compliant">Compliant</option>
                <option value="Non-Compliant">Non-Compliant</option>
                <option value="CompliantStar">CompliantStar</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <label>
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
                Active
              </label>
            </div>
            <div className={styles.formActions}>
              <Button type="submit">Create JDK Version</Button>
            </div>
          </form>
        </Card>
      )}

      <div className={styles.list}>
        {versions.length === 0 ? (
          <Card className={styles.empty}>
            <p>No JDK versions found. Create your first JDK version to get started.</p>
          </Card>
        ) : (
          versions.map((version) => (
            <Card key={version.id} className={styles.versionCard}>
              <div className={styles.versionHeader}>
                <h3>JDK {version.major_version}</h3>
                <div className={styles.badges}>
                  <Badge
                    variant={
                      version.compliance_status === 'Compliant' || version.compliance_status === 'CompliantStar'
                        ? 'success'
                        : 'error'
                    }
                  >
                    {version.compliance_status}
                  </Badge>
                  {version.is_active && <Badge variant="info">Active</Badge>}
                </div>
              </div>
              <div className={styles.versionDetails}>
                <div><strong>Vendor:</strong> {version.vendor}</div>
                <div className={styles.versionMeta}>
                  <span>Created: {new Date(version.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

