import apiClient from './client';
import { Cluster, ClusterCreate } from '../../types';

export const clustersApi = {
  list: async (): Promise<Cluster[]> => {
    const response = await apiClient.get<Cluster[]>('/api/clusters');
    return response.data;
  },

  get: async (id: number): Promise<Cluster> => {
    const response = await apiClient.get<Cluster>(`/api/clusters/${id}`);
    return response.data;
  },

  create: async (data: ClusterCreate): Promise<Cluster> => {
    const response = await apiClient.post<Cluster>('/api/clusters', data);
    return response.data;
  },

  update: async (id: number, data: Partial<ClusterCreate>): Promise<Cluster> => {
    const response = await apiClient.put<Cluster>(`/api/clusters/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/clusters/${id}`);
  },
};
