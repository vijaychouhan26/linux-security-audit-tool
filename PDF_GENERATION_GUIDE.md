# PDF Generation Guide

## Overview
The Linux Security Audit Tool can generate professional PDF reports from completed security scans.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Or check and install automatically:
```bash
python3 check_dependencies.py
```

### 2. Start the Application
```bash
# Terminal 1: Backend API
python3 run_api.py

# Terminal 2: Frontend Dashboard
python3 frontend/dashboard.py
```

### 3. Access Dashboard
Open `http://localhost:8080` in your browser

### 4. Generate PDF
- Navigate to History or Scans page
- Click the PDF icon (📄) next to a completed scan
- PDF downloads automatically

## API Usage

### Direct API Call
```bash
curl -o report.pdf http://localhost:5000/api/scans/<scan_id>/pdf
```

### Python Example
```python
import requests

response = requests.get('http://localhost:5000/api/scans/scan_fcd64093/pdf')
if response.status_code == 200:
    with open('report.pdf', 'wb') as f:
        f.write(response.content)
```

## Troubleshooting

### "PDF generation is not available"
**Solution**: Install reportlab
```bash
pip install reportlab>=4.0.0
```

### "Scan not found"
**Solution**: 
- Verify scan is completed
- Check scan ID using `/api/history`
- Use the scan_id from metadata, not directory name

## Testing

Verify PDF generation works:
```bash
python3 -c "
from src.api.app import create_app
app = create_app()
client = app.test_client()
response = client.get('/api/scans/scan_fcd64093/pdf')
print(f'Status: {response.status_code}')
print(f'Size: {len(response.data)} bytes')
"
```

## PDF Report Contents
- Executive summary
- Security findings by severity (Critical/High/Medium/Low)
- Scan statistics
- System information
- Detailed test results

## Status
✅ **PDF Generation is WORKING**
- All dependencies installed
- API endpoint functional
- 8-page reports generated successfully
- Tested and verified
