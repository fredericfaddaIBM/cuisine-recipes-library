# Security Review and Mitigation Plan
**Date**: 2026-05-02  
**Project**: Cuisine Recipes Library  
**Reviewer**: Security Analysis

## Executive Summary

This document outlines security vulnerabilities identified in the Recipe Library application and provides a comprehensive mitigation plan. The application has **3 Critical**, **5 High**, **4 Medium**, and **3 Low** severity vulnerabilities that require immediate attention.

---

## Critical Severity Vulnerabilities

### 1. Path Traversal in File Operations
**Severity**: 🔴 CRITICAL  
**CWE**: CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)

**Affected Files**:
- [`app.py:200`](app.py:200) - `view_recipe(recipe_id)`
- [`app.py:224`](app.py:224) - `edit_recipe(recipe_id)`
- [`app.py:332`](app.py:332) - `serve_image(filename)`

**Vulnerability**:
```python
# Current vulnerable code
recipe_file = Path(app.config['RECIPES_FOLDER']) / f"{recipe_id}.md"
return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
```

User-supplied `recipe_id` and `filename` are used directly without validation, allowing path traversal attacks like `../../../etc/passwd`.

**Attack Scenario**:
```bash
curl http://localhost:5000/recipe/../../../etc/passwd
curl http://localhost:5000/images/../../../etc/passwd
```

**Mitigation**:
```python
import os
from werkzeug.security import safe_join

def validate_recipe_id(recipe_id: str) -> bool:
    """Validate recipe ID contains only safe characters."""
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', recipe_id))

@app.route('/recipe/<recipe_id>')
def view_recipe(recipe_id):
    # Validate input
    if not validate_recipe_id(recipe_id):
        return "Invalid recipe ID", 400
    
    # Use safe_join to prevent path traversal
    recipe_file = safe_join(app.config['RECIPES_FOLDER'], f"{recipe_id}.md")
    if recipe_file is None or not os.path.exists(recipe_file):
        return "Recipe not found", 404
```

---

### 2. Arbitrary File Upload Without Content Validation
**Severity**: 🔴 CRITICAL  
**CWE**: CWE-434 (Unrestricted Upload of File with Dangerous Type)

**Affected Files**:
- [`app.py:67-113`](app.py:67) - `upload()` function

**Vulnerability**:
```python
# Only checks extension, not content
if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
    file.save(filepath)
```

Attackers can upload malicious files (PHP shells, executables) with image extensions.

**Attack Scenario**:
1. Upload `malware.php` renamed as `malware.jpg`
2. If server misconfigured, PHP code executes
3. Upload SVG with embedded JavaScript for XSS

**Mitigation**:
```python
from PIL import Image
import magic  # python-magic library

def validate_image_content(filepath: str) -> bool:
    """Validate file is actually an image."""
    try:
        # Check MIME type
        mime = magic.from_file(filepath, mime=True)
        if not mime.startswith('image/'):
            return False
        
        # Verify image can be opened
        img = Image.open(filepath)
        img.verify()
        
        # Re-save to strip metadata and ensure clean image
        img = Image.open(filepath)
        img.save(filepath)
        return True
    except Exception:
        return False

@app.route('/upload', methods=['POST'])
def upload():
    # ... existing code ...
    file.save(filepath)
    
    # Validate content
    if not validate_image_content(filepath):
        os.remove(filepath)
        return jsonify({'error': 'Invalid image file'}), 400
```

---

### 3. Debug Mode Enabled in Production
**Severity**: 🔴 CRITICAL  
**CWE**: CWE-489 (Active Debug Code)

**Affected Files**:
- [`app.py:383`](app.py:383)

**Vulnerability**:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

Debug mode exposes:
- Stack traces with source code
- Interactive debugger (Werkzeug debugger PIN can be bypassed)
- Internal application structure

**Mitigation**:
```python
import os

if __name__ == '__main__':
    # Ensure directories exist
    for directory in ['images', 'recipes', 'logs', 'json-extract', 'embeddings']:
        Path(directory).mkdir(exist_ok=True)
    
    # Never use debug=True in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
```

**Additional**: Use environment variables and never commit debug=True.

---

## High Severity Vulnerabilities

### 4. No Authentication or Authorization
**Severity**: 🟠 HIGH  
**CWE**: CWE-306 (Missing Authentication for Critical Function)

**Affected Files**:
- All routes in [`app.py`](app.py)

**Vulnerability**:
All endpoints are publicly accessible without authentication:
- Upload images
- Edit/delete recipes
- Access all data

**Mitigation**:
```python
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

auth = HTTPBasicAuth()

# Store in environment variables or secure config
users = {
    os.environ.get('ADMIN_USER', 'admin'): generate_password_hash(
        os.environ.get('ADMIN_PASSWORD', secrets.token_urlsafe(32))
    )
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# Protect sensitive routes
@app.route('/upload', methods=['GET', 'POST'])
@auth.login_required
def upload():
    # ... existing code ...

@app.route('/recipe/<recipe_id>/edit', methods=['GET', 'POST'])
@auth.login_required
def edit_recipe(recipe_id):
    # ... existing code ...
```

---

### 5. Missing CSRF Protection
**Severity**: 🟠 HIGH  
**CWE**: CWE-352 (Cross-Site Request Forgery)

**Affected Files**:
- [`app.py:67`](app.py:67) - Upload endpoint
- [`app.py:223`](app.py:223) - Edit endpoint

**Vulnerability**:
No CSRF tokens on state-changing operations.

**Attack Scenario**:
```html
<!-- Attacker's malicious site -->
<form action="http://victim-site:5000/upload" method="POST" enctype="multipart/form-data">
    <input type="file" name="file" value="malware.jpg">
    <input type="submit">
</form>
<script>document.forms[0].submit();</script>
```

**Mitigation**:
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Exempt API endpoints if needed
@app.route('/api/search', methods=['POST'])
@csrf.exempt
def api_search():
    # ... existing code ...
```

---

### 6. SQL Injection Risk in Future Database Integration
**Severity**: 🟠 HIGH  
**CWE**: CWE-89 (SQL Injection)

**Affected Files**:
- Currently file-based, but risk for future DB integration

**Vulnerability**:
If database is added without parameterized queries, vulnerable to SQL injection.

**Mitigation** (Preventive):
```python
# When adding database, always use parameterized queries
from sqlalchemy import create_engine, text

# GOOD - Parameterized
engine.execute(text("SELECT * FROM recipes WHERE id = :id"), {"id": recipe_id})

# BAD - String concatenation
engine.execute(f"SELECT * FROM recipes WHERE id = '{recipe_id}'")
```

---

### 7. Insecure Direct Object References (IDOR)
**Severity**: 🟠 HIGH  
**CWE**: CWE-639 (Authorization Bypass Through User-Controlled Key)

**Affected Files**:
- [`app.py:200`](app.py:200) - View recipe
- [`app.py:224`](app.py:224) - Edit recipe

**Vulnerability**:
Users can access/modify any recipe by guessing IDs.

**Mitigation**:
```python
# Add ownership checks when authentication is implemented
def check_recipe_ownership(recipe_id, user):
    """Verify user owns or has permission to access recipe."""
    recipe = load_recipe(recipe_id)
    if recipe and recipe.get('owner') != user:
        abort(403)  # Forbidden
```

---

### 8. Missing Rate Limiting
**Severity**: 🟠 HIGH  
**CWE**: CWE-770 (Allocation of Resources Without Limits)

**Affected Files**:
- [`app.py:67`](app.py:67) - Upload endpoint
- [`app.py:116`](app.py:116) - Search endpoint

**Vulnerability**:
No rate limiting allows:
- Brute force attacks
- Resource exhaustion (DoS)
- Abuse of expensive operations (AI processing)

**Mitigation**:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@app.route('/upload', methods=['POST'])
@limiter.limit("10 per hour")  # Expensive AI operation
def upload():
    # ... existing code ...

@app.route('/search', methods=['POST'])
@limiter.limit("100 per hour")
def search():
    # ... existing code ...
```

---

## Medium Severity Vulnerabilities

### 9. Sensitive Information in Logs
**Severity**: 🟡 MEDIUM  
**CWE**: CWE-532 (Insertion of Sensitive Information into Log File)

**Affected Files**:
- [`scripts/process_images.py:30-96`](scripts/process_images.py:30)
- [`scripts/search_recipes.py:21-87`](scripts/search_recipes.py:21)

**Vulnerability**:
Logs may contain sensitive data (file paths, user inputs, errors with data).

**Mitigation**:
```python
import re

def sanitize_log_message(message: str) -> str:
    """Remove sensitive information from log messages."""
    # Remove file paths
    message = re.sub(r'/Users/[^/]+/', '/Users/***/', message)
    # Remove potential tokens/keys
    message = re.sub(r'[A-Za-z0-9]{32,}', '***', message)
    return message

class DualLogger:
    def info(self, message: str):
        self.logger.info(sanitize_log_message(message))
```

---

### 10. Hardcoded Secrets Risk
**Severity**: 🟡 MEDIUM  
**CWE**: CWE-798 (Use of Hard-coded Credentials)

**Affected Files**:
- [`app.py:22`](app.py:22) - No SECRET_KEY set
- [`config.yaml`](config.yaml) - Configuration in version control

**Vulnerability**:
No secret key for session management, config file in git.

**Mitigation**:
```python
import secrets
import os

# Generate secure secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Warn if using default
if 'SECRET_KEY' not in os.environ:
    print("⚠️  WARNING: Using generated SECRET_KEY. Set SECRET_KEY environment variable.")
```

Add to `.gitignore`:
```
config.yaml
.env
*.key
```

Create `config.yaml.example` instead.

---

### 11. Missing Input Validation
**Severity**: 🟡 MEDIUM  
**CWE**: CWE-20 (Improper Input Validation)

**Affected Files**:
- [`app.py:116-197`](app.py:116) - Search parameters
- [`app.py:223-275`](app.py:223) - Recipe edit

**Vulnerability**:
User inputs not validated for type, length, format.

**Mitigation**:
```python
from marshmallow import Schema, fields, validate, ValidationError

class SearchSchema(Schema):
    semantic_query = fields.Str(validate=validate.Length(max=500))
    ingredients = fields.List(fields.Str(validate=validate.Length(max=100)))
    max_time = fields.Int(validate=validate.Range(min=1, max=1440))
    page = fields.Int(validate=validate.Range(min=1, max=1000))
    per_page = fields.Int(validate=validate.OneOf([4, 10, 20, 50, 100]))

@app.route('/search', methods=['POST'])
def search():
    schema = SearchSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': err.messages}), 400
    # ... continue with validated data ...
```

---

### 12. Insufficient Error Handling
**Severity**: 🟡 MEDIUM  
**CWE**: CWE-209 (Generation of Error Message Containing Sensitive Information)

**Affected Files**:
- [`app.py:105-109`](app.py:105)
- [`app.py:185-189`](app.py:185)

**Vulnerability**:
```python
except Exception as e:
    return jsonify({'error': str(e)}), 500
```

Exposes internal error details to users.

**Mitigation**:
```python
import logging

logger = logging.getLogger(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # ... processing ...
    except Exception as e:
        # Log detailed error internally
        logger.error(f"Upload failed: {e}", exc_info=True)
        # Return generic error to user
        return jsonify({
            'success': False,
            'error': 'An error occurred processing your request'
        }), 500
```

---

## Low Severity Vulnerabilities

### 13. Missing Security Headers
**Severity**: 🟢 LOW  
**CWE**: CWE-693 (Protection Mechanism Failure)

**Affected Files**:
- [`app.py`](app.py) - No security headers

**Vulnerability**:
Missing headers like CSP, X-Frame-Options, etc.

**Mitigation**:
```python
from flask_talisman import Talisman

Talisman(app, 
    force_https=False,  # Set True in production with HTTPS
    content_security_policy={
        'default-src': "'self'",
        'img-src': "'self' data:",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'"
    }
)

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

---

### 14. Predictable File Names
**Severity**: 🟢 LOW  
**CWE**: CWE-330 (Use of Insufficiently Random Values)

**Affected Files**:
- [`app.py:82-84`](app.py:82)

**Vulnerability**:
```python
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"{name}_{timestamp}{ext}"
```

Predictable filenames allow enumeration.

**Mitigation**:
```python
import uuid

filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
```

---

### 15. Docker Container Running as Root
**Severity**: 🟢 LOW  
**CWE**: CWE-250 (Execution with Unnecessary Privileges)

**Affected Files**:
- [`Dockerfile`](Dockerfile)

**Vulnerability**:
Container runs as root user by default.

**Mitigation**:
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt flask gunicorn

# Copy application
COPY --chown=appuser:appuser . .

# Create directories with correct permissions
RUN mkdir -p images recipes logs json-extract embeddings && \
    chown -R appuser:appuser images recipes logs json-extract embeddings

# Switch to non-root user
USER appuser

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "app:app"]
```

---

## Implementation Priority

### Phase 1: Critical Fixes (Immediate - Week 1)
1. ✅ Fix path traversal vulnerabilities
2. ✅ Add file content validation
3. ✅ Disable debug mode in production
4. ✅ Add basic authentication

### Phase 2: High Priority (Week 2-3)
5. ✅ Implement CSRF protection
6. ✅ Add rate limiting
7. ✅ Fix IDOR vulnerabilities
8. ✅ Add input validation

### Phase 3: Medium Priority (Week 4)
9. ✅ Sanitize logs
10. ✅ Implement proper error handling
11. ✅ Add security headers
12. ✅ Move secrets to environment variables

### Phase 4: Low Priority (Week 5)
13. ✅ Use random filenames
14. ✅ Run container as non-root
15. ✅ Add security documentation

---

## Security Best Practices Going Forward

### 1. Secure Development Lifecycle
- [ ] Code review all changes for security issues
- [ ] Run security scanners (Bandit, Safety)
- [ ] Keep dependencies updated
- [ ] Follow OWASP Top 10 guidelines

### 2. Configuration Management
```bash
# Use environment variables for secrets
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
export ADMIN_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
export FLASK_ENV=production
```

### 3. Monitoring and Logging
- [ ] Implement security event logging
- [ ] Monitor for suspicious activity
- [ ] Set up alerts for failed authentication
- [ ] Regular log review

### 4. Testing
```python
# Add security tests
def test_path_traversal():
    response = client.get('/recipe/../../../etc/passwd')
    assert response.status_code == 400

def test_file_upload_validation():
    response = client.post('/upload', data={'file': malicious_file})
    assert response.status_code == 400
```

### 5. Dependencies
```bash
# Regular security audits
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade package-name
```

---

## Required Dependencies for Security Fixes

Add to [`requirements.txt`](requirements.txt):
```
flask-httpauth>=4.8.0
flask-limiter>=3.5.0
flask-talisman>=1.1.0
flask-wtf>=1.2.0
python-magic>=0.4.27
marshmallow>=3.20.0
```

---

## Testing the Fixes

### Security Test Suite
```python
# tests/test_security.py
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_path_traversal_blocked(client):
    """Test path traversal is blocked."""
    response = client.get('/recipe/../../../etc/passwd')
    assert response.status_code in [400, 404]

def test_authentication_required(client):
    """Test authentication is required for sensitive endpoints."""
    response = client.post('/upload')
    assert response.status_code == 401

def test_rate_limiting(client):
    """Test rate limiting works."""
    for _ in range(100):
        client.post('/search')
    response = client.post('/search')
    assert response.status_code == 429

def test_csrf_protection(client):
    """Test CSRF protection is active."""
    response = client.post('/upload', data={})
    assert response.status_code in [400, 403]
```

---

## Compliance Considerations

### GDPR (if applicable)
- [ ] Add privacy policy
- [ ] Implement data deletion
- [ ] Add consent mechanisms
- [ ] Log data access

### OWASP ASVS Level 1
- [ ] Authentication (V2)
- [ ] Session Management (V3)
- [ ] Access Control (V4)
- [ ] Input Validation (V5)
- [ ] Cryptography (V6)
- [ ] Error Handling (V7)
- [ ] Data Protection (V8)

---

## Conclusion

This security review identified **15 vulnerabilities** requiring remediation. The most critical issues involve path traversal, arbitrary file upload, and debug mode in production. Following the phased implementation plan will significantly improve the application's security posture.

**Estimated Effort**: 3-5 weeks for complete implementation  
**Risk Reduction**: ~85% of identified vulnerabilities  
**Next Review**: After Phase 2 completion

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-02  
**Next Review Date**: 2026-06-02