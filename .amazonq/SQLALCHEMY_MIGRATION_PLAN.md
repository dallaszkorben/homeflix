# SQLAlchemy Migration Plan for HomeFlix Database

## Overview
Step-by-step migration from raw SQLite to SQLAlchemy, ensuring each step works independently without breaking existing functionality.

## Phase 1: Infrastructure Setup

### Step 1: SQLAlchemy Setup & Coexistence
- [x] Install SQLAlchemy dependencies
- [x] Create SQLAlchemy engine alongside existing SQLite connection
- [x] Add basic session management
- [x] Test both systems work together

### Step 2: Create SQLAlchemy Models (Read-Only)
- [x] Create `models.py` file with all table definitions
- [x] Define relationships between models
- [x] Test model definitions by reading existing data
- [x] Verify schema matches current database

## Phase 2: Static/Lookup Tables Migration

### Step 3: Migrate Simple Lookup Tables
- [x] Convert `TABLE_CATEGORY` operations
- [x] Convert `TABLE_GENRE` operations
- [x] Convert `TABLE_LANGUAGE` operations
- [x] Convert `TABLE_COUNTRY` operations
- [x] Convert `TABLE_THEME` operations
- [x] Convert `TABLE_MEDIATYPE` operations
- [x] Convert `TABLE_PERSON` operations

### Step 4: Test Lookup Table Operations
- [x] Test CRUD operations for all lookup tables
- [x] Verify data integrity
- [x] Test foreign key relationships

## Phase 3: User Management Migration

### Step 5: Migrate User Table Operations
- [x] Convert `fill_up_user_table()` method
- [x] Convert `append_user()` method
- [x] Convert `login()` method
- [x] Convert `get_logged_in_user_data()` method
- [x] Convert `update_user_data()` method

### Step 6: Test User Management
- [x] Test user creation and authentication
- [x] Test user data updates
- [x] Verify password hashing works

## Phase 4: Core Card Entity Migration

### Step 7: Migrate Basic Card Operations
- [x] Convert `TABLE_CARD` basic CRUD operations
- [x] Convert `append_card_media()` method
- [x] Convert `append_hierarchy()` method
- [x] Test basic card creation and retrieval

### Step 8: Migrate Card Text/Language Operations
- [x] Convert `TABLE_TEXT_CARD_LANG` operations
- [x] Convert `TABLE_CARD_MEDIA` operations
- [x] Test multilingual card data

## Phase 5: Relationship Tables Migration

### Step 9: Migrate Many-to-Many Relationships
- [x] Convert `TABLE_CARD_GENRE` operations
- [x] Convert `TABLE_CARD_THEME` operations
- [x] Convert `TABLE_CARD_SOUND` operations
- [x] Convert `TABLE_CARD_SUB` operations
- [x] Convert `TABLE_CARD_ORIGIN` operations
- [x] Convert `TABLE_CARD_ACTOR` operations

### Step 10: Test Relationship Operations
- [x] Test adding/removing genres from cards
- [x] Test actor associations
- [x] Test sound/subtitle relationships

## Phase 6: Complex Query Methods Migration

### Step 11: Migrate Simple List Methods
- [x] Convert `get_list_of_actors()` method
- [x] Convert `get_list_of_actors_by_role_count()` method (delegated to original for complex recursive query)
- [x] Convert `get_list_of_voices()` method
- [x] Convert `get_list_of_voices_by_role_count()` method (delegated to original for complex recursive query)
- [x] Convert `get_list_of_directors()` method
- [x] Convert `get_list_of_directors_by_movie_count()` method (delegated to original for complex recursive query)
- [x] Convert `get_list_of_writers()` method
- [x] Convert `get_list_of_tags()` method

### Step 12: Migrate ABC/Title Methods
- [x] Convert `get_abc_of_movie_title()` method
- [x] Test alphabetical sorting and filtering

### Step 13: Migrate Card Hierarchy Methods
- [x] Convert `get_highest_level_cards()` method (SQLAlchemy version directly calls get_raw_query_of_highest_level)
- [x] Keep `get_raw_query_of_highest_level()` method (original retained - too complex for SQLAlchemy conversion)
- [x] Convert `get_next_level_cards()` method (SQLAlchemy version directly calls get_raw_query_of_next_level)
- [x] Keep `get_raw_query_of_next_level()` method (original retained - too complex for SQLAlchemy conversion)
- [x] Convert `get_lowest_level_cards()` method (SQLAlchemy version directly calls get_raw_query_of_lowest_level)
- [x] Keep `get_raw_query_of_lowest_level()` method (original retained - too complex for SQLAlchemy conversion)

### Step 14: Test Card Hierarchy
- [x] Test hierarchical card navigation (tested get_highest_level_cards_sqlalchemy, get_next_level_cards_sqlalchemy, get_lowest_level_cards_sqlalchemy)
- [x] Test complex filtering with hierarchy (tested genre filtering, view_state filtering)
- [x] Verify performance of complex queries (all methods work with real database, maintain same performance as originals)

## Phase 7: User Interaction Methods Migration

### Step 15: Migrate History Operations
- [x] Convert `get_history()` method (get_history_sqlalchemy)
- [x] Convert `update_play_position()` method (update_play_position_sqlalchemy)
- [x] Convert `update_rating()` method (update_rating_sqlalchemy)
- [x] Convert `insert_tag()` method (insert_tag_sqlalchemy)
- [x] Convert `delete_tag()` method (delete_tag_sqlalchemy)
- [x] Convert `get_tags()` method (get_tags_sqlalchemy - delegates to original for complex query)
- [x] Test playback history tracking (all Step 15 methods tested and working)

### Step 16: Migrate Filter Methods
- [x] Convert `get_sql_where_condition_from_text_filter()` method
- [x] Convert `get_sql_like_where_condition_from_text_filter()` method
- [x] Test complex text filtering

### Step 17: Migrate JSON Conversion
- [x] Convert `get_converted_query_to_json()` method (no conversion needed - pure data transformation)
- [x] Test JSON response formatting (existing method works with SQLAlchemy results)

## Phase 8: Cleanup and Optimization

### Step 18: Remove Legacy Code (Method-by-Method)
#### Step 18.1: Replace Simple Lookup Methods
- [x] Replace `get_list_of_actors()` with SQLAlchemy version
- [x] Replace `get_list_of_voices()` with SQLAlchemy version
- [x] Replace `get_list_of_directors()` with SQLAlchemy version
- [x] Replace `get_list_of_writers()` with SQLAlchemy version
- [x] Replace `get_list_of_tags()` with SQLAlchemy version

#### Step 18.2: Replace ABC/Title Methods
- [x] Replace `get_abc_of_movie_title()` with SQLAlchemy version

#### Step 18.3: Replace Filter Methods
- [x] Replace `get_sql_where_condition_from_text_filter()` with SQLAlchemy version
- [x] Replace `get_sql_like_where_condition_from_text_filter()` with SQLAlchemy version

#### Step 18.4: Replace History Methods
- [x] Replace `get_history()` with SQLAlchemy version
- [x] Replace `update_play_position()` with SQLAlchemy version
- [x] Replace `update_rating()` with SQLAlchemy version
- [x] Replace `insert_tag()` with SQLAlchemy version
- [x] Replace `delete_tag()` with SQLAlchemy version

#### Step 18.5: Replace Card Hierarchy Methods
- [x] Replace `get_highest_level_cards()` with SQLAlchemy version
- [x] Replace `get_next_level_cards()` with SQLAlchemy version
- [x] Replace `get_lowest_level_cards()` with SQLAlchemy version

#### Step 18.6: Replace User Management Methods
- [x] Replace `fill_up_user_table()` with SQLAlchemy version
- [x] Replace `append_user()` with SQLAlchemy version
- [x] Replace `login()` with SQLAlchemy version
- [x] Replace `get_logged_in_user_data()` with SQLAlchemy version
- [x] Replace `update_user_data()` with SQLAlchemy version

#### Step 18.7: Replace Card Operations
- [x] Replace `append_card_media()` with SQLAlchemy version
- [x] Replace `append_hierarchy()` with SQLAlchemy version

#### Step 18.8: Final Cleanup
- [x] Remove old SQLite connection code (kept essential SQLite for initialization)
- [x] Remove unused raw SQL query methods (removed duplicate SQLAlchemy helper methods)
- [x] Clean up unused imports (minimal cleanup to maintain stability)

### Step 19: Performance Optimization
- [ ] Add query optimization
- [ ] Add proper indexing
- [ ] Add connection pooling
- [x] Add query caching where appropriate (implemented in-memory cache for high-priority methods)

### Step 20: Error Handling Enhancement
- [ ] Add SQLAlchemy-specific error handling
- [ ] Add transaction management
- [ ] Add rollback mechanisms

### Step 21: Final Testing
- [ ] Run full application test suite
- [ ] Test all user workflows
- [ ] Performance testing
- [ ] Load testing

## Phase 9: Documentation and Deployment

### Step 22: Documentation
- [ ] Update code documentation
- [ ] Create migration notes
- [ ] Update database schema documentation

### Step 23: Deployment Preparation
- [ ] Create database migration scripts
- [ ] Test migration on copy of production data
- [ ] Create rollback procedures

## Critical Notes

### Method Complexity Priority (High to Low)
1. **Most Complex**: `get_raw_query_of_lowest_level()` - Massive recursive query
2. **Very Complex**: `get_raw_query_of_highest_level()` - Complex joins and unions
3. **Very Complex**: `get_raw_query_of_next_level()` - Hierarchical navigation
4. **Complex**: `get_converted_query_to_json()` - Data transformation
5. **Medium**: Filter methods with text processing
6. **Simple**: Basic CRUD operations

### Testing Strategy
- Each step must pass all existing tests
- Create unit tests for each converted method
- Test with real data at each step
- Maintain backward compatibility until full migration

### Rollback Strategy
- Keep original methods as `_legacy` versions
- Use feature flags to switch between implementations
- Maintain database compatibility throughout migration

### Performance Considerations
- Monitor query performance at each step
- Compare SQLAlchemy vs raw SQL performance
- Optimize queries that show performance regression

## Dependencies
- SQLAlchemy >= 2.0
- Alembic (for migrations)
- pytest (for testing)