# Backend Dataflow Diagram

This document illustrates the dataflow through the JDK Compliance Scanner backend system.

## High-Level Dataflow

```mermaid
flowchart TD
    Client[Client/API Consumer] -->|HTTP Request| API[FastAPI Application]
    API -->|Requires Auth| AuthMiddleware[Authentication Middleware]
    AuthMiddleware -->|JWT Token| ValidateToken[Validate JWT Token]
    ValidateToken -->|Valid User| RouteHandler[Route Handler]
    ValidateToken -->|Invalid| ErrorResponse[401 Unauthorized]
    
    RouteHandler -->|CRUD Operations| DBSession[Database Session]
    RouteHandler -->|Scan Operations| ScannerFactory[Scanner Factory]
    RouteHandler -->|Encryption| EncryptionMgr[Encryption Manager]
    
    DBSession -->|Query/Insert/Update| SQLiteDB[(SQLite Database)]
    SQLiteDB -->|Results| DBSession
    DBSession -->|Data| RouteHandler
    
    ScannerFactory -->|Create Scanner| Scanner[Scanner Instance]
    Scanner -->|Connect| TargetSystem[Target System<br/>OpenShift/Unix/Cloud]
    TargetSystem -->|Execute Commands| Scanner
    Scanner -->|JDK Version Output| JDKDetector[JDK Detector]
    JDKDetector -->|Parsed Version| ComplianceChecker[Compliance Checker]
    ComplianceChecker -->|Check Against DB| SQLiteDB
    ComplianceChecker -->|Result| Scanner
    Scanner -->|Scan Result| RouteHandler
    
    EncryptionMgr -->|Encrypt| SensitiveData[Sensitive Data]
    EncryptionMgr -->|Decrypt| SensitiveData
    
    RouteHandler -->|Response Data| API
    API -->|JSON Response| Client
    
    ErrorResponse -->|Error JSON| Client
    
    style Client fill:#e1f5ff
    style API fill:#fff4e1
    style SQLiteDB fill:#ffe1f5
    style TargetSystem fill:#e1ffe1
    style Scanner fill:#f0e1ff
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant AuthMiddleware
    participant Authenticator
    participant Database
    participant RouteHandler
    
    Client->>FastAPI: POST /api/auth/login<br/>{username, password}
    FastAPI->>Authenticator: authenticate_user()
    Authenticator->>Database: Query User by username
    Database-->>Authenticator: User record
    Authenticator->>Authenticator: Verify password hash
    Authenticator->>Authenticator: create_access_token()
    Authenticator-->>FastAPI: JWT Token
    FastAPI-->>Client: {access_token, user}
    
    Client->>FastAPI: GET /api/projects<br/>Authorization: Bearer <token>
    FastAPI->>AuthMiddleware: get_current_user()
    AuthMiddleware->>Authenticator: decode_access_token()
    Authenticator-->>AuthMiddleware: Token payload
    AuthMiddleware->>Database: Query User by username
    Database-->>AuthMiddleware: User record
    AuthMiddleware->>AuthMiddleware: Check user.is_active
    AuthMiddleware-->>FastAPI: Current User
    FastAPI->>RouteHandler: Execute endpoint
    RouteHandler->>Database: Query Projects
    Database-->>RouteHandler: Project records
    RouteHandler-->>FastAPI: JSON Response
    FastAPI-->>Client: {projects: [...]}
```

## API Request Flow (CRUD Operations)

```mermaid
flowchart LR
    subgraph ClientLayer[Client Layer]
        HTTPReq[HTTP Request]
        HTTPResp[HTTP Response]
    end
    
    subgraph APILayer[API Layer]
        FastAPIApp[FastAPI App]
        Router[Router]
        RouteHandler[Route Handler]
    end
    
    subgraph AuthLayer[Authentication Layer]
        AuthMW[Auth Middleware]
        JWTValidate[JWT Validation]
        RoleCheck[Role Check]
    end
    
    subgraph BusinessLayer[Business Layer]
        ServiceLogic[Service Logic]
        Validation[Input Validation]
        Encryption[Encryption Manager]
    end
    
    subgraph DataLayer[Data Layer]
        DBSession[DB Session]
        Models[SQLAlchemy Models]
        SQLite[(SQLite DB)]
    end
    
    HTTPReq --> FastAPIApp
    FastAPIApp --> Router
    Router --> AuthMW
    AuthMW --> JWTValidate
    JWTValidate --> RoleCheck
    RoleCheck --> RouteHandler
    RouteHandler --> Validation
    Validation --> Encryption
    Encryption --> ServiceLogic
    ServiceLogic --> DBSession
    DBSession --> Models
    Models --> SQLite
    SQLite --> Models
    Models --> DBSession
    DBSession --> ServiceLogic
    ServiceLogic --> RouteHandler
    RouteHandler --> Router
    Router --> FastAPIApp
    FastAPIApp --> HTTPResp
    
    style HTTPReq fill:#e1f5ff
    style HTTPResp fill:#e1f5ff
    style SQLite fill:#ffe1f5
    style Encryption fill:#fff4e1
```

## Scanning Flow

```mermaid
sequenceDiagram
    participant API
    participant ScanHandler
    participant ScannerFactory
    participant Scanner
    participant TargetSystem
    participant JDKDetector
    participant ComplianceChecker
    participant Database
    
    API->>ScanHandler: POST /api/scans<br/>{targets, config}
    ScanHandler->>Database: Create ScanJob
    Database-->>ScanHandler: ScanJob ID
    
    loop For each target
        ScanHandler->>ScannerFactory: create_scanner(type, config)
        ScannerFactory-->>ScanHandler: Scanner Instance
        ScanHandler->>Scanner: scan(target)
        Scanner->>Scanner: connect()
        Scanner->>TargetSystem: SSH/API Connection
        TargetSystem-->>Scanner: Connection Established
        Scanner->>TargetSystem: execute_command("java -version")
        TargetSystem-->>Scanner: Command Output
        Scanner->>JDKDetector: parse_version_output()
        JDKDetector-->>Scanner: {version, vendor}
        Scanner->>ComplianceChecker: check_compliance(version, vendor)
        ComplianceChecker->>Database: Query JDK Versions
        Database-->>ComplianceChecker: JDK Version Records
        ComplianceChecker->>ComplianceChecker: Match & Check Status
        ComplianceChecker-->>Scanner: Compliance Status
        Scanner->>Scanner: disconnect()
        Scanner-->>ScanHandler: ScanResult
        ScanHandler->>Database: Save ScanResult
    end
    
    ScanHandler->>Database: Update ScanJob Status
    ScanHandler-->>API: Scan Results
    API-->>Client: {scan_job_id, results}
```

## Database Operations Flow

```mermaid
flowchart TD
    Request[API Request] -->|Data| RouteHandler[Route Handler]
    
    RouteHandler -->|Create| CreateOp[Create Operation]
    RouteHandler -->|Read| ReadOp[Read Operation]
    RouteHandler -->|Update| UpdateOp[Update Operation]
    RouteHandler -->|Delete| DeleteOp[Delete Operation]
    
    CreateOp -->|Encrypt| EncryptSensitive[Encrypt Sensitive Fields]
    EncryptSensitive -->|Insert| DBInsert[(Database Insert)]
    
    ReadOp -->|Query| DBQuery[(Database Query)]
    DBQuery -->|Decrypt| DecryptSensitive[Decrypt Sensitive Fields]
    DecryptSensitive -->|Return| RouteHandler
    
    UpdateOp -->|Encrypt| EncryptSensitive
    EncryptSensitive -->|Update| DBUpdate[(Database Update)]
    
    DeleteOp -->|Delete| DBDelete[(Database Delete)]
    
    DBInsert --> SQLite[(SQLite Database)]
    DBQuery --> SQLite
    DBUpdate --> SQLite
    DBDelete --> SQLite
    
    SQLite -->|Results| RouteHandler
    RouteHandler -->|Response| Response[HTTP Response]
    
    style SQLite fill:#ffe1f5
    style EncryptSensitive fill:#fff4e1
    style DecryptSensitive fill:#fff4e1
```

## Scanner Architecture Flow

```mermaid
graph TB
    subgraph Factory[Scanner Factory]
        FactoryCreate[create_scanner]
        Registry[Scanner Registry]
    end
    
    subgraph Scanners[Scanner Implementations]
        OpenShift[OpenShiftScanner]
        Unix[UnixScanner]
        AWS[AWSScanner]
        Azure[AzureScanner]
        GCP[GCPScanner]
        Cloud[CloudScanner]
    end
    
    subgraph Base[Base Scanner]
        BaseClass[BaseScanner]
        Connect[connect]
        Execute[execute_command]
        Scan[scan]
        Disconnect[disconnect]
    end
    
    subgraph Shared[Shared Components]
        JDKDetector[JDK Detector]
        ComplianceChecker[Compliance Checker]
        ErrorHandler[Error Handler]
        ParallelExecutor[Parallel Executor]
    end
    
    subgraph Targets[Target Systems]
        OpenShiftCluster[OpenShift Cluster]
        UnixHost[Unix/Linux Host]
        AWSInstance[AWS EC2]
        AzureVM[Azure VM]
        GCPVM[GCP Compute]
    end
    
    FactoryCreate --> Registry
    Registry -->|Creates| OpenShift
    Registry -->|Creates| Unix
    Registry -->|Creates| AWS
    Registry -->|Creates| Azure
    Registry -->|Creates| GCP
    Registry -->|Creates| Cloud
    
    OpenShift --> BaseClass
    Unix --> BaseClass
    AWS --> BaseClass
    Azure --> BaseClass
    GCP --> BaseClass
    Cloud -->|Routes to| AWS
    Cloud -->|Routes to| Azure
    Cloud -->|Routes to| GCP
    
    BaseClass --> Connect
    BaseClass --> Execute
    BaseClass --> Scan
    BaseClass --> Disconnect
    
    Scan --> JDKDetector
    JDKDetector --> ComplianceChecker
    ComplianceChecker --> Scan
    BaseClass --> ErrorHandler
    
    ParallelExecutor -->|Uses| BaseClass
    
    Connect --> OpenShiftCluster
    Connect --> UnixHost
    Connect --> AWSInstance
    Connect --> AzureVM
    Connect --> GCPVM
    
    Execute --> OpenShiftCluster
    Execute --> UnixHost
    Execute --> AWSInstance
    Execute --> AzureVM
    Execute --> GCPVM
    
    style BaseClass fill:#f0e1ff
    style JDKDetector fill:#fff4e1
    style ComplianceChecker fill:#fff4e1
    style ParallelExecutor fill:#e1ffe1
```

## Component Interactions

```mermaid
graph LR
    subgraph External[External]
        Client[Client Applications]
        OpenShiftAPI[OpenShift API]
        SSHHosts[SSH Hosts]
        CloudAPIs[Cloud Provider APIs]
    end
    
    subgraph API[API Layer]
        FastAPI[FastAPI]
        Routes[Routes]
        Middleware[Middleware]
    end
    
    subgraph Core[Core Services]
        Auth[Authentication]
        Scanner[Scanners]
        Compliance[Compliance]
        DB[Database]
        Encryption[Encryption]
    end
    
    Client -->|HTTP| FastAPI
    FastAPI --> Middleware
    Middleware --> Auth
    Auth --> DB
    Middleware --> Routes
    Routes --> Scanner
    Routes --> Compliance
    Routes --> DB
    Routes --> Encryption
    DB --> Encryption
    Scanner --> OpenShiftAPI
    Scanner --> SSHHosts
    Scanner --> CloudAPIs
    Scanner --> Compliance
    Compliance --> DB
    FastAPI -->|JSON| Client
    
    style Client fill:#e1f5ff
    style DB fill:#ffe1f5
    style Encryption fill:#fff4e1
```

## Data Encryption Flow

```mermaid
flowchart TD
    InputData[Sensitive Data<br/>Credentials/Tokens] --> EncryptionMgr[Encryption Manager]
    EncryptionMgr -->|Encrypt| EncryptedData[Encrypted String]
    EncryptedData -->|Store| Database[(Database)]
    
    Database -->|Retrieve| EncryptedData
    EncryptedData --> EncryptionMgr
    EncryptionMgr -->|Decrypt| OutputData[Decrypted Data]
    OutputData -->|Use| ScannerOrAPI[Scanner/API]
    
    EncryptionMgr -->|Uses| EncryptionKey[Encryption Key<br/>from ENV/config]
    EncryptionMgr -->|Uses| CryptographyLib[Cryptography Library]
    
    style EncryptionMgr fill:#fff4e1
    style Database fill:#ffe1f5
    style EncryptionKey fill:#f0e1ff
```

## Notes

### Key Components

1. **FastAPI Application**: Entry point for all HTTP requests
2. **Authentication Middleware**: Validates JWT tokens and enforces role-based access
3. **Route Handlers**: Process specific API endpoints (clusters, projects, targets, etc.)
4. **Database Layer**: SQLAlchemy ORM with SQLite database
5. **Encryption Manager**: Handles encryption/decryption of sensitive data
6. **Scanner Factory**: Creates appropriate scanner instances based on deployment type
7. **Scanners**: Connect to target systems and execute JDK version detection
8. **JDK Detector**: Parses `java -version` output to extract version and vendor
9. **Compliance Checker**: Validates JDK versions against database compliance rules

### Data Flow Patterns

- **Request Flow**: Client → FastAPI → Auth → Route Handler → Database/Scanner → Response
- **Authentication**: Token validation happens before route handlers execute
- **Encryption**: Sensitive data encrypted before storage, decrypted when retrieved
- **Scanning**: Factory creates scanner → Scanner connects → Executes commands → Parses output → Checks compliance → Returns results
- **Error Handling**: Centralized error handler logs errors at each layer

### Security Considerations

- All credentials stored encrypted in database
- JWT tokens validated on every authenticated request
- Role-based access control enforced by middleware
- Sensitive fields decrypted only when needed for operations
- Connection credentials encrypted before storage

