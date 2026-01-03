import React, { useEffect, useState } from 'react';
import { jdkApi } from '../../../services/api';
import { JDKVersion } from '../../../types';
import { Card, Button, Badge, Modal, Input, Select, SelectOption } from '../../../components/common';
import { useAuthStore } from '../../../store/authStore';
import styles from './JDKVersions.module.css';

const COMPLIANCE_STATUS_OPTIONS: SelectOption[] = [
  { value: 'Compliant', label: 'Compliant' },
  { value: 'Non-Compliant', label: 'Non-Compliant' },
  { value: 'CompliantStar', label: 'CompliantStar' },
];

// MAJOR_VERSION_OPTIONS removed - using Input type="number" instead

export const JDKVersions: React.FC = () => {
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'Administrator';
  
  const [versions, setVersions] = useState<JDKVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingVersion, setEditingVersion] = useState<JDKVersion | null>(null);
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

  const resetForm = () => {
    setFormData({
      major_version: '',
      vendor: '',
      compliance_status: 'Compliant',
      is_active: true,
    });
    setEditingVersion(null);
  };

  const handleCreate = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const handleEdit = (version: JDKVersion) => {
    setFormData({
      major_version: version.major_version.toString(),
      vendor: version.vendor,
      compliance_status: version.compliance_status,
      is_active: version.is_active,
    });
    setEditingVersion(version);
    setShowCreateModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      if (editingVersion) {
        await jdkApi.update(editingVersion.id, {
          vendor: formData.vendor,
          compliance_status: formData.compliance_status,
          is_active: formData.is_active,
        });
      } else {
        await jdkApi.create({
          major_version: parseInt(formData.major_version),
          vendor: formData.vendor,
          compliance_status: formData.compliance_status,
          is_active: formData.is_active,
        });
      }
      setShowCreateModal(false);
      resetForm();
      await loadVersions();
    } catch (err: any) {
      setError(err.detail || `Failed to ${editingVersion ? 'update' : 'create'} JDK version`);
    }
  };

  const handleToggleActive = async (version: JDKVersion) => {
    try {
      await jdkApi.update(version.id, {
        is_active: !version.is_active,
      });
      await loadVersions();
    } catch (err: any) {
      setError(err.detail || 'Failed to update JDK version');
    }
  };

  // handleUpdateComplianceStatus - reserved for future use if compliance status needs to be updated separately
  // Currently compliance status is updated via the edit modal
  // const handleUpdateComplianceStatus = async (version: JDKVersion, status: string) => {
  //   try {
  //     await jdkApi.updateComplianceStatus(version.id, status);
  //     await loadVersions();
  //   } catch (err: any) {
  //     setError(err.detail || 'Failed to update compliance status');
  //   }
  // };

  if (loading) {
    return <div className={styles.loading}>Loading JDK versions...</div>;
  }

  const getComplianceBadgeVariant = (status: string) => {
    if (status === 'Compliant' || status === 'CompliantStar') return 'success';
    if (status === 'Non-Compliant') return 'error';
    return 'neutral';
  };

  return (
    <div className={styles.jdkVersions}>
      <div className={styles.header}>
        <div>
          <h2>JDK Versions</h2>
          <p className={styles.subtitle}>Manage JDK versions and their compliance status</p>
        </div>
        {isAdmin && (
          <Button onClick={handleCreate}>+ Add JDK Version</Button>
        )}
      </div>

      {error && (
        <div className={styles.error}>
          {error}
          <button onClick={() => setError(null)} className={styles.errorClose}>×</button>
        </div>
      )}

      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          resetForm();
        }}
        title={editingVersion ? 'Edit JDK Version' : 'Create New JDK Version'}
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => {
                setShowCreateModal(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button type="submit" form="jdk-form">
              {editingVersion ? 'Update' : 'Create'}
            </Button>
          </>
        }
      >
        <form id="jdk-form" onSubmit={handleSubmit}>
          <div className={styles.form}>
            <Input
              id="major_version"
              label="Major Version"
              type="text"
              value={formData.major_version}
              onChange={(e) => setFormData({ ...formData, major_version: e.target.value })}
              required
              disabled={!!editingVersion}
              fullWidth
              placeholder="8, 11, 17, 18, 19, 21, 22"
            />

            <Input
              id="vendor"
              label="Vendor"
              type="text"
              value={formData.vendor}
              onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
              required
              fullWidth
              placeholder="e.g., Oracle, Zulu, Amazon"
            />

            <Select
              id="compliance_status"
              label="Compliance Status"
              value={formData.compliance_status}
              onChange={(e) =>
                setFormData({ ...formData, compliance_status: e.target.value as any })
              }
              options={COMPLIANCE_STATUS_OPTIONS}
              required
              fullWidth
            />

            <div className={styles.checkboxGroup}>
              <label>
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
                <span>Active</span>
              </label>
            </div>
          </div>
        </form>
      </Modal>

      <div className={styles.table}>
        {versions.length === 0 ? (
          <Card className={styles.empty}>
            <p>No JDK versions found. Create your first JDK version to get started.</p>
          </Card>
        ) : (
          <table className={styles.tableElement}>
            <thead>
              <tr>
                <th>Major Version</th>
                <th>Vendor</th>
                <th>Compliance Status</th>
                <th>Active</th>
                {isAdmin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {versions.map((version) => (
                <tr key={version.id}>
                  <td>{version.major_version}</td>
                  <td>{version.vendor}</td>
                  <td>
                    <Badge variant={getComplianceBadgeVariant(version.compliance_status)}>
                      {version.compliance_status}
                    </Badge>
                  </td>
                  <td>
                    <Badge variant={version.is_active ? 'success' : 'neutral'}>
                      {version.is_active ? 'Yes' : 'No'}
                    </Badge>
                  </td>
                  {isAdmin && (
                    <td>
                      <div className={styles.actions}>
                        <Button size="sm" variant="secondary" onClick={() => handleEdit(version)}>
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleToggleActive(version)}
                        >
                          {version.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};