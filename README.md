# HireIntel

HireIntel is an intelligent recruitment system specifically designed for hiring software engineers. The system acts as an AI-powered recruiter that streamlines the technical hiring process through automated resume processing, candidate research, and interview management.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [API Keys Setup](#api-keys-setup)
  - [Email Configuration](#email-configuration)
  - [Database Setup](#database-setup)
- [Architecture](#architecture)
  - [Project Structure](#project-structure)
  - [Pipeline System](#pipeline-system)
  - [Module Design](#module-design)
  - [Continuous Processing](#continuous-processing)
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
  - [Admin Endpoints](#admin-endpoints)
  - [Monitoring](#monitoring)
- [Email System](#email-system)
  - [Application Format](#application-format)
  - [Email Templates](#email-templates)
  - [Validation Process](#validation-process)
- [Pipeline Architecture](#pipeline-architecture)
  - [Pipeline Components](#pipeline-components)
  - [Status Management](#status-management)
  - [Data Flow](#data-flow)
- [Real-Time Monitoring](#real-time-monitoring)
  - [SSE Streams](#sse-streams)
  - [Dashboard Integration](#dashboard-integration)
- [Security](#security)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

HireIntel automates and enhances the technical recruitment process through:
- Automated resume parsing and analysis
- Multi-source candidate research (GitHub, LinkedIn, Google)
- AI-powered profile creation
- Automated interview scheduling
- Real-time pipeline monitoring

## Features

### Core Capabilities
- Advanced resume parsing using AI
- GitHub repository analysis
- LinkedIn profile integration
- Google presence analysis
- Intelligent candidate-job matching
- Automated email communications
- Real-time monitoring dashboard
- Interview scheduling system

### Pipeline Features
- Continuous background processing
- Status-based candidate progression
- Multi-stage data enrichment
- Automated profile creation
- Real-time status updates

## System Requirements

- Python 3.8 or higher
- SQLite database
- Poppler PDF library (for PDF processing)
- SMTP server access
- Required API access tokens
- Minimum 4GB RAM recommended
- Storage space for document processing
- 
## Architecture

### Project Structure
```
HireIntel/
├── src/
│   ├── config/
│   │   ├── AppSettings.py
│   │   ├── Config.yaml
│   │   └── DBModelsConfig.py
│   ├── Controllers/
│   │   ├── AdminController.py
│   │   ├── AuthController.py
│   │   └── ScheduleMonitorController.py
│   ├── Modules/
│   │   ├── Auth/
│   │   ├── Candidate/
│   │   ├── Jobs/
│   │   ├── Interviews/
│   │   └── PipeLineData/
│   ├── PipeLines/
│   │   ├── Integration/
│   │   ├── PipeLineManagement/
│   │   └── Profiling/
│   └── Static/
│       ├── EmailTemplates/
│       └── Resume/
├── instance/
└── email_attachments/
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kudzaiprichard/hireIntel.api
cd HireIntel
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Poppler:
- Windows: Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases/)
- Linux: `sudo apt-get install poppler-utils`
- MacOS: `brew install poppler`

## Configuration

### API Keys Setup

1. **GitHub Token**
- Visit [GitHub Developer Settings](https://github.com/settings/tokens)
- Create new token with:
  - `repo` scope (repository access)
  - `user` scope (user data access)
  - `read:org` scope (organization access)
- Add to config:
```yaml
profiler:
  github_token: "your_token"
```

2. **Google AI (Gemini) API**
- Visit [Google AI Studio](https://aistudio.google.com/apikey)
- Sign in and enable the API
- Create new API key
- Add to config:
```yaml
llm:
  genai_token: "your_token"
  poppler_path: "C:\\Program Files\\poppler-24.08.0\\Library\\bin"
```

3. **RapidAPI (LinkedIn)**
- Create account at [RapidAPI](https://rapidapi.com/rockapis-rockapis-default/api/linkedin-data-api/playground/apiendpoint_cac57ac3-a00e-481d-b76d-fca339fae2c0)
- Subscribe to LinkedIn Profile & Company Data API
- Copy API key to config:
```yaml
profiler:
  rapid_api_key: "your_key"
```

4. **Gmail Configuration**
- Enable [2-Step Verification](https://myaccount.google.com/security)
- Generate App Password:
  - Go to Security → App Passwords
  - Select "Mail" and "Other (Custom name)"
  - Name it "HireIntel"
  - Copy 16-character password
- Add to config:
```yaml
email:
  from: "hire"
  username: "your.email@gmail.com"
  password: "your_app_password"
  smtp_host: "smtp.gmail.com"
  smtp_port: 465
  imap_host: "imap.gmail.com"
  imap_port: 993
```

### Complete Configuration Example
```yaml
server:
  ip: "0.0.0.0"
  port: 12345
  debug: true
  ssl: false

database:
  uri: "sqlite:///hire.db"
  track_modifications: false

jwt:
  secret_key: "your_jwt_secret"

assets:
  resume: "./src/Static/Resume/Documents"
  json_resume: "./src/Static/Resume/Json"

profiler:
  github_token: "ghp_xxxxxxxxxxxx"
  google_api_key: "your_google_api_key"
  rapid_api_key: "xxxxxxxxxxxxxxxx"
  batch_size: 5
  intervals:
    linkedin_scraping: 1
    text_extraction: 1
    github_scraping: 1
    google_scraping: 1
    profile_creation: 1
  scoring:
    weights:
      technical: 0.4
      experience: 0.35
      github: 0.25
    min_passing_score: 70.0

watcher:
  watcher_folder: "./src/PipeLines/Integration/FileWatcher/Watcher/watcher_folder"
  failed_folder: "./src/PipeLines/Integration/FileWatcher/Watcher/failed_folder"
  check_interval: 1

email_pipe_line:
  batch_size: 10
  check_interval: 1
  folder: "INBOX"
  allowed_attachments: [".pdf", ".doc", ".docx"]
```

# Integration Systems

## File Watcher Integration

### XML Structure
Candidate applications must be submitted in XML format:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<candidate>
    <email>example@email.com</email>
    <first_name>John</first_name>
    <last_name>Doe</last_name>
    <job_id>93f14b11-da25-4a9a-8bb2-4ac8509ddac0</job_id>
    <phone>+1234567890</phone>
    <current_company>Company Name</current_company>
    <current_position>Current Role</current_position>
    <years_of_experience>5</years_of_experience>
    <documents>
        <document name="resume.pdf" type="resume">resume.pdf</document>
    </documents>
</candidate>
```

Required fields:
- `email`
- `first_name`
- `last_name`
- `job_id` (valid UUID)
- `documents` (with resume)

### File Watcher Flow
1. **Input Detection**:
   - Monitors `watcher_folder` for new XML files
   - Validates XML structure and schema
   - Checks for associated resume document

2. **Document Processing**:
   - Moves resume to document storage
   - Generates unique document identifiers
   - Maintains document associations

3. **Candidate Creation**:
   - Creates new candidate record
   - Sets initial pipeline status to `XML`
   - Triggers pipeline processing

### Configuration
```yaml
watcher:
  watcher_folder: "./src/PipeLines/Integration/FileWatcher/Watcher/watcher_folder"
  failed_folder: "./src/PipeLines/Integration/FileWatcher/Watcher/failed_folder"
  check_interval: 1  # minutes

assets:
  resume: "./src/Static/Resume/Documents"
  json_resume: "./src/Static/Resume/Json"
```

## Pipeline Architecture

### Daemon Thread Architecture
Each pipeline operates as a daemon thread, continuously monitoring for candidates in specific states:

```
Pipeline Threads (All Running Continuously):
├── File Watcher Thread
│   └── Monitors folder for new XML files
│   └── Creates candidates with XML status
│
├── Email Watcher Thread
│   └── Monitors email inbox
│   └── Converts to XML and triggers File Watcher
│
├── Text Extraction Thread
│   └── Watches for status: XML
│   └── Processes resume text
│   └── Updates to: EXTRACT_TEXT
│
├── Google Scraping Thread
│   └── Watches for status: EXTRACT_TEXT
│   └── Gathers web presence
│   └── Updates to: GOOGLE_SCRAPE
│
├── LinkedIn Scraping Thread
│   └── Watches for status: GOOGLE_SCRAPE
│   └── Fetches LinkedIn data
│   └── Updates to: LINKEDIN_SCRAPE
│
├── GitHub Scraping Thread
│   └── Watches for status: LINKEDIN_SCRAPE
│   └── Analyzes GitHub activity
│   └── Updates to: GITHUB_SCRAPE
│
└── Profile Creation Thread
    └── Watches for status: GITHUB_SCRAPE
    └── Creates final profile
    └── Updates to: PROFILE_CREATED
```

### Thread Management
Each pipeline uses an infinite loop for continuous processing:
```python
def _run_pipeline(self):
    with self.app.app_context():
        while not self.stop_flag.is_set():
            try:
                # Get candidates in specific status
                candidates = self.get_input_data()
                
                # Process batch if found
                if candidates:
                    self.process_batch()
                
                # Wait for next interval
                self.stop_flag.wait(self.config.process_interval)
            except Exception as e:
                self.handle_error(e)
```

### Batch Processing
1. **Continuous Polling**:
   - Each thread continuously polls database
   - Looks for candidates in its input status
   - Processes in configurable batch sizes

2. **Status-Based Processing**:
   ```
   XML → EXTRACT_TEXT → GOOGLE_SCRAPE → LINKEDIN_SCRAPE → 
   GITHUB_SCRAPE → PROFILE_CREATION → PROFILE_CREATED
   ```

3. **Thread Safety**:
   - Isolated database transactions
   - Atomic status updates
   - Pipeline-specific state management

### Configuration Control
```yaml
profiler:
  batch_size: 5  # Number of candidates per batch
  intervals:     # Polling intervals in minutes
    linkedin_scraping: 1
    text_extraction: 1
    github_scraping: 1
    google_scraping: 1
    profile_creation: 1
```

### Process Flow
```python
# Each pipeline continuously:
while not stop_flag:
    # Find candidates in input status
    candidates = find_candidates_in_status(INPUT_STATUS)
    
    if candidates:
        try:
            # Process candidates
            process_candidates(candidates)
            # Update to next status
            update_status(candidates, OUTPUT_STATUS)
        except:
            # Mark as failed
            update_status(candidates, FAILED_STATUS)
    
    # Wait for next interval
    wait(process_interval)
```

### Status Progression Examples
```
Candidate A: XML → EXTRACT_TEXT → GOOGLE_SCRAPE → ...
Candidate B: XML → EXTRACT_TEXT → GOOGLE_SCRAPE_FAILED
Candidate C: XML → EXTRACT_TEXT_FAILED
```

### Error Handling
- Failed states don't block pipeline
- Detailed error logging
- Automatic retry mechanism
- Status-based error tracking
- Error notification system

#### Status Management
Pipeline states for each candidate:
```python
class CandidatePipelineStatus(Enum):
    XML = "xml"
    EXTRACT_TEXT = "extract_text"
    GOOGLE_SCRAPE = "google_scrape"
    LINKEDIN_SCRAPE = "linkedin_scrape"
    GITHUB_SCRAPE = "github_scrape"
    PROFILE_CREATION = "profile_creation"
    PROFILE_CREATED = "profile_created"
    
    # Failed states
    XML_FAILED = "xml_failed"
    EXTRACT_TEXT_FAILED = "extract_text_failed"
    GOOGLE_SCRAPE_FAILED = "google_scrape_failed"
    LINKEDIN_SCRAPE_FAILED = "linkedin_scrape_failed"
    GITHUB_SCRAPE_FAILED = "github_scrape_failed"
    PROFILE_CREATION_FAILED = "profile_creation_failed"
```

## Email System

### Application Format
Email applications must follow this format:
```
Applying for [position name] position. Please find below attached resume and documents for your reference
First Name: [Required]
Middle Name: [Optional]
Last Name: [Required]
Job Id: [Required UUID]
```

### Email Templates

1. **Application Received**:
```html
Subject: Application Received - [Position]
Dear [First Name],
Your application for [Position] has been received...
```

2. **Invalid Job ID**:
```html
Subject: Application Error - Invalid Job ID
Dear [First Name],
The Job ID [Job ID] is not valid...
```

3. **Missing Fields**:
```html
Subject: Application Error - Missing Information
Dear Applicant,
The following required fields are missing:
[Missing Fields List]
```

## API Documentation

### Auth Controller (`/api/v1/auth`)
```
Authentication Endpoints:
├── POST /register
├── POST /login
├── POST /logout
├── POST /refresh/tokens
└── GET  /user/fetch
```

### Admin Controller (`/api/v1/admin`)
```
Protected Endpoints:
├── Jobs Management
│   ├── GET  /jobs
│   ├── POST /jobs
│   └── PUT  /jobs/<id>
└── Interview Management
    ├── POST /interviews/schedule
    └── GET  /interviews/schedules
```

### Monitor Controller
```
Real-time Endpoints:
├── GET /api/monitor/status
└── GET /api/monitor/status/stream
```

## Real-Time Monitoring

### SSE Streams
1. **Pipeline Monitor**:
```javascript
{
    "timestamp": "2025-02-12T10:00:00Z",
    "pipelines": {
        "text_extraction": {
            "status": "PROCESSING",
            "last_updated": "2025-02-12T09:59:55Z"
        }
    }
}
```

2. **Candidate Monitor**:
```javascript
{
    "data": {
        "candidates": [...],
        "pagination": {
            "total": 100,
            "page": 1,
            "per_page": 10
        }
    }
}
```

## Security
- JWT-based authentication
- Role-based access control
- API rate limiting
- Secure password storage
- Email validation
- Input sanitization

## Deployment
1. Set up environment:
   - Configure API keys
   - Set up email server
   - Configure database
2. Install dependencies
3. Initialize database
4. Start application:
```bash
python app.py
```

## Troubleshooting

### Common Issues
1. Pipeline Failures:
   - Check API quotas
   - Verify credentials
   - Check network connectivity

2. Email Issues:
   - Verify SMTP settings
   - Check email templates
   - Validate email format

3. Database Issues:
   - Check connections
   - Verify permissions
   - Monitor disk space

## Contributing
1. Fork repository
2. Create feature branch
3. Submit pull request

## License
MIT License
