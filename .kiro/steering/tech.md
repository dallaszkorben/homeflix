# HomeFlix Technical Specification

## Technology Stack

### Frontend Technologies
- **Core Framework**: Vanilla JavaScript ES6+ with jQuery 3.6.0
- **UI Components**: jQuery UI for dialogs and interactions
- **Media Display**: Fancybox for lightbox functionality
- **Styling**: Custom CSS with responsive design patterns
- **Data Parsing**: js-yaml for YAML configuration parsing
- **Code Highlighting**: Highlight.js for syntax highlighting
- **Device Detection**: Custom JavaScript for TV/mobile/desktop detection

### Backend Technologies
- **Web Framework**: Flask 2.1.2 with Flask-Classful for REST API organization
- **Database**: SQLite 3.36+ with custom query builder
- **Configuration**: PyYAML for YAML file processing
- **Authentication**: Flask sessions with SHA256 hashing
- **CORS**: Flask-CORS for cross-origin requests
- **Logging**: Python logging with rotating file handlers
- **Virtual Environment**: Python 3.10 with isolated dependencies

### Infrastructure Technologies
- **Web Server**: Apache 2.4 with mod_wsgi
- **Operating System**: Raspberry Pi OS (Debian-based)
- **Process Management**: Systemd services
- **File System**: ext4 with USB/NAS mounting
- **Network**: Local network only (no external dependencies)

## Architecture Patterns

### Frontend Architecture

#### Single Page Application (SPA)
- **Entry Point**: `index.html` loads all JavaScript modules
- **Dynamic Loading**: Content generated via REST API calls
- **State Management**: Browser cookies and localStorage for persistence
- **Routing**: Hash-based navigation without page reloads
- **Component System**: Object-oriented JavaScript classes

#### UI Component Pattern
```javascript
// Base Generator Pattern
class Generator {
    constructor(language_code) {
        this.language_code = language_code;
    }
    produceContainers() {
        // Abstract method - implemented by subclasses
    }
}

// Specialized Generators
class MovieGenerator extends RestGenerator {
    generateThumbnail(data_dict, play_list) {
        // Movie-specific thumbnail generation
    }
}
```

#### Container Management Pattern
```javascript
// Scroll Section Management
class ObjScrollSection {
    constructor({ oContainerGenerator, historyLevels, objThumbnailController }) {
        this.oContainerGenerator = oContainerGenerator;
        this.thumbnailContainerList = [];
        this.focusedThumbnailList = [];
        // Initialize containers and description
    }
}
```

### Backend Architecture

#### Flask Application Pattern
```python
# Main Application Class
class WSHomeflix(Flask):
    def __init__(self, import_name):
        super().__init__(import_name)
        # Configuration loading
        # Database initialization
        # View registration
        # CORS setup
```

#### View Organization Pattern
```python
# RESTful View Classes using Flask-Classful
class CollectView(FlaskView):
    route_base = '/collect'
    
    @route('/highest_level', methods=['GET'])
    def get_highest_level(self):
        # Implementation
        
    @route('/next_level', methods=['POST'])
    def get_next_level(self):
        # Implementation
```

#### Database Access Pattern
```python
# Singleton Database Class
class SqlDatabase:
    __instance = None
    
    def __new__(cls, web_gadget):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
```

### Data Architecture

#### YAML-Based Configuration
```yaml
# Hierarchical Configuration Structure
containers:
  - name: "categories"
    type: "hardcoded"
    title:
      en: "Categories"
      hu: "Kategóriák"
    items:
      - category: "movie"
        image: "images/categories/movie.jpg"
        
  - name: "movie_genres"
    type: "queried"
    query_type: "genre"
    category: "movie"
```

#### Card-Based Media Metadata
```yaml
# Media Item Structure
category: movie
level: movie
sequence: -1
title:
  onthumbnail: true
  showsequence: 
  orig: en
  titles:
    en: "The Matrix"
    hu: "Mátrix"
storylines:
  en: "A computer hacker learns..."
performer: "The Wachowskis"
date: 1999
decade: 1990
sounds: [en]
genres: [action, sci_fi]
origins: [us]
medium: "video=The.Matrix-1999.mkv"
```

## Database Design

### Schema Architecture

#### Core Entity Tables
```sql
-- Primary content table
CREATE TABLE Card (
    id INTEGER PRIMARY KEY,
    category TEXT,
    level TEXT,
    sequence INTEGER,
    source_path TEXT,
    date INTEGER,
    decade INTEGER,
    length TEXT,
    rate INTEGER,
    skip_continuous_play BOOLEAN
);

-- Lookup tables for normalization
CREATE TABLE Category (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
CREATE TABLE Genre (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
CREATE TABLE Language (id INTEGER PRIMARY KEY, code TEXT UNIQUE);
CREATE TABLE Country (id INTEGER PRIMARY KEY, code TEXT UNIQUE);
```

#### Relationship Tables (Many-to-Many)
```sql
-- Content relationships
CREATE TABLE Card_Genre (id_card INTEGER, id_genre INTEGER);
CREATE TABLE Card_Actor (id_card INTEGER, id_person INTEGER);
CREATE TABLE Card_Director (id_card INTEGER, id_person INTEGER);
CREATE TABLE Card_Sound (id_card INTEGER, id_language INTEGER);
CREATE TABLE Card_Sub (id_card INTEGER, id_language INTEGER);
```

#### User Data Tables
```sql
-- User management
CREATE TABLE User (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    language_code TEXT,
    preferences TEXT -- JSON blob
);

-- User activity tracking
CREATE TABLE History (
    id INTEGER PRIMARY KEY,
    id_user INTEGER,
    id_card INTEGER,
    position INTEGER,
    timestamp DATETIME
);
```

### Query Optimization Patterns

#### Dynamic Query Building
```python
def build_filter_query(self, filters):
    """Build SQL query with dynamic WHERE conditions"""
    base_query = "SELECT * FROM Card"
    conditions = []
    params = []
    
    if 'category' in filters:
        conditions.append("category = ?")
        params.append(filters['category'])
        
    if 'genre' in filters:
        conditions.append("id IN (SELECT id_card FROM Card_Genre WHERE id_genre = ?)")
        params.append(self.get_genre_id(filters['genre']))
    
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    return base_query, params
```

#### Hierarchical Data Queries
```python
def get_hierarchy_path(self, card_id):
    """Get full hierarchy path for a card"""
    path = []
    current_id = card_id
    
    while current_id:
        card = self.get_card_by_id(current_id)
        path.insert(0, card)
        current_id = card.get('id_higher_level')
    
    return path
```

## API Design

### RESTful Endpoint Design

#### Resource-Based URLs
```
/collect/highest_level          # GET - Top-level categories
/collect/next_level            # POST - Child items with filters
/collect/lowest_level          # POST - Leaf items (playable media)
/personal/history/{user_id}    # GET - User viewing history
/personal/rating              # POST - Submit content rating
/stream/media/{card_id}       # GET - Stream media file
```

#### Request/Response Standards
```python
# Standard Success Response
{
    "result": True,
    "data": [
        {
            "id": 123,
            "title": "Movie Title",
            "category": "movie",
            "thumbnail_url": "/media/path/thumbnail.jpg"
        }
    ],
    "message": "Success",
    "error": None
}

# Standard Error Response
{
    "result": False,
    "data": None,
    "message": "Invalid category specified",
    "error": "INVALID_CATEGORY"
}
```

### Authentication & Session Management

#### Session-Based Authentication
```python
@route('/login', methods=['POST'])
def login(self):
    username = request.form.get('username')
    password = request.form.get('password')
    
    if self.validate_credentials(username, password):
        session['user_id'] = user.id
        session['language'] = user.language_code
        session.permanent = True
        return self.success_response(user_data)
    else:
        return self.error_response("Invalid credentials")
```

#### Request Validation Pattern
```python
def validate_request(self, required_fields):
    """Validate required fields in request"""
    missing_fields = []
    for field in required_fields:
        if field not in request.form and field not in request.json:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing fields: {missing_fields}")
```

## Performance Optimization

### Frontend Optimization

#### Lazy Loading Strategy
```javascript
// Progressive content loading
class ThumbnailLoader {
    constructor() {
        this.loadQueue = [];
        this.loadBatchSize = 20;
    }
    
    loadNextBatch() {
        const batch = this.loadQueue.splice(0, this.loadBatchSize);
        batch.forEach(thumbnail => this.loadThumbnail(thumbnail));
    }
}
```

#### Caching Strategy
```javascript
// Browser-based caching
function getCachedData(key, maxAge = 300000) { // 5 minutes
    const cached = localStorage.getItem(key);
    if (cached) {
        const data = JSON.parse(cached);
        if (Date.now() - data.timestamp < maxAge) {
            return data.value;
        }
    }
    return null;
}
```

### Backend Optimization

#### Database Connection Pooling
```python
class SqlDatabase:
    def __init__(self):
        self.connection_pool = []
        self.max_connections = 10
        
    def get_connection(self):
        if self.connection_pool:
            return self.connection_pool.pop()
        return sqlite3.connect(self.db_path)
    
    def return_connection(self, conn):
        if len(self.connection_pool) < self.max_connections:
            self.connection_pool.append(conn)
        else:
            conn.close()
```

#### Query Result Caching
```python
from functools import lru_cache

class SqlDatabase:
    @lru_cache(maxsize=128)
    def get_genres_by_category(self, category):
        """Cache frequently accessed genre lists"""
        return self.execute_query(
            "SELECT DISTINCT g.name FROM Genre g "
            "JOIN Card_Genre cg ON g.id = cg.id_genre "
            "JOIN Card c ON cg.id_card = c.id "
            "WHERE c.category = ?", [category]
        )
```

## Security Implementation

### Input Validation & Sanitization

#### SQL Injection Prevention
```python
def execute_query(self, query, params=None):
    """Always use parameterized queries"""
    try:
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise
```

#### File Path Validation
```python
def validate_media_path(self, path):
    """Ensure media paths are within allowed directories"""
    abs_path = os.path.abspath(path)
    allowed_paths = [self.mediaAbsolutePath]
    
    for allowed in allowed_paths:
        if abs_path.startswith(os.path.abspath(allowed)):
            return True
    
    raise SecurityError("Path not allowed")
```

### Session Security

#### Secure Session Configuration
```python
class WSHomeflix(Flask):
    def __init__(self, import_name):
        super().__init__(import_name)
        
        # Secure session configuration
        self.secret_key = hashlib.sha256("secret_salt".encode()).hexdigest()
        self.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
        self.config['SESSION_COOKIE_SECURE'] = False  # HTTP only (local network)
        self.config['SESSION_COOKIE_HTTPONLY'] = True
```

## Deployment Architecture

### Apache Configuration

#### Virtual Host Setup
```apache
<VirtualHost *:80>
    ServerName localhost
    ServerAlias homeflix.com
    
    # WSGI Configuration
    WSGIDaemonProcess homeflix user=pi group=pi threads=5 python-home=/var/www/homeflix/python/env
    WSGIProcessGroup homeflix
    WSGIScriptAlias / /var/www/homeflix/python/homeflix.wsgi
    
    # Static file serving
    Alias /homeflix /var/www/homeflix/
    Alias /media /var/www/homeflix/MEDIA/
    
    # Security headers
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
</VirtualHost>
```

#### WSGI Entry Point
```python
#!/usr/bin/python3
import sys
import os

# Add project directory to Python path
sys.path.insert(0, "/var/www/homeflix/python/")

# Activate virtual environment
activate_this = '/var/www/homeflix/python/env/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import Flask application
from homeflix.restserver.ws_homeflix import app as application

if __name__ == "__main__":
    application.run()
```

### System Service Configuration

#### Systemd Service
```ini
[Unit]
Description=HomeFlix Media Server
After=network.target

[Service]
Type=forking
User=pi
Group=pi
WorkingDirectory=/var/www/homeflix
ExecStart=/usr/sbin/apache2ctl start
ExecReload=/usr/sbin/apache2ctl graceful
ExecStop=/usr/sbin/apache2ctl stop
Restart=always

[Install]
WantedBy=multi-user.target
```

### Environment Setup

#### Python Virtual Environment
```bash
# Virtual environment creation
cd /var/www/homeflix/python
python3 -m venv env
source env/bin/activate

# Dependency installation
pip install Flask==2.1.2
pip install Flask-Classful==0.14.2
pip install Flask-CORS==3.0.10
pip install PyYAML==6.0
pip install Werkzeug==2.1.2
```

#### File System Permissions
```bash
# Set proper ownership
sudo chown -R pi:pi /var/www/homeflix
sudo chown -R pi:pi /home/pi/.homeflix

# Set directory permissions
sudo chmod -R 755 /var/www/homeflix
sudo chmod -R 644 /var/www/homeflix/python/homeflix/*.py

# Set media directory permissions
sudo chmod -R 755 /var/www/homeflix/MEDIA
```

## Development Workflow

### Code Organization Standards

#### Python Code Style
```python
# Follow PEP 8 standards
class SqlDatabase:
    """Database operations class following singleton pattern"""
    
    def __init__(self, web_gadget):
        """Initialize database connection and configuration"""
        self.web_gadget = web_gadget
        self.db_path = self._get_db_path()
    
    def _get_db_path(self):
        """Private method for database path resolution"""
        config = getConfig()
        return os.path.join(config["path"], config['card-db-name'])
```

#### JavaScript Code Style
```javascript
// Use consistent naming and structure
class ObjThumbnailContainer {
    constructor(containerIndex, containerTitle, objScrollSection) {
        this.containerIndex = containerIndex;
        this.containerTitle = containerTitle;
        this.objScrollSection = objScrollSection;
        this.thumbnailList = [];
    }
    
    addThumbnail(thumbnailData) {
        const thumbnail = new ObjThumbnail(thumbnailData, this);
        this.thumbnailList.push(thumbnail);
        return thumbnail;
    }
}
```

### Testing Strategy

#### Unit Testing Pattern
```python
import unittest
from homeflix.card.database import SqlDatabase

class TestSqlDatabase(unittest.TestCase):
    def setUp(self):
        self.db = SqlDatabase(mock_web_gadget)
    
    def test_get_card_by_id(self):
        card = self.db.get_card_by_id(1)
        self.assertIsNotNone(card)
        self.assertEqual(card['id'], 1)
    
    def test_invalid_card_id(self):
        card = self.db.get_card_by_id(-1)
        self.assertIsNone(card)
```

#### Integration Testing
```python
def test_api_endpoint(self):
    """Test complete API workflow"""
    # Test authentication
    response = self.client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'test_pass'
    })
    self.assertEqual(response.status_code, 200)
    
    # Test content retrieval
    response = self.client.get('/collect/highest_level')
    self.assertEqual(response.status_code, 200)
    data = response.get_json()
    self.assertTrue(data['result'])
```

### Monitoring & Logging

#### Application Logging
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure rotating log files
logging.basicConfig(
    handlers=[RotatingFileHandler(
        '/home/pi/.homeflix/homeflix.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )],
    format="%(asctime)s %(levelname)8s - %(message)s",
    level=logging.DEBUG
)

# Usage in application
logging.info(f"User {user_id} accessed {endpoint}")
logging.error(f"Database error: {str(e)}")
```

#### Performance Monitoring
```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # Log slow operations
            logging.warning(f"{func.__name__} took {execution_time:.2f}s")
        
        return result
    return wrapper
```

This technical specification provides comprehensive guidance for understanding, maintaining, and extending the HomeFlix platform while following established patterns and best practices.