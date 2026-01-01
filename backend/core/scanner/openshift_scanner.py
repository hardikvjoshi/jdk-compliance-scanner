"""
OpenShift Scanner - Implementation for OpenShift pods
"""
import subprocess
import os
from typing import Dict, Any, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from core.scanner.base import BaseScanner, ScanResult
from core.database.models import Project, Cluster


class OpenShiftScanner(BaseScanner):
    """
    Scanner implementation for OpenShift clusters
    Uses OC API (Kubernetes Python client) to execute commands in pods
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize OpenShift scanner
        
        Args:
            config_dict: Configuration containing:
                - project: Project database object or dict with project info
                - cluster: Cluster database object or dict with cluster info
                - pod_name: Name of pod to scan (optional, will scan all pods if not provided)
                - namespace: Namespace/project name (from project.project_name)
        """
        super().__init__(config_dict)
        self.project = config_dict.get("project")
        self.cluster = config_dict.get("cluster")
        self.pod_name = config_dict.get("pod_name")
        self.namespace = config_dict.get("namespace")
        
        # Extract credentials from project
        if isinstance(self.project, Project):
            self.read_token = self._decrypt_credential(self.project.tech_read_token)
            self.edit_credentials = self._decrypt_credential(self.project.tech_edit_credentials)
            self.namespace = self.project.project_name
        elif isinstance(self.project, dict):
            self.read_token = self.project.get("tech_read_token")
            self.edit_credentials = self.project.get("tech_edit_credentials")
            self.namespace = self.project.get("project_name")
        
        # Extract cluster info
        if isinstance(self.cluster, Cluster):
            self.api_url = self.cluster.api_url
            self.cluster_name = self.cluster.cluster_name
        elif isinstance(self.cluster, dict):
            self.api_url = self.cluster.get("api_url")
            self.cluster_name = self.cluster.get("cluster_name")
        
        self.k8s_client: Optional[client.CoreV1Api] = None
        self._oc_configured = False
    
    def _decrypt_credential(self, encrypted_credential: str) -> str:
        """Decrypt a credential using the encryption manager"""
        from core.database.encryption import get_encryption_manager
        encryptor = get_encryption_manager()
        try:
            return encryptor.decrypt(encrypted_credential)
        except Exception:
            # If decryption fails, assume it's not encrypted (for backward compatibility)
            return encrypted_credential
    
    def connect(self) -> bool:
        """
        Establish connection to OpenShift cluster using OC login
        Uses tech_read_token for authentication
        """
        if not self.read_token:
            return False
        
        try:
            # Use OC command line tool to login
            # OC login with token
            login_cmd = [
                "oc", "login",
                self.api_url or f"https://api.{self.cluster_name}",
                f"--token={self.read_token}",
                "--insecure-skip-tls-verify=true"  # Adjust based on cluster config
            ]
            
            result = subprocess.run(
                login_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.connected = True
                self._oc_configured = True
                return True
            else:
                self.handle_errors(
                    Exception(f"OC login failed: {result.stderr}"),
                    {"operation": "connect", "cluster": self.cluster_name}
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.handle_errors(
                Exception("OC login timeout"),
                {"operation": "connect", "cluster": self.cluster_name}
            )
            return False
        except FileNotFoundError:
            # OC command not found, try using Kubernetes Python client
            return self._connect_via_k8s_client()
        except Exception as e:
            self.handle_errors(e, {"operation": "connect", "cluster": self.cluster_name})
            return False
    
    def _connect_via_k8s_client(self) -> bool:
        """
        Alternative connection method using Kubernetes Python client
        """
        try:
            # Create kubeconfig from token
            kubeconfig_content = f"""
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: {self.api_url}
    insecure-skip-tls-verify: true
  name: {self.cluster_name}
contexts:
- context:
    cluster: {self.cluster_name}
    user: {self.cluster_name}-user
  name: {self.cluster_name}
current-context: {self.cluster_name}
users:
- name: {self.cluster_name}-user
  user:
    token: {self.read_token}
"""
            
            # Write temporary kubeconfig
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
                f.write(kubeconfig_content)
                temp_kubeconfig = f.name
            
            try:
                # Load kubeconfig
                config.load_kube_config(config_file=temp_kubeconfig)
                self.k8s_client = client.CoreV1Api()
                self.connected = True
                return True
            finally:
                # Clean up temp file
                os.unlink(temp_kubeconfig)
                
        except Exception as e:
            self.handle_errors(e, {"operation": "connect_k8s_client", "cluster": self.cluster_name})
            return False
    
    def disconnect(self):
        """Close connection"""
        if self._oc_configured:
            # OC logout
            try:
                subprocess.run(["oc", "logout"], capture_output=True, timeout=10)
            except Exception:
                pass
        
        self.connected = False
        self.k8s_client = None
        self._oc_configured = False
    
    def execute_command(self, command: str) -> tuple:
        """
        Execute command in pod using OC exec or Kubernetes Python client
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        if not self.connected:
            raise RuntimeError("Not connected to cluster")
        
        if not self.pod_name:
            raise ValueError("pod_name is required for command execution")
        
        try:
            if self._oc_configured:
                # Use OC exec
                oc_cmd = [
                    "oc", "exec", self.pod_name,
                    "-n", self.namespace,
                    "--", "sh", "-c", command
                ]
                
                result = subprocess.run(
                    oc_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                return result.stdout, result.stderr, result.returncode
            elif self.k8s_client:
                # Use Kubernetes Python client
                try:
                    from kubernetes.stream import stream
                    exec_command = ["sh", "-c", command]
                    resp = stream(
                        self.k8s_client.connect_get_namespaced_pod_exec,
                        self.pod_name,
                        self.namespace,
                        command=exec_command,
                        stderr=True,
                        stdin=False,
                        stdout=True,
                        tty=False
                    )
                    
                    stdout = ""
                    stderr = ""
                    while resp.is_open():
                        resp.update(timeout=1)
                        if resp.peek_stdout():
                            stdout += resp.read_stdout()
                        if resp.peek_stderr():
                            stderr += resp.read_stderr()
                    
                    return_code = 0  # Kubernetes exec doesn't provide return code directly
                    return stdout, stderr, return_code
                except ImportError:
                    return "", "kubernetes.stream not available", 1
            else:
                raise RuntimeError("No connection method available")
                
        except subprocess.TimeoutExpired:
            return "", "Command execution timeout", 1
        except ApiException as e:
            return "", f"Kubernetes API error: {str(e)}", 1
        except Exception as e:
            self.handle_errors(e, {
                "operation": "execute_command",
                "pod": self.pod_name,
                "namespace": self.namespace,
                "command": command
            })
            return "", str(e), 1



