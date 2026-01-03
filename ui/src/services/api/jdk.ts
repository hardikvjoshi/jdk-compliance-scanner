import apiClient from './client';
import { JDKVersion } from '../../types';

export interface JDKVersionCreate {
  major_version: number;
  vendor: string;
  compliance_status: 'Compliant' | 'Non-Compliant' | 'CompliantStar';
  is_active?: boolean;
}

export interface JDKVersionFilters {
  vendor?: string;
  compliance_status?: string;
  is_active?: boolean;
}

export const jdkApi = {
  list: async (filters?: JDKVersionFilters): Promise<JDKVersion[]> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
    }
    const response = await apiClient.get<JDKVersion[]>(`/api/jdk-versions?${params.toString()}`);
    return response.data;
  },

  get: async (id: number): Promise<JDKVersion> => {
    const response = await apiClient.get<JDKVersion>(`/api/jdk-versions/${id}`);
    return response.data;
  },

  create: async (data: JDKVersionCreate): Promise<JDKVersion> => {
    const response = await apiClient.post<JDKVersion>('/api/jdk-versions', data);
    return response.data;
  },

  update: async (id: number, data: Partial<JDKVersionCreate>): Promise<JDKVersion> => {
    const response = await apiClient.put<JDKVersion>(`/api/jdk-versions/${id}`, data);
    return response.data;
  },

  updateComplianceStatus: async (id: number, compliance_status: string): Promise<JDKVersion> => {
    const response = await apiClient.put<JDKVersion>(
      `/api/jdk-versions/${id}/compliance-status?compliance_status=${encodeURIComponent(compliance_status)}`
    );
    return response.data;
  },
};
