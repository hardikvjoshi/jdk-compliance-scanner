import apiClient from './client';
import { Target } from '../../types';

export interface TargetCreate {
  name: string;
  deployment_type: string;
  hostname?: string;
  ip_address?: string;
  connection_config: Record<string, any>;
  project_id?: number;
  cluster_id?: number;
  tier: string;
}

export interface TargetFilters {
  deployment_type?: string;
  tier?: string;
  status?: string;
}

export const targetsApi = {
  list: async (filters?: TargetFilters): Promise<Target[]> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
    }
    const response = await apiClient.get<Target[]>(`/api/targets?${params.toString()}`);
    return response.data;
  },

  get: async (id: number): Promise<Target> => {
    const response = await apiClient.get<Target>(`/api/targets/${id}`);
    return response.data;
  },

  create: async (data: TargetCreate): Promise<Target> => {
    const response = await apiClient.post<Target>('/api/targets', data);
    return response.data;
  },

  update: async (id: number, data: Partial<TargetCreate>): Promise<Target> => {
    const response = await apiClient.put<Target>(`/api/targets/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/targets/${id}`);
  },
};
