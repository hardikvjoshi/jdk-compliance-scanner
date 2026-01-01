import apiClient from './client';
import { Project, ProjectCreate } from '../../types';

export interface ProjectFilters {
  cluster_id?: number;
  tribe?: string;
  technology?: string;
  tier?: string;
  retired?: boolean;
  status?: string;
}

export const projectsApi = {
  list: async (filters?: ProjectFilters): Promise<Project[]> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
    }
    const response = await apiClient.get<Project[]>(`/api/projects?${params.toString()}`);
    return response.data;
  },

  get: async (id: number): Promise<Project> => {
    const response = await apiClient.get<Project>(`/api/projects/${id}`);
    return response.data;
  },

  create: async (data: ProjectCreate): Promise<Project> => {
    const response = await apiClient.post<Project>('/api/projects', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Omit<ProjectCreate, 'tech_read_token' | 'tech_edit_credentials' | 'wrapper_cluster_token'>>): Promise<Project> => {
    const response = await apiClient.put<Project>(`/api/projects/${id}`, data);
    return response.data;
  },

  updateCredentials: async (id: number, credentials: {
    tech_read_token: string;
    tech_edit_credentials: string;
    wrapper_cluster_token: string;
  }): Promise<Project> => {
    const response = await apiClient.put<Project>(`/api/projects/${id}/credentials`, credentials);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/projects/${id}`);
  },

  activate: async (id: number): Promise<Project> => {
    const response = await apiClient.post<Project>(`/api/projects/${id}/activate`);
    return response.data;
  },

  validate: async (id: number): Promise<{ valid: boolean; errors: string[]; warnings: string[] }> => {
    const response = await apiClient.get(`/api/projects/${id}/validation`);
    return response.data;
  },
};
