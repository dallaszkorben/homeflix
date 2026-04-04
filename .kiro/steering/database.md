# HomeFlix Database Schema Documentation

## Database Overview

HomeFlix uses SQLite as its primary database engine with a comprehensive schema designed to handle media metadata, user management, and content relationships. The database is organized into two main categories: **Static Tables** (media content) and **Personal Tables** (user data).

## Database Architecture

### Database Files
- **Location**: `~/.homeflix/homeflix.db`
- **Engine**: SQLite 3.36+
- **Connection**: Single connection with thread safety and row factory
- **Backup**: Automatic recreation if corrupted

### Table Categories

#### Static Tables (Media Content)
Tables that store media metadata and are rebuilt when content changes:
- Core content tables (Card, Category, Person, etc.)
- Relationship tables (Card_Genre, Card_Actor, etc.)
- Lookup tables (Language, Country, Genre, etc.)

#### Personal Tables (User Data)
Tables that store user-specific data and preferences:
- User management (User, History, Rating, Tag)
- Search functionality (Search, Search_Request, etc.)

## Core Tables

### Card Table (Primary Content)
The central table representing all media items in the system.

```sql
CREATE TABLE Card (
    id                  TEXT        NOT NULL,           -- MD5 hash of card path
    id_title_orig       INTEGER     NOT NULL,           -- Original language ID
    id_category         INTEGER     NOT NULL,           -- Category ID (movie, music, etc.)
    isappendix          BOOLEAN     NOT NULL,           -- Is supplementary content
    show                BOOLEAN     NOT NULL,           -- Should be displayed
    download            BOOLEAN     NOT NULL,           -- Available for download
    decade              TEXT,                           -- Decade (1990, 2000, etc.)
    date                TEXT,                           -- Release date
    length              TEXT,                           -- Duration (HH:MM:SS)
    full_time           DECIMAL(10,2),                  -- Full duration in seconds
    net_start_time      DECIMAL(10,2),                  -- Net start time in seconds
    net_stop_time       DECIMAL(10,2),                  -- Net stop time in seconds
    source_path         TEXT        NOT NULL,           -- Relative path from media root
    absolute_media_path TEXT        NOT NULL,           -- Absolute file system path
    basename            TEXT        NOT NULL,           -- Base filename
    sequence            INTEGER,                        -- Order within parent
    id_higher_card      INTEGER,                        -- Parent card ID (hierarchy)
    level               TEXT,                           -- Hierarchy level (movie, season, episode, lp, record)
    title_on_thumbnail  BOOLEAN     NOT NULL,           -- Show title on thumbnail
    title_show_sequence TEXT        NOT NULL,           -- Sequence display format
    
    FOREIGN KEY (id_title_orig) REFERENCES Language (id),
    FOREIGN KEY (id_higher_card) REFERENCES Card (id)
);
```

**Key Fields Explained:**
- **id**: MD5 hash of the card's file system path, ensuring uniqueness
- **level**: Defines hierarchy position (`movie`, `season`, `episode`, `lp`, `record`)
- **sequence**: Order within parent container (episode 1, 2, 3 or track 1, 2, 3)
- **id_higher_card**: Creates parent-child relationships for series/albums

### Lookup Tables

#### Category Table
Defines content categories (movie, music_audio, music_video, etc.)

```sql
CREATE TABLE Category (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(name)
);
```

#### Person Table
Stores all people (actors, directors, writers, performers, etc.)

```sql
CREATE TABLE Person (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL
);
```

#### Language Table
Language codes for audio, subtitles, and original content

```sql
CREATE TABLE Language (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,                    -- Language code (en, hu, de, etc.)
    UNIQUE(name)
);
```

#### Country Table
Country codes for content origins

```sql
CREATE TABLE Country (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,                    -- Country code (us, gb, hu, etc.)
    UNIQUE(name)
);
```

#### Genre Table
Content genres (action, comedy, rock, jazz, etc.)

```sql
CREATE TABLE Genre (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(name)
);
```

#### Theme Table
Content themes (war, love, christmas, etc.)

```sql
CREATE TABLE Theme (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(name)
);
```

#### MediaType Table
File format types (video, audio, image, document)

```sql
CREATE TABLE MediaType (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(name)
);
```

## Relationship Tables (Many-to-Many)

### Content Relationships

#### Card_Genre
Links cards to their genres

```sql
CREATE TABLE Card_Genre (
    id_card INTEGER NOT NULL,
    id_genre INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_genre) REFERENCES Genre (id),
    PRIMARY KEY (id_card, id_genre)
);
```

#### Card_Theme
Links cards to their themes

```sql
CREATE TABLE Card_Theme (
    id_card INTEGER NOT NULL,
    id_theme INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_theme) REFERENCES Theme (id),
    PRIMARY KEY (id_card, id_theme)
);
```

### Audio/Language Relationships

#### Card_Sound
Links cards to their audio languages

```sql
CREATE TABLE Card_Sound (
    id_card INTEGER NOT NULL,
    id_sound INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_sound) REFERENCES Language (id),
    PRIMARY KEY (id_card, id_sound)
);
```

#### Card_Sub
Links cards to their subtitle languages

```sql
CREATE TABLE Card_Sub (
    id_card INTEGER NOT NULL,
    id_sub INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_sub) REFERENCES Language (id),
    PRIMARY KEY (id_card, id_sub)
);
```

#### Card_Origin
Links cards to their country origins

```sql
CREATE TABLE Card_Origin (
    id_card INTEGER NOT NULL,
    id_origin INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_origin) REFERENCES Country (id),
    PRIMARY KEY (id_card, id_origin)
);
```

### People Relationships

#### Card_Actor
Links cards to their actors

```sql
CREATE TABLE Card_Actor (
    id_card INTEGER NOT NULL,
    id_actor INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_actor) REFERENCES Person (id),
    PRIMARY KEY (id_card, id_actor)
);
```

#### Card_Director
Links cards to their directors

```sql
CREATE TABLE Card_Director (
    id_card INTEGER NOT NULL,
    id_director INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_director) REFERENCES Person (id),
    PRIMARY KEY (id_card, id_director)
);
```

#### Card_Writer
Links cards to their writers

```sql
CREATE TABLE Card_Writer (
    id_card INTEGER NOT NULL,
    id_writer INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_writer) REFERENCES Person (id),
    PRIMARY KEY (id_card, id_writer)
);
```

#### Card_Voice
Links cards to their voice actors

```sql
CREATE TABLE Card_Voice (
    id_card INTEGER NOT NULL,
    id_voice INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_voice) REFERENCES Person (id),
    PRIMARY KEY (id_card, id_voice)
);
```

#### Card_Star
Links cards to their starring actors

```sql
CREATE TABLE Card_Star (
    id_card INTEGER NOT NULL,
    id_star INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_star) REFERENCES Person (id),
    PRIMARY KEY (id_card, id_star)
);
```

#### Card_Performer
Links cards to their performers (music)

```sql
CREATE TABLE Card_Performer (
    id_card INTEGER NOT NULL,
    id_performer INTEGER NOT NULL,
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_performer) REFERENCES Person (id),
    PRIMARY KEY (id_card, id_performer)
);
```

#### Additional People Tables
Similar structure for:
- `Card_Host` - Show hosts
- `Card_Guest` - Show guests  
- `Card_Interviewer` - Interviewers
- `Card_Interviewee` - Interviewees
- `Card_Presenter` - Presenters
- `Card_Lecturer` - Lecturers
- `Card_Reporter` - Reporters

### Text Content

#### Text_Card_Lang
Stores multilingual text content (titles, storylines, lyrics)

```sql
CREATE TABLE Text_Card_Lang (
    text TEXT NOT NULL,                    -- The actual text content
    id_language INTEGER NOT NULL,          -- Language of the text
    id_card INTEGER NOT NULL,              -- Card this text belongs to
    type TEXT NOT NULL,                    -- Type: 'title', 'storyline', 'lyrics'
    FOREIGN KEY (id_language) REFERENCES Language (id),
    FOREIGN KEY (id_card) REFERENCES Card (id),
    PRIMARY KEY (id_card, id_language, type)
);
```

### Media Files

#### Card_Media
Links cards to their actual media files

```sql
CREATE TABLE Card_Media (
    name TEXT NOT NULL,                    -- Filename
    id_card INTEGER NOT NULL,              -- Card this media belongs to
    id_mediatype INTEGER NOT NULL,         -- Type of media file
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_mediatype) REFERENCES MediaType (id),
    PRIMARY KEY (id_card, id_mediatype, name)
);
```

### Role System

#### Role Table
Defines character roles for actors/voices

```sql
CREATE TABLE Role (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    id_card INTEGER NOT NULL,              -- Card this role belongs to
    name TEXT NOT NULL,                    -- Role/character name
    FOREIGN KEY (id_card) REFERENCES Card (id),
    UNIQUE (id_card, name)
);
```

#### Actor_Role
Links actors to their roles

```sql
CREATE TABLE Actor_Role (
    id_actor INTEGER NOT NULL,
    id_role INTEGER NOT NULL,
    FOREIGN KEY (id_actor) REFERENCES Person (id),
    FOREIGN KEY (id_role) REFERENCES Role (id),
    PRIMARY KEY (id_actor, id_role)
);
```

#### Voice_Role
Links voice actors to their roles

```sql
CREATE TABLE Voice_Role (
    id_voice INTEGER NOT NULL,
    id_role INTEGER NOT NULL,
    FOREIGN KEY (id_voice) REFERENCES Person (id),
    FOREIGN KEY (id_role) REFERENCES Role (id),
    PRIMARY KEY (id_voice, id_role)
);
```

## User Management Tables

### User Table
Stores user accounts and preferences

```sql
CREATE TABLE User (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,                    -- Username
    password TEXT NOT NULL,                -- Hashed password
    is_admin BOOLEAN NOT NULL,             -- Admin privileges
    id_language INTEGER NOT NULL,          -- Preferred language
    descriptor_color TEXT NOT NULL,        -- UI color preference
    show_original_title BOOLEAN NOT NULL,  -- Show original titles
    show_lyrics_anyway BOOLEAN NOT NULL,   -- Always show lyrics
    show_storyline_anyway BOOLEAN NOT NULL, -- Always show storylines
    play_continuously BOOLEAN NOT NULL,    -- Auto-play next item
    history_days INTEGER NOT NULL,         -- History retention days
    created_epoch INTEGER NOT NULL,        -- Account creation timestamp
    FOREIGN KEY (id_language) REFERENCES Language (id),
    UNIQUE(name)
);
```

### History Table
Tracks user viewing history and progress

```sql
CREATE TABLE History (
    start_epoch INTEGER NOT NULL,          -- When viewing started
    recent_epoch INTEGER NOT NULL,         -- Last activity timestamp
    recent_position DECIMAL(10,2) NOT NULL, -- Playback position in seconds
    id_card TEXT NOT NULL,                 -- Card being watched
    id_user INTEGER NOT NULL,              -- User watching
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_user) REFERENCES User (id),
    PRIMARY KEY (id_card, id_user, start_epoch)
);
```

### Rating Table
Stores user ratings for content

```sql
CREATE TABLE Rating (
    id_card TEXT NOT NULL,                 -- Card being rated
    id_user INTEGER NOT NULL,              -- User rating
    rate INTEGER CHECK(rate BETWEEN 0 AND 5), -- Rating (0-5 stars)
    skip_continuous_play BOOLEAN NOT NULL, -- Skip in continuous play
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_user) REFERENCES User (id),
    PRIMARY KEY (id_card, id_user)
);
```

### Tag Table
User-defined tags for content

```sql
CREATE TABLE Tag (
    id_card TEXT NOT NULL,                 -- Card being tagged
    id_user INTEGER NOT NULL,              -- User creating tag
    name TEXT NOT NULL,                    -- Tag name
    FOREIGN KEY (id_card) REFERENCES Card (id),
    FOREIGN KEY (id_user) REFERENCES User (id),
    PRIMARY KEY (id_card, id_user, name)
);
```

## Search System Tables

### Search Request Tables
Track API endpoints for search functionality

#### Search_Request_Method
```sql
CREATE TABLE Search_Request_Method (
    name TEXT PRIMARY KEY NOT NULL         -- HTTP method (GET, POST)
);
```

#### Search_Request_Protocol
```sql
CREATE TABLE Search_Request_Protocol (
    name TEXT PRIMARY KEY NOT NULL         -- Protocol (http, https)
);
```

#### Search_Request_Path
```sql
CREATE TABLE Search_Request_Path (
    name TEXT PRIMARY KEY NOT NULL         -- API path (/collect/lowest, etc.)
);
```

#### Search_Request
```sql
CREATE TABLE Search_Request (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    id_request_method TEXT NOT NULL,
    id_request_protocol TEXT NOT NULL,
    id_request_path TEXT NOT NULL,
    FOREIGN KEY (id_request_method) REFERENCES Search_Request_Method (name),
    FOREIGN KEY (id_request_protocol) REFERENCES Search_Request_Protocol (name),
    FOREIGN KEY (id_request_path) REFERENCES Search_Request_Path (name),
    UNIQUE(id_request_method, id_request_protocol, id_request_path)
);
```

### Search Tables
Store user search queries and results

#### Search
```sql
CREATE TABLE Search (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    thumbnail_id TEXT NOT NULL,            -- UI thumbnail identifier
    title TEXT NOT NULL,                   -- Search title/name
    id_search_request INTEGER NOT NULL,    -- Associated request type
    id_user INTEGER NOT NULL,              -- User who created search
    FOREIGN KEY (id_search_request) REFERENCES Search_Request (id),
    FOREIGN KEY (id_user) REFERENCES User (id)
);
```

#### Search_Data_Field
```sql
CREATE TABLE Search_Data_Field (
    id_search INTEGER NOT NULL,            -- Search this data belongs to
    name TEXT NOT NULL,                    -- Field name (category, genre, etc.)
    value TEXT NOT NULL,                   -- Field value
    FOREIGN KEY (id_search) REFERENCES Search (id),
    PRIMARY KEY (id_search, name)
);
```

## Database Patterns and Relationships

### Hierarchical Content Structure

The Card table supports hierarchical relationships through the `id_higher_card` field:

```
Movie Series
├── Season 1 (id_higher_card → Series ID)
│   ├── Episode 1 (id_higher_card → Season 1 ID)
│   ├── Episode 2 (id_higher_card → Season 1 ID)
│   └── Episode 3 (id_higher_card → Season 1 ID)
└── Season 2 (id_higher_card → Series ID)
    ├── Episode 1 (id_higher_card → Season 2 ID)
    └── Episode 2 (id_higher_card → Season 2 ID)

Music Album
├── Track 1 (id_higher_card → Album ID)
├── Track 2 (id_higher_card → Album ID)
└── Track 3 (id_higher_card → Album ID)
```

### Content Levels

The `level` field defines the type of content:
- **`movie`**: Standalone movie
- **`series`**: TV series container
- **`season`**: Season within a series
- **`episode`**: Individual episode
- **`lp`**: Music album
- **`record`**: Individual music track

### Media Card Level Condition

The system uses a specific condition to identify playable media:
```sql
MEDIA_CARD_LEVEL_CONDITION = "(card.level IS NULL OR card.level = 'record' OR card.level = 'episode')"
```

This identifies cards that contain actual media files (not just containers).

### Query Filter Level (filter_on parameter)

The `filter_on` parameter controls at which hierarchy level filtering/searching happens in the recursive queries. It works together with the `level` parameter to determine both where to filter and what to show.

#### filter_on values

- **`filter_on=None` or `'v'` (default)**: Filter at the **LOWEST level** (media-level cards: episodes, records, standalone movies). The recursive CTE starts from these cards, applies all WHERE filters (genre, actor, theme, etc.) there, then walks UP the hierarchy to find their parent containers. Example use cases:
  - "Find all series that contain a Sci-Fi episode" (filter genre at episode level, show series)
  - "Search by record name 'The Robots', show the band Kraftwerk"
  - "Show bands that have records in a given genre"

- **`filter_on='-'`**: Filter at the **HIGHEST level** (top-level cards: franchises, series, bands). No recursive walk needed — filters are applied directly on top-level cards. Example use cases:
  - "Movies in ABC" — show Alien Franchise, Austin Powers Franchise, etc. by their top-level name
  - "Search by band name Kraftwerk" — filter on the band-level card directly

Both modes always **show** the appropriate level (highest or given), but the difference is where the filter criteria are applied. This is intentional — many combinations are needed (search by record name but show band, search by band name but show records, etc.).

#### SQL CASE logic

In the base case WHERE clause (which cards to start recursion from):
```sql
-- filter_on=None/v: start from media-level cards
WHEN (:filter_on IS NULL OR :filter_on = 'v') THEN MEDIA_CARD_LEVEL_CONDITION

-- filter_on='-': start from top-level cards
WHEN :filter_on = '-' THEN card.id_higher_card IS NULL
```

In the outer WHERE clause (which cards to show from recursive result):
```sql
-- Both cases show the highest level when level is not specified
WHEN (:level IS NULL) THEN id_higher_card IS NULL
```

#### Performance implications

The `filter_on=None` path is significantly slower because it starts from all media-level cards (e.g., 1,636 movie cards) with 18+ LEFT JOINs each, then walks up the hierarchy recursively. The `filter_on='-'` path starts from only top-level cards (e.g., 285 movie cards) with no recursive walk needed.

### ID Generation

Card IDs are generated using MD5 hashing of the file system path:
```python
hasher = hashlib.md5()
hasher.update(card_path.encode('utf-8'))
card_id = hasher.hexdigest()
```

This ensures consistent, unique identifiers based on file location.

## Query Patterns

### Common Query Examples

#### Get All Movies in a Genre
```sql
SELECT c.* FROM Card c
JOIN Card_Genre cg ON c.id = cg.id_card
JOIN Genre g ON cg.id_genre = g.id
WHERE g.name = 'action' AND c.category = 'movie';
```

#### Get User's Viewing History
```sql
SELECT c.*, h.recent_position, h.recent_epoch
FROM Card c
JOIN History h ON c.id = h.id_card
WHERE h.id_user = ? 
ORDER BY h.recent_epoch DESC;
```

#### Get Series Episodes in Order
```sql
SELECT * FROM Card 
WHERE id_higher_card = ? 
ORDER BY sequence ASC;
```

#### Get Multilingual Titles
```sql
SELECT tcl.text, l.name as language
FROM Text_Card_Lang tcl
JOIN Language l ON tcl.id_language = l.id
WHERE tcl.id_card = ? AND tcl.type = 'title';
```

### Performance Considerations

#### Indexes
The database relies on SQLite's automatic indexing for primary keys and unique constraints. Additional indexes may be beneficial for:
- `Card.source_path` (file system queries)
- `Card.id_higher_card` (hierarchy traversal)
- `History.id_user, History.recent_epoch` (user history)

#### Query Optimization
- Use parameterized queries to prevent SQL injection
- Leverage foreign key relationships for joins
- Consider the MEDIA_CARD_LEVEL_CONDITION for performance
- Use LIMIT clauses for large result sets

## Database Maintenance

### Initialization Process
1. Check if static tables exist and are valid
2. If corrupted, drop and recreate all static tables
3. Populate lookup tables from translation dictionaries
4. Scan file system and populate Card tables
5. Check personal tables and create if missing
6. Create default admin and user accounts

### Data Population
- **Static tables**: Populated from file system scanning
- **Lookup tables**: Populated from YAML translation dictionaries
- **Personal tables**: Created with default users and empty data

### Backup and Recovery
- Database automatically recreates if corrupted
- File system scanning rebuilds all media metadata
- User data (history, ratings, tags) preserved separately
- Configuration-driven paths allow database relocation

This comprehensive database schema supports HomeFlix's rich media organization, user management, and search functionality while maintaining performance and data integrity.