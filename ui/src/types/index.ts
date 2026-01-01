// User types
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'Administrator' | 'Viewer' | 'Operator';
  is_active: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Cluster types
export interface Cluster {
  id: number;
  cluster_name: string;
  console_url: string | null;
  api_url: string | null;
  environment: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClusterCreate {
  cluster_name: string;
  console_url?: string;
  api_url?: string;
  environment?: string;
}

// Project types
export interface Project {
  id: number;
  project_name: string;
  cluster_id: number;
  technology: string;
  tribe: string;
  tier: string;
  cluster_name: string;
  console_url: string;
  retired: boolean;
  status: string;
  onboarded_at: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  project_name: string;
  cluster_id: number;
  technology: string;
  tribe: string;
  tier: string;
  cluster_name: string;
  console_url: string;
  retired: boolean;
  tech_read_token: string;
  tech_edit_credentials: string;
  wrapper_cluster_token: string;
}

// Target types
export interface Target {
  id: number;
  name: string;
  deployment_type: string;
  hostname: string | null;
  ip_address: string | null;
  project_id: number | null;
  cluster_id: number | null;
  tier: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// JDK Version types
export interface JDKVersion {
  id: number;
  major_version: number;
  vendor: string;
  compliance_status: 'Compliant' | 'Non-Compliant' | 'CompliantStar';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Common types
export interface ApiError {
  detail: string;
  status?: number;
}
