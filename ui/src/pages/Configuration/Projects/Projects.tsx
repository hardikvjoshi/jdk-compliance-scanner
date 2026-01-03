import React, { useEffect, useState } from 'react';
import { projectsApi, clustersApi } from '../../../services/api';
import { Project, Cluster } from '../../../types';
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
import styles from './Projects.module.css';

const TECHNOLOGY_OPTIONS: SelectOption[] = [
  { value: 'Java', label: 'Java' },
  { value: 'Python', label: 'Python' },
  { value: 'Node', label: 'Node' },
  { value: 'Go', label: 'Go' },
  { value: 'Mixed', label: 'Mixed' },
];

const TIER_OPTIONS: SelectOption[] = [
  { value: 'Dev', label: 'Dev' },
  { value: 'UAT', label: 'UAT' },
  { value: 'Production', label: 'Production' },
];

const STATUS_OPTIONS: SelectOption[] = [
  { value: 'Active', label: 'Active' },
  { value: 'Inactive', label: 'Inactive' },
  { value: 'Retired', label: 'Retired' },
];

type FormStep = 1 | 2 | 3;

interface ProjectFormData {
  project_name: string;
  cluster_id: string;
  technology: string;
  tribe: string;
  tier: string;
  retired: boolean;
  console_url: string;
  cluster_name: string;
  tech_read_token: string;
  tech_edit_credentials: string;
  wrapper_cluster_token: string;
}

export const Projects: React.FC = () => {
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'Administrator';

  const [projects, setProjects] = useState<Project[]>([]);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // Form states
  const [formStep, setFormStep] = useState<FormStep>(1);
  const [formData, setFormData] = useState<ProjectFormData>({
    project_name: '',
    cluster_id: '',
    technology: '',
    tribe: '',
    tier: '',
    retired: false,
    console_url: '',
    cluster_name: '',
    tech_read_token: '',
    tech_edit_credentials: '',
    wrapper_cluster_token: '',
  });

  const [credentialsData, setCredentialsData] = useState({
    tech_read_token: '',
    tech_edit_credentials: '',
    wrapper_cluster_token: '',
  });

  // Filter states
  const [filters, setFilters] = useState({
    cluster_id: '',
    technology: '',
    tier: '',
    retired: '',
    status: '',
  });
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [projectsData, clustersData] = await Promise.all([
        projectsApi.list(),
        clustersApi.list(),
      ]);
      setProjects(projectsData);
      setClusters(clustersData);
    } catch (err: any) {
      setError(err.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const filterParams: any = {};
      if (filters.cluster_id) filterParams.cluster_id = parseInt(filters.cluster_id);
      if (filters.technology) filterParams.technology = filters.technology;
      if (filters.tier) filterParams.tier = filters.tier;
      if (filters.retired !== '') filterParams.retired = filters.retired === 'true';
      if (filters.status) filterParams.status = filters.status;

      const data = await projectsApi.list(filterParams);
      setProjects(data);
    } catch (err: any) {
      setError(err.detail || 'Failed to load projects');
    }
  };

  useEffect(() => {
    if (!showCreateModal && !showEditModal) {
      loadProjects();
    }
  }, [filters]);

  const clusterOptions: SelectOption[] = clusters.map((c) => ({
    value: c.id.toString(),
    label: c.cluster_name,
  }));

  const resetForm = () => {
    setFormData({
      project_name: '',
      cluster_id: '',
      technology: '',
      tribe: '',
      tier: '',
      retired: false,
      console_url: '',
      cluster_name: '',
      tech_read_token: '',
      tech_edit_credentials: '',
      wrapper_cluster_token: '',
    });
    setFormStep(1);
    setSelectedProject(null);
  };

  const handleCreate = () => {
    resetForm();
    setShowCreateModal(true);
  };

  const handleEdit = (project: Project) => {
    const selectedCluster = clusters.find((c) => c.id === project.cluster_id);
    // Use cluster data if available, otherwise use project data (fallback)
    setFormData({
      project_name: project.project_name,
      cluster_id: project.cluster_id.toString(),
      technology: project.technology,
      tribe: project.tribe,
      tier: project.tier,
      retired: project.retired,
      console_url: selectedCluster?.console_url || project.console_url,
      cluster_name: selectedCluster?.cluster_name || project.cluster_name,
      tech_read_token: '',
      tech_edit_credentials: '',
      wrapper_cluster_token: '',
    });
    setSelectedProject(project);
    setShowEditModal(true);
  };

  const handleUpdateCredentials = (project: Project) => {
    setCredentialsData({
      tech_read_token: '',
      tech_edit_credentials: '',
      wrapper_cluster_token: '',
    });
    setSelectedProject(project);
    setShowCredentialsModal(true);
  };

  const handleClusterChange = (clusterId: string) => {
    const cluster = clusters.find((c) => c.id === parseInt(clusterId));
    setFormData({
      ...formData,
      cluster_id: clusterId,
      cluster_name: cluster?.cluster_name || '',
      console_url: cluster?.console_url || '',
    });
  };

  const validateStep = (step: FormStep): boolean => {
    if (step === 1) {
      return !!(
        formData.project_name &&
        formData.cluster_id &&
        formData.technology &&
        formData.tribe &&
        formData.tier
      );
    }
    if (step === 2) {
      // Step 2 requires cluster_name and console_url (must be valid URL)
      return !!(formData.cluster_name && formData.console_url && formData.console_url.trim());
    }
    if (step === 3) {
      return !!(
        formData.tech_read_token &&
        formData.tech_edit_credentials &&
        formData.wrapper_cluster_token
      );
    }
    return false;
  };

  const handleNextStep = () => {
    if (validateStep(formStep)) {
      if (formStep < 3) {
        setFormStep((formStep + 1) as FormStep);
      }
    }
  };

  const handlePrevStep = () => {
    if (formStep > 1) {
      setFormStep((formStep - 1) as FormStep);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateStep(3)) {
      setError('Please fill all required fields');
      return;
    }

    // Validate console_url is a valid URL
    if (!formData.console_url || !formData.console_url.trim()) {
      setError('Console URL is required');
      return;
    }

    try {
      // Validate URL format
      new URL(formData.console_url.trim());
    } catch (e) {
      setError('Console URL must be a valid URL (e.g., https://console.example.com)');
      return;
    }

    try {
      setError(null);
      await projectsApi.create({
        project_name: formData.project_name,
        cluster_id: parseInt(formData.cluster_id),
        technology: formData.technology,
        tribe: formData.tribe,
        tier: formData.tier,
        cluster_name: formData.cluster_name,
        console_url: formData.console_url.trim(),
        retired: formData.retired,
        tech_read_token: formData.tech_read_token,
        tech_edit_credentials: formData.tech_edit_credentials,
        wrapper_cluster_token: formData.wrapper_cluster_token,
      });
      setShowCreateModal(false);
      resetForm();
      await loadProjects();
    } catch (err: any) {
      setError(err.detail || 'Failed to create project');
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject) return;

    // Validate console_url is a valid URL if provided
    if (formData.console_url && formData.console_url.trim()) {
      try {
        new URL(formData.console_url.trim());
      } catch (e) {
        setError('Console URL must be a valid URL (e.g., https://console.example.com)');
        return;
      }
    }

    try {
      setError(null);
      await projectsApi.update(selectedProject.id, {
        project_name: formData.project_name,
        technology: formData.technology,
        tribe: formData.tribe,
        tier: formData.tier,
        cluster_name: formData.cluster_name,
        console_url: formData.console_url?.trim() || formData.console_url,
        retired: formData.retired,
      });
      setShowEditModal(false);
      resetForm();
      await loadProjects();
    } catch (err: any) {
      setError(err.detail || 'Failed to update project');
    }
  };

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject) return;

    if (
      !credentialsData.tech_read_token ||
      !credentialsData.tech_edit_credentials ||
      !credentialsData.wrapper_cluster_token
    ) {
      setError('All credential fields are required');
      return;
    }

    try {
      setError(null);
      await projectsApi.updateCredentials(selectedProject.id, credentialsData);
      setShowCredentialsModal(false);
      setCredentialsData({
        tech_read_token: '',
        tech_edit_credentials: '',
        wrapper_cluster_token: '',
      });
      setSelectedProject(null);
      await loadProjects();
    } catch (err: any) {
      setError(err.detail || 'Failed to update credentials');
    }
  };

  const handleRetire = async (project: Project) => {
    if (!window.confirm(`Are you sure you want to retire project "${project.project_name}"?`)) {
      return;
    }

    try {
      await projectsApi.delete(project.id);
      await loadProjects();
    } catch (err: any) {
      setError(err.detail || 'Failed to retire project');
    }
  };

  const handleActivate = async (project: Project) => {
    try {
      await projectsApi.activate(project.id);
      await loadProjects();
    } catch (err: any) {
      setError(err.detail || 'Failed to activate project');
    }
  };

  const filteredProjects = projects.filter((project) => {
    if (searchTerm) {
      return project.project_name.toLowerCase().includes(searchTerm.toLowerCase());
    }
    return true;
  });

  if (loading) {
    return <div className={styles.loading}>Loading projects...</div>;
  }

  const renderCreateFormStep = () => {
    switch (formStep) {
      case 1:
        return (
          <div className={styles.formStep}>
            <Input
              id="project_name"
              label="Project Name"
              value={formData.project_name}
              onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
              required
              fullWidth
            />
            <Select
              id="cluster_id"
              label="Cluster"
              value={formData.cluster_id}
              onChange={(e) => handleClusterChange(e.target.value)}
              options={clusterOptions}
              required
              fullWidth
              placeholder="Select a cluster"
            />
            <Select
              id="technology"
              label="Technology"
              value={formData.technology}
              onChange={(e) => setFormData({ ...formData, technology: e.target.value })}
              options={TECHNOLOGY_OPTIONS}
              required
              fullWidth
              placeholder="Select technology"
            />
            <Input
              id="tribe"
              label="Tribe"
              value={formData.tribe}
              onChange={(e) => setFormData({ ...formData, tribe: e.target.value })}
              required
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
            <div className={styles.checkboxGroup}>
              <label>
                <input
                  type="checkbox"
                  checked={formData.retired}
                  onChange={(e) => setFormData({ ...formData, retired: e.target.checked })}
                />
                <span>Retired</span>
              </label>
            </div>
          </div>
        );
      case 2:
        const selectedCluster = clusters.find((c) => c.id === parseInt(formData.cluster_id));
        const clusterHasConsoleUrl = selectedCluster?.console_url;
        return (
          <div className={styles.formStep}>
            <div className={styles.infoSection}>
              <p className={styles.infoText}>
                Cluster information (auto-populated from selected cluster):
              </p>
            </div>
            <Input
              id="cluster_name"
              label="Cluster Name"
              value={formData.cluster_name}
              disabled
              fullWidth
            />
            <Input
              id="console_url"
              label="Console URL"
              type="url"
              value={formData.console_url || ''}
              onChange={(e) => setFormData({ ...formData, console_url: e.target.value })}
              disabled={!!clusterHasConsoleUrl}
              required
              fullWidth
              placeholder={clusterHasConsoleUrl ? '' : 'Enter console URL (e.g., https://console.example.com)'}
            />
            {!clusterHasConsoleUrl && (
              <p className={styles.warningText}>
                Note: Selected cluster does not have a console URL configured. Please enter it manually.
              </p>
            )}
          </div>
        );
      case 3:
        return (
          <div className={styles.formStep}>
            <Input
              id="tech_read_token"
              label="Tech Read Token"
              type="password"
              value={formData.tech_read_token}
              onChange={(e) => setFormData({ ...formData, tech_read_token: e.target.value })}
              required
              fullWidth
            />
            <Input
              id="tech_edit_credentials"
              label="Tech Edit Credentials"
              type="password"
              value={formData.tech_edit_credentials}
              onChange={(e) =>
                setFormData({ ...formData, tech_edit_credentials: e.target.value })
              }
              required
              fullWidth
            />
            <Input
              id="wrapper_cluster_token"
              label="Wrapper Cluster Token"
              type="password"
              value={formData.wrapper_cluster_token}
              onChange={(e) =>
                setFormData({ ...formData, wrapper_cluster_token: e.target.value })
              }
              required
              fullWidth
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={styles.projects}>
      <div className={styles.header}>
        <div>
          <h2>Projects</h2>
          <p className={styles.subtitle}>Manage and onboard OpenShift projects/namespaces</p>
        </div>
        {isAdmin && <Button onClick={handleCreate}>+ Add Project</Button>}
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
            placeholder="Search by project name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            fullWidth
          />
          <Select
            id="filter_cluster"
            placeholder="Filter by Cluster"
            value={filters.cluster_id}
            onChange={(e) => setFilters({ ...filters, cluster_id: e.target.value })}
            options={[{ value: '', label: 'All Clusters' }, ...clusterOptions]}
          />
          <Select
            id="filter_technology"
            placeholder="Filter by Technology"
            value={filters.technology}
            onChange={(e) => setFilters({ ...filters, technology: e.target.value })}
            options={[{ value: '', label: 'All Technologies' }, ...TECHNOLOGY_OPTIONS]}
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
        title={`Create Project - Step ${formStep} of 3`}
        size="lg"
        footer={
          <>
            {formStep > 1 && (
              <Button variant="secondary" onClick={handlePrevStep}>
                Previous
              </Button>
            )}
            {formStep < 3 ? (
              <Button onClick={handleNextStep} disabled={!validateStep(formStep)}>
                Next
              </Button>
            ) : (
              <Button type="submit" form="create-project-form">
                Create Project
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={() => {
                setShowCreateModal(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
          </>
        }
      >
        <form id="create-project-form" onSubmit={handleCreateSubmit}>
          {renderCreateFormStep()}
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          resetForm();
        }}
        title="Edit Project"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button type="submit" form="edit-project-form">
              Update
            </Button>
          </>
        }
      >
        <form id="edit-project-form" onSubmit={handleEditSubmit}>
          <div className={styles.form}>
            <Input
              id="edit_project_name"
              label="Project Name"
              value={formData.project_name}
              onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
              required
              fullWidth
            />
            <Select
              id="edit_technology"
              label="Technology"
              value={formData.technology}
              onChange={(e) => setFormData({ ...formData, technology: e.target.value })}
              options={TECHNOLOGY_OPTIONS}
              required
              fullWidth
            />
            <Input
              id="edit_tribe"
              label="Tribe"
              value={formData.tribe}
              onChange={(e) => setFormData({ ...formData, tribe: e.target.value })}
              required
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
            <div className={styles.infoSection}>
              <p className={styles.infoText}>Cluster information (from cluster):</p>
            </div>
            <Input
              id="edit_cluster_name"
              label="Cluster Name"
              value={formData.cluster_name}
              disabled
              fullWidth
            />
            <Input
              id="edit_console_url"
              label="Console URL"
              type="url"
              value={formData.console_url || ''}
              onChange={(e) => setFormData({ ...formData, console_url: e.target.value })}
              required
              fullWidth
            />
            <div className={styles.checkboxGroup}>
              <label>
                <input
                  type="checkbox"
                  checked={formData.retired}
                  onChange={(e) => setFormData({ ...formData, retired: e.target.checked })}
                />
                <span>Retired</span>
              </label>
            </div>
          </div>
        </form>
      </Modal>

      {/* Update Credentials Modal */}
      <Modal
        isOpen={showCredentialsModal}
        onClose={() => {
          setShowCredentialsModal(false);
          setCredentialsData({
            tech_read_token: '',
            tech_edit_credentials: '',
            wrapper_cluster_token: '',
          });
          setSelectedProject(null);
        }}
        title="Update Credentials"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => {
                setShowCredentialsModal(false);
                setCredentialsData({
                  tech_read_token: '',
                  tech_edit_credentials: '',
                  wrapper_cluster_token: '',
                });
                setSelectedProject(null);
              }}
            >
              Cancel
            </Button>
            <Button type="submit" form="credentials-form">
              Update Credentials
            </Button>
          </>
        }
      >
        <form id="credentials-form" onSubmit={handleCredentialsSubmit}>
          <div className={styles.form}>
            <Input
              id="cred_tech_read_token"
              label="Tech Read Token"
              type="password"
              value={credentialsData.tech_read_token}
              onChange={(e) =>
                setCredentialsData({ ...credentialsData, tech_read_token: e.target.value })
              }
              required
              fullWidth
            />
            <Input
              id="cred_tech_edit_credentials"
              label="Tech Edit Credentials"
              type="password"
              value={credentialsData.tech_edit_credentials}
              onChange={(e) =>
                setCredentialsData({
                  ...credentialsData,
                  tech_edit_credentials: e.target.value,
                })
              }
              required
              fullWidth
            />
            <Input
              id="cred_wrapper_cluster_token"
              label="Wrapper Cluster Token"
              type="password"
              value={credentialsData.wrapper_cluster_token}
              onChange={(e) =>
                setCredentialsData({
                  ...credentialsData,
                  wrapper_cluster_token: e.target.value,
                })
              }
              required
              fullWidth
            />
          </div>
        </form>
      </Modal>

      {/* Projects Table */}
      <div className={styles.table}>
        {filteredProjects.length === 0 ? (
          <Card className={styles.empty}>
            <p>No projects found. Create your first project to get started.</p>
          </Card>
        ) : (
          <table className={styles.tableElement}>
            <thead>
              <tr>
                <th>Project Name</th>
                <th>Cluster</th>
                <th>Technology</th>
                <th>Tribe</th>
                <th>Tier</th>
                <th>Status</th>
                <th>Retired</th>
                {isAdmin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {filteredProjects.map((project) => (
                <tr key={project.id}>
                  <td>{project.project_name}</td>
                  <td>{project.cluster_name}</td>
                  <td>{project.technology}</td>
                  <td>{project.tribe}</td>
                  <td>{project.tier}</td>
                  <td>
                    <Badge variant={project.status === 'Active' ? 'success' : 'neutral'}>
                      {project.status}
                    </Badge>
                  </td>
                  <td>
                    <Badge variant={project.retired ? 'warning' : 'success'}>
                      {project.retired ? 'Yes' : 'No'}
                    </Badge>
                  </td>
                  {isAdmin && (
                    <td>
                      <div className={styles.actions}>
                        <Button size="sm" variant="secondary" onClick={() => handleEdit(project)}>
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleUpdateCredentials(project)}
                        >
                          Credentials
                        </Button>
                        {project.retired ? (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleActivate(project)}
                          >
                            Activate
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => handleRetire(project)}
                          >
                            Retire
                          </Button>
                        )}
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