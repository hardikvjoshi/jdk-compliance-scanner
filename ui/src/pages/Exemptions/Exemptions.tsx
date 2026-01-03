import React, { useEffect, useState } from 'react';
import { exemptionsApi, projectsApi, jdkApi } from '../../services/api';
import { Exemption, Project, JDKVersion } from '../../types';
import {
  Card,
  Button,
  Badge,
  Modal,
  Input,
  Select,
  SelectOption,
  TextArea,
} from '../../components/common';
import { useAuthStore } from '../../store/authStore';
import styles from './Exemptions.module.css';

const EXEMPTION_TYPE_OPTIONS: SelectOption[] = [
  { value: 'Temporary', label: 'Temporary' },
  { value: 'Permanent', label: 'Permanent' },
];

const EXEMPTION_STATUS_OPTIONS: SelectOption[] = [
  { value: 'Active', label: 'Active' },
  { value: 'Expired', label: 'Expired' },
  { value: 'Revoked', label: 'Revoked' },
];

interface ExemptionFormData {
  project_id: string;
  application_name: string;
  jdk_version_id: string;
  exemption_reason: string;
  start_date: string;
  end_date: string;
  exemption_type: 'Temporary' | 'Permanent';
}

export const Exemptions: React.FC = () => {
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'Administrator';

  const [exemptions, setExemptions] = useState<Exemption[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [jdkVersions, setJdkVersions] = useState<JDKVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRevokeConfirm, setShowRevokeConfirm] = useState(false);
  const [selectedExemption, setSelectedExemption] = useState<Exemption | null>(null);

  // Form states
  const [formData, setFormData] = useState<ExemptionFormData>({
    project_id: '',
    application_name: '',
    jdk_version_id: '',
    exemption_reason: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    exemption_type: 'Temporary',
  });

  // Filter states
  const [filters, setFilters] = useState({
    project_id: '',
    exemption_status: '',
    exemption_type: '',
  });
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [exemptionsData, projectsData, jdkVersionsData] = await Promise.all([
        exemptionsApi.list(),
        projectsApi.list(),
        jdkApi.list(),
      ]);
      setExemptions(exemptionsData);
      setProjects(projectsData.filter((p) => p.status === 'Active'));
      setJdkVersions(jdkVersionsData.filter((v) => v.is_active));
    } catch (err: any) {
      setError(err.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadExemptions = async () => {
    try {
      const filterParams: any = {};
      if (filters.project_id) filterParams.project_id = parseInt(filters.project_id);
      if (filters.exemption_status) filterParams.exemption_status = filters.exemption_status;
      if (filters.exemption_type) filterParams.exemption_type = filters.exemption_type;

      const data = await exemptionsApi.list(filterParams);
      setExemptions(data);
    } catch (err: any) {
      setError(err.detail || 'Failed to load exemptions');
    }
  };

  useEffect(() => {
    if (!showCreateModal) {
      loadExemptions();
    }
  }, [filters]);

  const projectOptions: SelectOption[] = projects.map((p) => ({
    value: p.id.toString(),
    label: p.project_name,
  }));

  const jdkVersionOptions: SelectOption[] = jdkVersions.map((v) => ({
    value: v.id.toString(),
    label: `JDK ${v.major_version} (${v.vendor})`,
  }));

  const resetForm = () => {
    setFormData({
      project_id: '',
      application_name: '',
      jdk_version_id: '',
      exemption_reason: '',
      start_date: new Date().toISOString().split('T')[0],
      end_date: '',
      exemption_type: 'Temporary',
    });
  };

  const handleCreate = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const handleRevoke = (exemption: Exemption) => {
    setSelectedExemption(exemption);
    setShowRevokeConfirm(true);
  };

  const confirmRevoke = async () => {
    if (!selectedExemption) return;

    try {
      await exemptionsApi.revoke(selectedExemption.id);
      setShowRevokeConfirm(false);
      setSelectedExemption(null);
      await loadExemptions();
    } catch (err: any) {
      setError(err.detail || 'Failed to revoke exemption');
      setShowRevokeConfirm(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (
      !formData.project_id ||
      !formData.application_name ||
      !formData.jdk_version_id ||
      !formData.exemption_reason ||
      !formData.start_date ||
      !formData.exemption_type
    ) {
      setError('Please fill all required fields');
      return;
    }

    if (formData.exemption_type === 'Temporary' && !formData.end_date) {
      setError('End date is required for temporary exemptions');
      return;
    }

    // Validate dates
    if (formData.end_date && formData.start_date >= formData.end_date) {
      setError('End date must be after start date');
      return;
    }

    try {
      setError(null);
      await exemptionsApi.create({
        project_id: parseInt(formData.project_id),
        application_name: formData.application_name.trim(),
        jdk_version_id: parseInt(formData.jdk_version_id),
        exemption_reason: formData.exemption_reason.trim(),
        start_date: formData.start_date,
        end_date: formData.exemption_type === 'Temporary' ? formData.end_date : null,
        exemption_type: formData.exemption_type,
      });
      setShowCreateModal(false);
      resetForm();
      await loadExemptions();
    } catch (err: any) {
      setError(err.detail || 'Failed to create exemption');
    }
  };

  const filteredExemptions = exemptions.filter((exemption) => {
    if (searchTerm) {
      return (
        exemption.application_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (exemption.project?.project_name || '')
          .toLowerCase()
          .includes(searchTerm.toLowerCase())
      );
    }
    return true;
  });

  const stats = {
    active: exemptions.filter((e) => e.exemption_status === 'Active').length,
    temporary: exemptions.filter((e) => e.exemption_type === 'Temporary').length,
    permanent: exemptions.filter((e) => e.exemption_type === 'Permanent').length,
    expiringSoon: exemptions.filter((e) => {
      if (e.exemption_type === 'Permanent' || !e.end_date) return false;
      const endDate = new Date(e.end_date);
      const today = new Date();
      const daysUntilExpiry = Math.ceil((endDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      return daysUntilExpiry <= 30 && daysUntilExpiry > 0;
    }).length,
  };

  if (loading) {
    return <div className={styles.loading}>Loading exemptions...</div>;
  }

  return (
    <div className={styles.exemptions}>
      <div className={styles.header}>
        <div>
          <h2>Exemptions</h2>
          <p className={styles.subtitle}>Manage JDK compliance exemptions for applications</p>
        </div>
        {isAdmin && <Button onClick={handleCreate}>+ Create Exemption</Button>}
      </div>

      {error && (
        <div className={styles.error}>
          {error}
          <button onClick={() => setError(null)} className={styles.errorClose}>
            ×
          </button>
        </div>
      )}

      {/* Statistics */}
      <div className={styles.statsGrid}>
        <Card className={styles.statCard}>
          <div className={styles.statValue}>{stats.active}</div>
          <div className={styles.statLabel}>Active Exemptions</div>
        </Card>
        <Card className={styles.statCard}>
          <div className={styles.statValue}>{stats.temporary}</div>
          <div className={styles.statLabel}>Temporary</div>
        </Card>
        <Card className={styles.statCard}>
          <div className={styles.statValue}>{stats.permanent}</div>
          <div className={styles.statLabel}>Permanent</div>
        </Card>
        <Card className={styles.statCard}>
          <div className={styles.statValue}>{stats.expiringSoon}</div>
          <div className={styles.statLabel}>Expiring Soon</div>
        </Card>
      </div>

      {/* Filters */}
      <Card className={styles.filtersCard}>
        <div className={styles.filters}>
          <Input
            id="search"
            placeholder="Search by application or project name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            fullWidth
          />
          <Select
            id="filter_project"
            placeholder="Filter by Project"
            value={filters.project_id}
            onChange={(e) => setFilters({ ...filters, project_id: e.target.value })}
            options={[{ value: '', label: 'All Projects' }, ...projectOptions]}
          />
          <Select
            id="filter_status"
            placeholder="Filter by Status"
            value={filters.exemption_status}
            onChange={(e) => setFilters({ ...filters, exemption_status: e.target.value })}
            options={[{ value: '', label: 'All Statuses' }, ...EXEMPTION_STATUS_OPTIONS]}
          />
          <Select
            id="filter_type"
            placeholder="Filter by Type"
            value={filters.exemption_type}
            onChange={(e) => setFilters({ ...filters, exemption_type: e.target.value })}
            options={[{ value: '', label: 'All Types' }, ...EXEMPTION_TYPE_OPTIONS]}
          />
        </div>
      </Card>

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          resetForm();
        }}
        title="Create Exemption"
        size="lg"
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
            <Button type="submit" form="create-exemption-form">
              Create Exemption
            </Button>
          </>
        }
      >
        <form id="create-exemption-form" onSubmit={handleCreateSubmit}>
          <div className={styles.form}>
            <Select
              id="project_id"
              label="Project"
              value={formData.project_id}
              onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
              options={projectOptions}
              required
              fullWidth
              placeholder="Select a project"
            />
            <Input
              id="application_name"
              label="Application Name"
              value={formData.application_name}
              onChange={(e) => setFormData({ ...formData, application_name: e.target.value })}
              required
              fullWidth
              placeholder="e.g., my-app-service"
            />
            <Select
              id="jdk_version_id"
              label="JDK Version"
              value={formData.jdk_version_id}
              onChange={(e) => setFormData({ ...formData, jdk_version_id: e.target.value })}
              options={jdkVersionOptions}
              required
              fullWidth
              placeholder="Select JDK version"
            />
            <Select
              id="exemption_type"
              label="Exemption Type"
              value={formData.exemption_type}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  exemption_type: e.target.value as 'Temporary' | 'Permanent',
                  end_date: e.target.value === 'Permanent' ? '' : formData.end_date,
                })
              }
              options={EXEMPTION_TYPE_OPTIONS}
              required
              fullWidth
            />
            <Input
              id="start_date"
              label="Start Date"
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              required
              fullWidth
            />
            {formData.exemption_type === 'Temporary' && (
              <Input
                id="end_date"
                label="End Date"
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                required
                fullWidth
                min={formData.start_date}
              />
            )}
            <TextArea
              id="exemption_reason"
              label="Exemption Reason"
              value={formData.exemption_reason}
              onChange={(e) => setFormData({ ...formData, exemption_reason: e.target.value })}
              required
              fullWidth
              rows={4}
              placeholder="Explain why this exemption is needed..."
            />
          </div>
        </form>
      </Modal>

      {/* Revoke Confirmation Modal */}
      <Modal
        isOpen={showRevokeConfirm}
        onClose={() => {
          setShowRevokeConfirm(false);
          setSelectedExemption(null);
        }}
        title="Revoke Exemption"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => {
                setShowRevokeConfirm(false);
                setSelectedExemption(null);
              }}
            >
              Cancel
            </Button>
            <Button variant="danger" onClick={confirmRevoke}>
              Revoke
            </Button>
          </>
        }
      >
        <p>
          Are you sure you want to revoke the exemption for &quot;
          {selectedExemption?.application_name}&quot;? This action cannot be undone.
        </p>
      </Modal>

      {/* Exemptions Table */}
      <div className={styles.table}>
        {filteredExemptions.length === 0 ? (
          <Card className={styles.empty}>
            <p>No exemptions found. Create an exemption to see it here.</p>
          </Card>
        ) : (
          <table className={styles.tableElement}>
            <thead>
              <tr>
                <th>Project</th>
                <th>Application</th>
                <th>JDK Version</th>
                <th>Type</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Status</th>
                <th>Reason</th>
                {isAdmin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {filteredExemptions.map((exemption) => (
                <tr key={exemption.id}>
                  <td>{exemption.project?.project_name || `Project ${exemption.project_id}`}</td>
                  <td>{exemption.application_name}</td>
                  <td>
                    {exemption.jdk_version
                      ? `JDK ${exemption.jdk_version.major_version} (${exemption.jdk_version.vendor})`
                      : `JDK Version ${exemption.jdk_version_id}`}
                  </td>
                  <td>
                    <Badge variant={exemption.exemption_type === 'Permanent' ? 'info' : 'neutral'}>
                      {exemption.exemption_type}
                    </Badge>
                  </td>
                  <td>{new Date(exemption.start_date).toLocaleDateString()}</td>
                  <td>
                    {exemption.end_date
                      ? new Date(exemption.end_date).toLocaleDateString()
                      : 'N/A'}
                  </td>
                  <td>
                    <Badge
                      variant={
                        exemption.exemption_status === 'Active'
                          ? 'success'
                          : exemption.exemption_status === 'Expired'
                            ? 'warning'
                            : 'neutral'
                      }
                    >
                      {exemption.exemption_status}
                    </Badge>
                  </td>
                  <td className={styles.reasonCell}>{exemption.exemption_reason}</td>
                  {isAdmin && exemption.exemption_status === 'Active' && (
                    <td>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => handleRevoke(exemption)}
                      >
                        Revoke
                      </Button>
                    </td>
                  )}
                  {isAdmin && exemption.exemption_status !== 'Active' && <td>-</td>}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
