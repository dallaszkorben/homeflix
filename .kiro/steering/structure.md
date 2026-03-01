# HomeFlix Project Structure

## Directory Architecture

```
homeflix/
├── var/www/homeflix/                    # Web application root
│   ├── index.html                       # Main SPA entry point
│   ├── config.js                        # Frontend configuration
│   ├── utils.js                         # Utility functions
│   ├── container.js                     # UI container classes
│   ├── generators.js                    # Dynamic UI generation
│   ├── selection_components.js          # UI selection components
│   ├── stylesheet.css                   # Main styling
│   ├── favicon.ico                      # Application icon
│   │
│   ├── script/                          # Third-party libraries
│   │   ├── jquery/                      # jQuery library
│   │   ├── jquery-ui/                   # jQuery UI components
│   │   ├── fancybox/                    # Lightbox functionality
│   │   ├── highlight/                   # Code highlighting
│   │   └── js-jaml/                     # YAML parsing
│   │
│   ├── images/                          # Static images
│   │   ├── categories/                  # Category thumbnails
│   │   ├── rating/                      # Star rating icons
│   │   ├── thumbnails/                  # Default thumbnails
│   │   ├── tools/                       # UI tool icons
│   │   └── product-image/               # Application branding
│   │
│   ├── logs/                            # Application logs
│   │   ├── access.log                   # Apache access log
│   │   └── error.log                    # Apache error log
│   │
│   ├── MEDIA/                           # Media storage (mounted)
│   │   ├── 01.Movie/                    # Movie collections
│   │   ├── 02.Music/                    # Music collections
│   │   ├── 03.Video/                    # Video collections
│   │   └── [other categories]/          # Additional media types
│   │
│   └── python/                          # Python backend
│       ├── homeflix.wsgi                # WSGI entry point
│       ├── env/                         # Virtual environment
│       └── homeflix/                    # Main Python package
│           ├── __init__.py
│           ├── card/                    # Media metadata handling
│           │   ├── __init__.py
│           │   ├── card_handle.py       # Card operations
│           │   ├── database.py          # Database operations
│           │   └── database_descriptor.yaml # Schema definition
│           │
│           ├── config/                  # Configuration management
│           │   ├── __init__.py
│           │   ├── config.py            # Configuration loader
│           │   └── card_menu.py         # Menu configuration
│           │
│           ├── restserver/              # REST API endpoints
│           │   ├── __init__.py
│           │   ├── ws_homeflix.py       # Main Flask application
│           │   ├── view_auth.py         # Authentication endpoints
│           │   ├── view_collect.py      # Content collection endpoints
│           │   ├── view_control.py      # System control endpoints
│           │   ├── view_info.py         # Information endpoints
│           │   ├── view_personal.py     # User preference endpoints
│           │   ├── view_stream.py       # Media streaming endpoints
│           │   └── view_translate.py    # Translation endpoints
│           │
│           ├── translator/              # Multi-language support
│           │   ├── __init__.py
│           │   ├── translator.py        # Translation engine
│           │   ├── dictionary.yaml      # Main translation dictionary
│           │   └── dictionary_[lang].yaml # Language-specific dictionaries
│           │
│           ├── property/                # Base property classes
│           │   ├── __init__.py
│           │   └── property.py          # YAML property handling
│           │
│           └── exceptions/              # Custom exceptions
│               ├── __init__.py
│               └── not_existing_table.py # Database exceptions
│
├── etc/apache2/                         # Apache configuration
│   ├── envvars                          # Environment variables
│   └── site-enabled/
│       └── homeflix.conf                # Virtual host configuration
│
├── home/pi/.homeflix/                   # User configuration
│   ├── config.yaml                      # Application configuration
│   ├── card_menu.yaml                   # Menu structure definition
│   └── homeflix.log                     # Application log
│
├── usr/local/bin/                       # System scripts
├── usr/share/icons/                     # System icons
│   └── homeflix-image.png               # Application icon
│
├── img/                                 # System images
│   └── homeflix.v1.2.5.img              # Raspberry Pi image
│
├── wiki/                                # Documentation
│   ├── preparation.md                   # Setup instructions
│   ├── database.md                      # Database documentation
│   └── solutions.md                     # Troubleshooting guide
│
├── .amazonq/rules/                      # AI assistant rules
│   ├── context-frontend.md              # Frontend context rules
│   ├── homeflix-data-architecture.md    # Data architecture rules
│   ├── mobile-touch-gestures.md         # Mobile interaction rules
│   ├── tracklist-modification-guide.md  # Music tracklist rules
│   ├── band-album-structure-creation-guide.md # Album structure rules
│   └── audio-poster-aspect-ratio.md     # Media aspect ratio rules
│
├── README.md                            # Project overview
├── .gitignore                           # Git ignore rules
└── lazydog.txt                          # Test file
```

## Component Architecture

### Frontend Components

#### Core JavaScript Modules
- **config.js**: Global configuration and initialization
- **utils.js**: Utility functions (path joining, cookies, device detection)
- **container.js**: UI container management and thumbnail display
- **generators.js**: Dynamic content generation from API responses
- **selection_components.js**: User interaction components

#### UI Component Hierarchy
```
ObjScrollSection (container.js)
├── ObjDescriptionContainer
├── ObjThumbnailController
└── ObjThumbnailContainer[]
    ├── ObjThumbnail[]
    └── ObjThumbnailSpace

Generator (generators.js)
├── RestGenerator
├── CategoryGenerator
├── MovieGenerator
├── MusicGenerator
└── [Other specialized generators]
```

### Backend Components

#### Flask Application Structure
```
WSHomeflix (ws_homeflix.py)
├── InfoView (/info/*)
├── CollectView (/collect/*)
├── TranslateView (/translate/*)
├── ControlView (/control/*)
├── PersonalView (/personal/*)
├── AuthView (/auth/*)
└── StreamView (/stream/*)
```

#### Core Python Modules
- **SqlDatabase**: Database operations and query building
- **CardHandle**: Media card operations and file system interaction
- **Translator**: Multi-language translation and localization
- **Config**: Configuration management and defaults
- **Property**: YAML file handling base class

### Data Architecture

#### Database Schema (SQLite)
```
Core Tables:
├── Card (media items)
├── Category (content categories)
├── Language (language codes)
├── Country (country codes)
├── Genre (content genres)
├── Theme (content themes)
├── Person (actors, directors, etc.)
└── MediaType (file format types)

Relationship Tables:
├── Card_Genre (many-to-many)
├── Card_Theme (many-to-many)
├── Card_Actor (many-to-many)
├── Card_Director (many-to-many)
├── Card_Sound (many-to-many)
├── Card_Sub (many-to-many)
└── [Other relationship tables]

User Tables:
├── User (user accounts)
├── History (viewing history)
├── Rating (user ratings)
├── Tag (user tags)
└── Search (search history)
```

#### File System Structure
```
Media Item Structure:
/MEDIA/[Category]/[Collection]/[Item]/
├── card.yaml                    # Metadata file
├── media/                       # Media files
│   └── [media_files]
├── screenshots/                 # Preview images
│   └── [screenshot_files]
└── thumbnails/                  # Thumbnail images
    └── [thumbnail_files]

Hierarchical Example:
/MEDIA/01.Movie/Action/The.Matrix-1999/
├── card.yaml
├── media/
│   └── The.Matrix-1999.mkv
├── screenshots/
│   └── screenshot_1920x1080.jpg
└── thumbnails/
    └── thumbnail_460x600.jpg
```

## Configuration Architecture

### YAML Configuration Files

#### card_menu.yaml Structure
```yaml
containers:
  - name: "categories"
    type: "hardcoded"
    items: [list of category items]
  
  - name: "movie_genres"
    type: "queried"
    query_params: [database query parameters]
    
  - name: "continue_playing"
    type: "personal"
    user_specific: true
```

#### card.yaml Structure (Media Metadata)
```yaml
category: movie
level: movie
title:
  onthumbnail: true
  orig: en
  titles:
    en: "Movie Title"
    hu: "Film Cím"
storylines:
  en: "Plot description..."
performer: "Director Name"
date: 2023
genres: [action, thriller]
origins: [us]
sounds: [en]
subs: [en, hu]
medium: "video=filename.mkv"
```

### Configuration Hierarchy
1. **System Defaults** (hardcoded in Python)
2. **Global Config** (`~/.homeflix/config.yaml`)
3. **User Preferences** (database User table)
4. **Session Settings** (Flask session)

## API Architecture

### REST Endpoint Organization

#### /auth/* - Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/status` - Session status

#### /collect/* - Content Collection
- `GET /collect/highest_level` - Top-level categories
- `GET /collect/next_level` - Child items
- `GET /collect/lowest_level` - Media items
- `POST /collect/filter` - Filtered content

#### /translate/* - Localization
- `GET /translate/labels` - UI labels
- `GET /translate/categories` - Category translations
- `GET /translate/genres` - Genre translations

#### /personal/* - User Data
- `GET /personal/history` - Viewing history
- `POST /personal/rating` - Rate content
- `GET /personal/preferences` - User settings

#### /stream/* - Media Delivery
- `GET /stream/media` - Media file streaming
- `GET /stream/subtitle` - Subtitle files

### Request/Response Patterns

#### Standard Response Format
```json
{
  "result": true,
  "data": [response_data],
  "message": "Success message",
  "error": null
}
```

#### Error Response Format
```json
{
  "result": false,
  "data": null,
  "message": "Error description",
  "error": "ERROR_CODE"
}
```

## Deployment Architecture

### System Services
- **Apache 2**: Web server with mod_wsgi
- **Python Virtual Environment**: Isolated dependencies
- **SQLite Database**: Local data storage
- **Systemd Services**: Application lifecycle management

### Network Architecture
```
Client Devices (Browser)
    ↓ HTTP/80
Apache Web Server
    ↓ WSGI
Python Flask Application
    ↓ SQLite
Database Files
    ↓ File System
Media Storage (USB/NAS)
```

### Security Architecture
- **Local Network Only**: No external internet exposure
- **Session-Based Auth**: Flask session management
- **File System Permissions**: Restricted media access
- **Input Validation**: SQL injection prevention

## Development Patterns

### Code Organization Principles
1. **Separation of Concerns**: Frontend/Backend/Data layers
2. **Configuration-Driven**: YAML-based customization
3. **Multi-Language Support**: Translation layer throughout
4. **RESTful Design**: Clean API boundaries
5. **Component-Based UI**: Reusable JavaScript classes

### Naming Conventions
- **Python**: snake_case for functions/variables, PascalCase for classes
- **JavaScript**: camelCase for functions/variables, PascalCase for classes
- **Files**: kebab-case for web assets, snake_case for Python modules
- **Database**: PascalCase for tables, snake_case for columns

### Error Handling Strategy
- **Frontend**: Try/catch with user-friendly messages
- **Backend**: Exception handling with logging
- **Database**: Transaction rollback on errors
- **API**: Consistent error response format