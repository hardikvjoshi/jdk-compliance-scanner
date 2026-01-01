#!/usr/bin/env python3
"""
Interactive CLI script to test API endpoints
Prompts for inputs and saves outputs to dated log file
"""
import os
import sys
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from getpass import getpass

# Add backend directory to path for imports if needed
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, backend_dir)

BASE_URL = "http://localhost:8000"
LOG_DIR = "logs"


class APITester:
    """Interactive API testing CLI"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.log_file: Optional[str] = None
        self._setup_log_file()
    
    def _setup_log_file(self):
        """Create log file with date"""
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, mode=0o755)
        
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(LOG_DIR, f"output_{date_str}.log")
    
    def log(self, message: str):
        """Write to log file and print to console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        print(message)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message)
    
    def log_response(self, method: str, endpoint: str, response: requests.Response):
        """Log API response"""
        self.log(f"\n{'='*80}")
        self.log(f"{method} {endpoint}")
        self.log(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            self.log(f"Response:\n{json.dumps(response_data, indent=2)}")
        except:
            self.log(f"Response (text): {response.text}")
        
        self.log(f"{'='*80}\n")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make API request with authentication"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("headers", {}).update(self.headers)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, **kwargs)
            elif method.upper() == "POST":
                response = requests.post(url, **kwargs)
            elif method.upper() == "PUT":
                response = requests.put(url, **kwargs)
            elif method.upper() == "DELETE":
                response = requests.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            self.log_response(method, endpoint, response)
            return response
        except requests.exceptions.ConnectionError:
            self.log(f"ERROR: Could not connect to {self.base_url}")
            self.log("Make sure the server is running with: cd backend && python run.py")
            sys.exit(1)
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            raise
    
    def login(self):
        """Login and get JWT token"""
        self.log("\n=== LOGIN ===")
        username = input("Username: ").strip()
        password = getpass("Password: ")
        
        response = self.make_request("POST", "/api/auth/login", json={
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers["Authorization"] = f"Bearer {self.token}"
            self.log("✓ Login successful")
        else:
            self.log("✗ Login failed")
            self.token = None
    
    def test_root(self):
        """Test root endpoint"""
        self.log("\n=== Testing GET / ===")
        self.make_request("GET", "/")
    
    def test_health(self):
        """Test health endpoint"""
        self.log("\n=== Testing GET /health ===")
        self.make_request("GET", "/health")
    
    def test_validate_token(self):
        """Test token validation"""
        self.log("\n=== Testing GET /api/auth/validate ===")
        if not self.token:
            self.log("Please login first")
            return
        self.make_request("GET", "/api/auth/validate")
    
    def test_list_clusters(self):
        """Test list clusters"""
        self.log("\n=== Testing GET /api/clusters ===")
        self.make_request("GET", "/api/clusters")
    
    def test_create_cluster(self):
        """Test create cluster"""
        self.log("\n=== Testing POST /api/clusters ===")
        cluster_name = input("Cluster name: ").strip()
        console_url = input("Console URL (optional): ").strip() or None
        api_url = input("API URL (optional): ").strip() or None
        environment = input("Environment (Dev/UAT/Production, optional): ").strip() or None
        
        data = {"cluster_name": cluster_name}
        if console_url:
            data["console_url"] = console_url
        if api_url:
            data["api_url"] = api_url
        if environment:
            data["environment"] = environment
        
        self.make_request("POST", "/api/clusters", json=data)
    
    def test_get_cluster(self):
        """Test get cluster"""
        self.log("\n=== Testing GET /api/clusters/{id} ===")
        cluster_id = input("Cluster ID: ").strip()
        self.make_request("GET", f"/api/clusters/{cluster_id}")
    
    def test_update_cluster(self):
        """Test update cluster"""
        self.log("\n=== Testing PUT /api/clusters/{id} ===")
        cluster_id = input("Cluster ID: ").strip()
        cluster_name = input("Cluster name (optional, press Enter to skip): ").strip() or None
        console_url = input("Console URL (optional, press Enter to skip): ").strip() or None
        api_url = input("API URL (optional, press Enter to skip): ").strip() or None
        environment = input("Environment (optional, press Enter to skip): ").strip() or None
        
        data = {}
        if cluster_name:
            data["cluster_name"] = cluster_name
        if console_url:
            data["console_url"] = console_url
        if api_url:
            data["api_url"] = api_url
        if environment:
            data["environment"] = environment
        
        self.make_request("PUT", f"/api/clusters/{cluster_id}", json=data)
    
    def test_delete_cluster(self):
        """Test delete cluster"""
        self.log("\n=== Testing DELETE /api/clusters/{id} ===")
        cluster_id = input("Cluster ID: ").strip()
        confirm = input(f"Are you sure you want to delete cluster {cluster_id}? (yes/no): ").strip()
        if confirm.lower() == "yes":
            self.make_request("DELETE", f"/api/clusters/{cluster_id}")
        else:
            self.log("Deletion cancelled")
    
    def test_list_projects(self):
        """Test list projects"""
        self.log("\n=== Testing GET /api/projects ===")
        filters = {}
        cluster_id = input("Filter by Cluster ID (optional, press Enter to skip): ").strip()
        if cluster_id:
            filters["cluster_id"] = int(cluster_id)
        tier = input("Filter by Tier (optional, press Enter to skip): ").strip()
        if tier:
            filters["tier"] = tier
        tribe = input("Filter by Tribe (optional, press Enter to skip): ").strip()
        if tribe:
            filters["tribe"] = tribe
        
        query_string = "&".join([f"{k}={v}" for k, v in filters.items()])
        endpoint = f"/api/projects?{query_string}" if query_string else "/api/projects"
        self.make_request("GET", endpoint)
    
    def test_create_project(self):
        """Test create project"""
        self.log("\n=== Testing POST /api/projects ===")
        self.log("Enter project details (all fields required):")
        project_name = input("Project name: ").strip()
        cluster_id = input("Cluster ID: ").strip()
        technology = input("Technology (Java/Python/Node/Go/Mixed): ").strip()
        tribe = input("Tribe: ").strip()
        tier = input("Tier (Dev/UAT/Production): ").strip()
        cluster_name = input("Cluster name: ").strip()
        console_url = input("Console URL: ").strip()
        tech_read_token = getpass("Tech read token: ")
        tech_edit_credentials = getpass("Tech edit credentials: ")
        wrapper_cluster_token = getpass("Wrapper cluster token: ")
        
        data = {
            "project_name": project_name,
            "cluster_id": int(cluster_id),
            "technology": technology,
            "tribe": tribe,
            "tier": tier,
            "cluster_name": cluster_name,
            "console_url": console_url,
            "tech_read_token": tech_read_token,
            "tech_edit_credentials": tech_edit_credentials,
            "wrapper_cluster_token": wrapper_cluster_token,
            "retired": False
        }
        
        self.make_request("POST", "/api/projects", json=data)
    
    def test_get_project(self):
        """Test get project"""
        self.log("\n=== Testing GET /api/projects/{id} ===")
        project_id = input("Project ID: ").strip()
        self.make_request("GET", f"/api/projects/{project_id}")
    
    def test_list_jdk_versions(self):
        """Test list JDK versions"""
        self.log("\n=== Testing GET /api/jdk-versions ===")
        vendor = input("Filter by Vendor (optional, press Enter to skip): ").strip()
        compliance_status = input("Filter by Compliance Status (optional, press Enter to skip): ").strip()
        
        filters = []
        if vendor:
            filters.append(f"vendor={vendor}")
        if compliance_status:
            filters.append(f"compliance_status={compliance_status}")
        
        endpoint = f"/api/jdk-versions?{'&'.join(filters)}" if filters else "/api/jdk-versions"
        self.make_request("GET", endpoint)
    
    def test_create_jdk_version(self):
        """Test create JDK version"""
        self.log("\n=== Testing POST /api/jdk-versions ===")
        major_version = input("Major version (e.g., 11, 17, 21): ").strip()
        vendor = input("Vendor (e.g., Oracle, Zulu, Amazon): ").strip()
        compliance_status = input("Compliance Status (Compliant/Non-Compliant/CompliantStar): ").strip()
        is_active = input("Is Active? (true/false, default: true): ").strip().lower()
        is_active = is_active != "false"
        
        data = {
            "major_version": int(major_version),
            "vendor": vendor,
            "compliance_status": compliance_status,
            "is_active": is_active
        }
        
        self.make_request("POST", "/api/jdk-versions", json=data)
    
    def test_list_targets(self):
        """Test list targets"""
        self.log("\n=== Testing GET /api/targets ===")
        deployment_type = input("Filter by Deployment Type (optional, press Enter to skip): ").strip()
        tier = input("Filter by Tier (optional, press Enter to skip): ").strip()
        status = input("Filter by Status (optional, press Enter to skip): ").strip()
        
        filters = []
        if deployment_type:
            filters.append(f"deployment_type={deployment_type}")
        if tier:
            filters.append(f"tier={tier}")
        if status:
            filters.append(f"status={status}")
        
        endpoint = f"/api/targets?{'&'.join(filters)}" if filters else "/api/targets"
        self.make_request("GET", endpoint)
    
    def test_create_target(self):
        """Test create target"""
        self.log("\n=== Testing POST /api/targets ===")
        name = input("Target name: ").strip()
        deployment_type = input("Deployment Type (Unix/Cloud/Windows): ").strip()
        hostname = input("Hostname (optional, press Enter to skip): ").strip() or None
        ip_address = input("IP Address (optional, press Enter to skip): ").strip() or None
        tier = input("Tier (Dev/UAT/Production): ").strip()
        
        self.log("\nConnection Config (JSON format):")
        self.log("Example for Unix: {\"hostname\": \"server.com\", \"username\": \"user\", \"password\": \"pass\"}")
        self.log("Example for AWS: {\"provider\": \"aws\", \"instance_id\": \"i-123\", \"region\": \"us-east-1\"}")
        connection_config_str = input("Connection Config (JSON): ").strip()
        try:
            connection_config = json.loads(connection_config_str)
        except json.JSONDecodeError:
            self.log("ERROR: Invalid JSON format")
            return
        
        data = {
            "name": name,
            "deployment_type": deployment_type,
            "tier": tier,
            "connection_config": connection_config
        }
        if hostname:
            data["hostname"] = hostname
        if ip_address:
            data["ip_address"] = ip_address
        
        self.make_request("POST", "/api/targets", json=data)
    
    def test_get_target(self):
        """Test get target"""
        self.log("\n=== Testing GET /api/targets/{id} ===")
        target_id = input("Target ID: ").strip()
        self.make_request("GET", f"/api/targets/{target_id}")
    
    def test_update_target(self):
        """Test update target"""
        self.log("\n=== Testing PUT /api/targets/{id} ===")
        target_id = input("Target ID: ").strip()
        name = input("Name (optional, press Enter to skip): ").strip() or None
        hostname = input("Hostname (optional, press Enter to skip): ").strip() or None
        tier = input("Tier (optional, press Enter to skip): ").strip() or None
        status = input("Status (optional, press Enter to skip): ").strip() or None
        
        data = {}
        if name:
            data["name"] = name
        if hostname:
            data["hostname"] = hostname
        if tier:
            data["tier"] = tier
        if status:
            data["status"] = status
        
        self.make_request("PUT", f"/api/targets/{target_id}", json=data)
    
    def test_delete_target(self):
        """Test delete target"""
        self.log("\n=== Testing DELETE /api/targets/{id} ===")
        target_id = input("Target ID: ").strip()
        confirm = input(f"Are you sure you want to delete target {target_id}? (yes/no): ").strip()
        if confirm.lower() == "yes":
            self.make_request("DELETE", f"/api/targets/{target_id}")
        else:
            self.log("Deletion cancelled")
    
    def show_menu(self):
        """Display main menu"""
        menu = """
╔═══════════════════════════════════════════════════════════════════╗
║                    API Testing CLI Menu                           ║
╚═══════════════════════════════════════════════════════════════════╝

Authentication:
  1. Login
  2. Validate Token

System:
  3. Root (GET /)
  4. Health (GET /health)

Clusters:
  5. List Clusters (GET /api/clusters)
  6. Create Cluster (POST /api/clusters)
  7. Get Cluster (GET /api/clusters/{id})
  8. Update Cluster (PUT /api/clusters/{id})
  9. Delete Cluster (DELETE /api/clusters/{id})

Projects:
  10. List Projects (GET /api/projects)
  11. Create Project (POST /api/projects)
  12. Get Project (GET /api/projects/{id})

JDK Versions:
  13. List JDK Versions (GET /api/jdk-versions)
  14. Create JDK Version (POST /api/jdk-versions)

Targets:
  15. List Targets (GET /api/targets)
  16. Create Target (POST /api/targets)
  17. Get Target (GET /api/targets/{id})
  18. Update Target (PUT /api/targets/{id})
  19. Delete Target (DELETE /api/targets/{id})

  0. Exit

Log file: {log_file}
"""
        print(menu.format(log_file=self.log_file))
    
    def run(self):
        """Run interactive CLI"""
        self.log(f"API Tester started - Log file: {self.log_file}")
        self.log(f"Base URL: {self.base_url}")
        
        handlers = {
            "1": self.login,
            "2": self.test_validate_token,
            "3": self.test_root,
            "4": self.test_health,
            "5": self.test_list_clusters,
            "6": self.test_create_cluster,
            "7": self.test_get_cluster,
            "8": self.test_update_cluster,
            "9": self.test_delete_cluster,
            "10": self.test_list_projects,
            "11": self.test_create_project,
            "12": self.test_get_project,
            "13": self.test_list_jdk_versions,
            "14": self.test_create_jdk_version,
            "15": self.test_list_targets,
            "16": self.test_create_target,
            "17": self.test_get_target,
            "18": self.test_update_target,
            "19": self.test_delete_target,
        }
        
        while True:
            self.show_menu()
            choice = input("Select option: ").strip()
            
            if choice == "0":
                self.log("\nExiting...")
                break
            
            if choice in handlers:
                try:
                    handlers[choice]()
                except KeyboardInterrupt:
                    self.log("\n\nOperation cancelled by user")
                except Exception as e:
                    self.log(f"\nERROR: {str(e)}")
                    import traceback
                    self.log(traceback.format_exc())
            else:
                self.log("Invalid option. Please try again.")
            
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    tester = APITester()
    tester.run()

