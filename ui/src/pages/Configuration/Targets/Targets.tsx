import React, { useEffect, useState } from 'react';
import { targetsApi } from '../../../services/api';
import { Target } from '../../../types';
import {
  Card,
  Button,
  Badge,
  Modal,
  Input,
  Select,
  SelectOption,
  TextArea,
} from '../../../components/common';
import { useAuthStore } from '../../../store/authStore';
import styles from './Targets.module.css';

// Only Unix and Windows are supported in UI (Cloud is placeholder, OpenShift handled via Projects)
const DEPLOYMENT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'Unix', label: 'Unix' },
  { value: 'Windows', label: 'Windows' },
];

const TIER_OPTIONS: SelectOption[] = [
  { value: 'Dev', label: 'Dev' },
  { value: 'UAT', label: 'UAT' },
  { value: 'Production', label: 'Production' },
];

const STATUS_OPTIONS: SelectOption[] = [
  { value: 'Active', label: 'Active' },
  { value: 'Inactive', label: 'Inactive' },
];

interface TargetFormData {
  name: string;
  deployment_type: string; // Unix or Windows only
  hostname: string;
  ip_address: string;
  connection_config: string; // JSON string: {"username": "user", "password": "pass"}
  tier: string;
  // Note: project_id and cluster_id are NOT applicable for Unix/Windows targets (standalone)
}

export const Targets: React.FC = () => {
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'Administrator';

  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState<Target | null>(null);

  // Form states
  const [formData, setFormData] = useState<TargetFormData>({
    name: '',
    deployment_type: '',
    hostname: '',
    ip_address: '',
    connection_config: '{}',
    tier: '',
  });

  // Filter states
  const [filters, setFilters] = useState({
    deployment_type: '',
    tier: '',
    status: '',
  });
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // Filter to only show Unix and Windows targets (exclude Cloud and OpenShift)
      const allTargets = await targetsApi.list();
      const filteredTargets = allTargets.filter(
        (t) => t.deployment_type === 'Unix' || t.deployment_type === 'Windows'
      );
      setTargets(filteredTargets);
    } catch (err: any) {
      setError(err.detail || 'Failed to load targets');
    } finally {
      setLoading(false);
    }
  };

  const loadTargets = async () => {
    try {
      const filterParams: any = {};
      if (filters.deployment_type) filterParams.deployment_type = filters.deployment_type;
      if (filters.tier) filterParams.tier = filters.tier;
      if (filters.status) filterParams.status = filters.status;

      const allTargets = await targetsApi.list(filterParams);
      // Filter to only show Unix and Windows targets (exclude Cloud and OpenShift)
      const filteredTargets = allTargets.filter(
        (t) => t.deployment_type === 'Unix' || t.deployment_type === 'Windows'
      );
      setTargets(filteredTargets);
    } catch (err: any) {
      setError(err.detail || 'Failed to load targets');
    }
  };

  useEffect(() => {
    if (!showCreateModal && !showEditModal) {
      loadTargets();
    }
  }, [filters]);

  const resetForm = () => {
    setFormData({
      name: '',
      deployment_type: '',
      hostname: '',
      ip_address: '',
      connection_config: '{}',
      tier: '',
    });
    setSelectedTarget(null);
  };

  const handleCreate = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const handleEdit = (target: Target) => {
    setFormData({
      name: target.name,
      deployment_type: target.deployment_type,
      hostname: target.hostname || '',
      ip_address: target.ip_address || '',
      connection_config: '{}', // Cannot show encrypted config, user must re-enter
      tier: target.tier,
    });
    setSelectedTarget(target);
    setShowEditModal(true);
  };

  const handleDelete = (target: Target) => {
    setSelectedTarget(target);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (!selectedTarget) return;

    try {
      await targetsApi.delete(selectedTarget.id);
      setShowDeleteConfirm(false);
      setSelectedTarget(null);
      await loadTargets();
    } catch (err: any) {
      setError(err.detail || 'Failed to delete target');
      setShowDeleteConfirm(false);
    }
  };

  const validateConnectionConfig = (jsonString: string): { valid: boolean; error?: string } => {
    try {
      const parsed = JSON.parse(jsonString);
      if (typeof parsed !== 'object' || Array.isArray(parsed)) {
        return { valid: false, error: 'Connection config must be a JSON object' };
      }
      return { valid: true };
    } catch (e) {
      return { valid: false, error: 'Invalid JSON format' };
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name || !formData.deployment_type || !formData.hostname || !formData.tier) {
      setError('Name, deployment type, hostname, and tier are required');
      return;
    }

    const configValidation = validateConnectionConfig(formData.connection_config);
    if (!configValidation.valid) {
      setError(configValidation.error || 'Invalid connection config');
      return;
    }

    try {
      setError(null);
      const connectionConfig = JSON.parse(formData.connection_config);

      await targetsApi.create({
        name: formData.name,
        deployment_type: formData.deployment_type,
        hostname: formData.hostname || undefined,
        ip_address: formData.ip_address || undefined,
        connection_config: connectionConfig,
        // Note: project_id and cluster_id are not applicable for Unix/Windows targets
        tier: formData.tier,
      });
      setShowCreateModal(false);
      resetForm();
      await loadTargets();
    } catch (err: any) {
      setError(err.detail || 'Failed to create target');
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTarget) return;

    if (!formData.name || !formData.tier) {
      setError('Name and tier are required');
      return;
    }

    const updateData: any = {
      name: formData.name,
      hostname: formData.hostname || undefined,
      ip_address: formData.ip_address || undefined,
      tier: formData.tier,
    };

    // Only update connection_config if it's valid JSON and not empty
    if (formData.connection_config && formData.connection_config !== '{}') {
      const configValidation = validateConnectionConfig(formData.connection_config);
      if (!configValidation.valid) {
        setError(configValidation.error || 'Invalid connection config');
        return;
      }
      updateData.connection_config = JSON.parse(formData.connection_config);
    }

    try {
      setError(null);
      await targetsApi.update(selectedTarget.id, updateData);
      setShowEditModal(false);
      resetForm();
      await loadTargets();
    } catch (err: any) {
      setError(err.detail || 'Failed to update target');
    }
  };

  const filteredTargets = targets.filter((target) => {
    if (searchTerm) {
      return target.name.toLowerCase().includes(searchTerm.toLowerCase());
    }
    return true;
  });

  if (loading) {
    return <div className={styles.loading}>Loading targets...</div>;
  }

  return (
    <div className={styles.targets}>
      <div className={styles.header}>
        <div>
          <h2>Targets</h2>
          <p className={styles.subtitle}>Manage standalone Unix and Windows scan targets</p>
        </div>
        {isAdmin && <Button onClick={handleCreate}>+ Add Target</Button>}
      </div>

      {error && (
        <div className={styles.error}>
          {error}
          <button onClick={() => setError(null)} className={styles.errorClose}>
            ×
          </button>
        </div>
      )}

      {/* Filters */}
      <Card className={styles.filtersCard}>
        <div className={styles.filters}>
          <Input
            id="search"
            placeholder="Search by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            fullWidth
          />
          <Select
            id="filter_deployment_type"
            placeholder="Filter by Deployment Type"
            value={filters.deployment_type}
            onChange={(e) => setFilters({ ...filters, deployment_type: e.target.value })}
            options={[
              { value: '', label: 'All Types' },
              ...DEPLOYMENT_TYPE_OPTIONS,
            ]}
          />
          <Select
            id="filter_tier"
            placeholder="Filter by Tier"
            value={filters.tier}
            onChange={(e) => setFilters({ ...filters, tier: e.target.value })}
            options={[{ value: '', label: 'All Tiers' }, ...TIER_OPTIONS]}
          />
          <Select
            id="filter_status"
            placeholder="Filter by Status"
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            options={[{ value: '', label: 'All Statuses' }, ...STATUS_OPTIONS]}
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
        title="Create Target"
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
            <Button type="submit" form="create-target-form">
              Create Target
            </Button>
          </>
        }
      >
        <form id="create-target-form" onSubmit={handleCreateSubmit}>
          <div className={styles.form}>
            <Input
              id="name"
              label="Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              fullWidth
            />
            <Select
              id="deployment_type"
              label="Deployment Type"
              value={formData.deployment_type}
              onChange={(e) => setFormData({ ...formData, deployment_type: e.target.value })}
              options={DEPLOYMENT_TYPE_OPTIONS}
              required
              fullWidth
              placeholder="Select deployment type"
            />
            <Input
              id="hostname"
              label="Hostname"
              value={formData.hostname}
              onChange={(e) => setFormData({ ...formData, hostname: e.target.value })}
              required
              fullWidth
            />
            <Input
              id="ip_address"
              label="IP Address"
              value={formData.ip_address}
              onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
              fullWidth
            />
            <Select
              id="tier"
              label="Tier"
              value={formData.tier}
              onChange={(e) => setFormData({ ...formData, tier: e.target.value })}
              options={TIER_OPTIONS}
              required
              fullWidth
              placeholder="Select tier"
            />
            <TextArea
              id="connection_config"
              label="Connection Config (JSON)"
              value={formData.connection_config}
              onChange={(e) => setFormData({ ...formData, connection_config: e.target.value })}
              required
              fullWidth
              rows={6}
              placeholder='{"username": "user", "password": "pass"}'
            />
            <p className={styles.helpText}>
              Enter connection configuration as JSON object. Example:{' '}
              <code>{'{"username": "user", "password": "pass"}'}</code>
              <br />
              Additional optional fields: port (for Unix), domain (for Windows), ssh_key (for Unix)
            </p>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          resetForm();
        }}
        title="Edit Target"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button type="submit" form="edit-target-form">
              Update
            </Button>
          </>
        }
      >
        <form id="edit-target-form" onSubmit={handleEditSubmit}>
          <div className={styles.form}>
            <Input
              id="edit_name"
              label="Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              fullWidth
            />
            <Input
              id="edit_deployment_type"
              label="Deployment Type"
              value={formData.deployment_type}
              disabled
              fullWidth
            />
            <Input
              id="edit_hostname"
              label="Hostname"
              value={formData.hostname}
              onChange={(e) => setFormData({ ...formData, hostname: e.target.value })}
              fullWidth
            />
            <Input
              id="edit_ip_address"
              label="IP Address"
              value={formData.ip_address}
              onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
              fullWidth
            />
            <Select
              id="edit_tier"
              label="Tier"
              value={formData.tier}
              onChange={(e) => setFormData({ ...formData, tier: e.target.value })}
              options={TIER_OPTIONS}
              required
              fullWidth
            />
            <TextArea
              id="edit_connection_config"
              label="Connection Config (JSON) - Re-enter to update"
              value={formData.connection_config}
              onChange={(e) => setFormData({ ...formData, connection_config: e.target.value })}
              fullWidth
              rows={6}
              placeholder='{"username": "user", "password": "pass"}'
            />
            <p className={styles.helpText}>
              Connection config is encrypted. Re-enter JSON config to update. Leave as {'{}'} to
              keep existing config.
            </p>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteConfirm}
        onClose={() => {
          setShowDeleteConfirm(false);
          setSelectedTarget(null);
        }}
        title="Delete Target"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => {
                setShowDeleteConfirm(false);
                setSelectedTarget(null);
              }}
            >
              Cancel
            </Button>
            <Button variant="danger" onClick={confirmDelete}>
              Delete
            </Button>
          </>
        }
      >
        <p>
          Are you sure you want to delete target &quot;{selectedTarget?.name}&quot;? This action
          cannot be undone.
        </p>
      </Modal>

      {/* Targets Table */}
      <div className={styles.table}>
        {filteredTargets.length === 0 ? (
          <Card className={styles.empty}>
            <p>No targets found. Create your first target to get started.</p>
          </Card>
        ) : (
          <table className={styles.tableElement}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Deployment Type</th>
                <th>Hostname/IP</th>
                <th>Tier</th>
                <th>Status</th>
                {isAdmin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {filteredTargets.map((target) => (
                <tr key={target.id}>
                  <td>{target.name}</td>
                  <td>
                    <Badge variant="info">{target.deployment_type}</Badge>
                  </td>
                  <td>{target.hostname || target.ip_address || '-'}</td>
                  <td>{target.tier}</td>
                  <td>
                    <Badge variant={target.status === 'Active' ? 'success' : 'neutral'}>
                      {target.status}
                    </Badge>
                  </td>
                  {isAdmin && (
                    <td>
                      <div className={styles.actions}>
                        <Button size="sm" variant="secondary" onClick={() => handleEdit(target)}>
                          Edit
                        </Button>
                        <Button size="sm" variant="danger" onClick={() => handleDelete(target)}>
                          Delete
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