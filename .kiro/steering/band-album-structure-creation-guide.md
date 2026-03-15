# Band Album Structure Creation Guide

## Overview
This guide provides a standardized process for creating organized album structures for music collections, following a consistent template pattern.

## Required Information for Execution
**CRITICAL**: All four pieces of information must be provided to execute the process:

1. **Band Name** - Name of the performing artist/band
2. **Album Name** - Title of the album 
3. **Absolute Path** - Full path to the album folder containing MP3 files
4. **Screenshots & Thumbnails Folders** - Must exist in the album folder

**If any information is missing, execution cannot proceed.**

## Template Reference
- Source template: `/media/akoel/vegyes/MEDIA/02.Music/02.Audio/Supertramp/The.Very.Best.Of.Supertramp`
- Additional reference: `/media/akoel/vegyes/MEDIA/02.Music/02.Audio/Kraftwerk/Kraftwerk-1977-Trans.Europa.Express-en`

## Album Structure Creation Process

### STEP 0: MP3 File Naming (FIRST STEP)

#### Naming Rules for Media Files
**Format**: `Band-Album-Index-Title.extension`

1. **Band name**: Replace spaces with dots (.)
2. **Album name**: Replace spaces with dots (.), separated by dash (-)
3. **Index**: 2-digit format with leading zeros (01, 02, etc.), separated by dash (-)
4. **Title**: Replace spaces with dots (.), separated by dash (-)
5. **Special character handling**:
   - `&` → replace with `and`
   - `!` → remove/ignore
   - `?` → remove/ignore
   - `'` → remove/ignore
   - `()` → remove/ignore

#### Example Transformations
- `Artist Name - Album Title - 01 - Song Title.mp3` → `Artist.Name-Album.Title-01-Song.Title.mp3`
- `Boys say go!` → `Boys.Say.Go`
- `What's your name?` → `Whats.Your.Name`

### Main Structure Components

#### Album Level
- `card.yaml` - Album metadata with:
  - category: music_audio
  - level: lp
  - performer: [Band Name]
  - date: [Year], decade: [Decade]
  - genres: [Genre list]
  - origins: [Country codes]
  - **storylines**: Complete track listing with durations
    - Format: `Number.\tTrack Title\t\t\tDuration`
    - Lists all tracks in order with their lengths

#### Track Level (01-XX)
Each track folder contains:
- `card.yaml` - Track metadata with:
  - category: music_audio, primarymediatype: audio
  - level: record, sequence: [track_number]
  - title with proper track names
  - lyrics: placeholder or actual lyrics
  - length/netstart/netstop from actual MP3 durations
- `media/` - folder containing the MP3 file
- `screenshots/` - copied from album level
- `thumbnails/` - copied from album level

### Step-by-Step Process

**STEP 0 (FIRST)**: Rename MP3 files according to naming rules
1. Create main album card.yaml with proper metadata
2. Add storylines section with complete track listing and durations
3. Create numbered track directories with media/screenshots/thumbnails subfolders
4. Create track card.yaml files with proper metadata structure
5. Copy album-level screenshots/thumbnails to all tracks
6. Extract and update actual MP3 durations
7. Move MP3 files to respective track media folders
8. **Lyrics Addition (Automated Process)**
   - **IMPORTANT**: Activate virtual environment first:
     ```bash
     source /home/akoel/Projects/python/homeflix/var/www/homeflix/python/env/bin/activate
     ```
   - Use automated lyrics fetcher script:
     ```bash
     python3 /home/akoel/Projects/python/homeflix/var/fetch_lyrics.py '/path/to/album/folder'
     ```
   - Script automatically:
     - Reads artist/album from main card.yaml
     - Fetches lyrics using Genius API with token
     - Cleans lyrics (removes headers, adds proper spacing between sections)
     - **Handles instrumental tracks**: Sets empty lyrics and `sounds: []`
     - Updates all track card.yaml files with formatted lyrics
   - **Requirements**: Album must have proper structure with main card.yaml and track directories

### Key Operations

1. **Directory Structure Creation**
   ```bash
   for i in {02..XX}; do mkdir -p "$i/media" "$i/screenshots" "$i/thumbnails"; done
   ```

2. **Main Album card.yaml Creation**
   - Set proper metadata for band and album
   - Include storylines with track listing

3. **Track card.yaml Files Creation**
   - Individual track files with proper sequence numbering
   - Track titles from MP3 filenames

4. **Screenshots/Thumbnails Distribution**
   ```bash
   for i in {01..XX}; do
     cp screenshots/* "$i/screenshots/"
     cp thumbnails/* "$i/thumbnails/"
   done
   ```

5. **Duration Extraction & Update**
   - Use ffprobe to get MP3 durations
   - Update length: [actual_duration]
   - Set netstart: [same_as_length]
   - Set netstop: 00:00:00
   - **TIME FORMAT**: Always use HH:MM:SS format (3 sections only)
     - Examples: 00:03:45, 00:06:32, 01:04:15
     - Never use 4 sections or MM:SS format in card.yaml files

6. **MP3 File Organization**
   ```bash
   for i in {01..XX}; do
     mv [Band].[Album]-$i-*.mp3 "$i/media/"
   done
   ```

### Scripts Used
- `rename_files.py` - Rename MP3 files according to naming rules
- `update_durations.py` - Extract MP3 durations and update card.yaml
- `fetch_lyrics.py` - **Working automated lyrics fetcher** (requires virtual environment activation)
  - Location: `/home/akoel/Projects/python/homeflix/var/fetch_lyrics.py`
  - Uses Genius API with proper token authentication
  - Cleans and formats lyrics automatically

### Storylines Format
```yaml
storylines:
  en: |
    <table class="playlist-table">
        <tr><td>1.</td><td>Track Title                    </td><td>Duration</td></tr>
        <tr><td>2.</td><td>Track Title                    </td><td>Duration</td></tr>
        ...
    </table>
```
- **CRITICAL**: Use HTML table format with 3 separate `<td>` elements:
  1. Track number with period (1., 2., etc.)
  2. Track title (padded with spaces for alignment)
  3. Duration (M:SS or MM:SS format)
- **4-space indentation** for table rows
- **Vertical alignment**: Pad track titles with spaces to align duration columns
- **NEVER use plain text format** - always use HTML table structure
- Lists all album tracks in sequential order

### Key Metadata Fields
- **Album**: category, level, title, storylines, performer, date, decade, sounds, genres, origins
- **Track**: category, primarymediatype, level, sequence, title, lyrics, performer, date, decade, length, netstart, netstop, sounds, genres, origins

### Correct Title Format
**CRITICAL**: Always use this exact title format in card.yaml files:
```yaml
title:
  onthumbnail: true
  showsequence: ""
  orig: hu
  titles:
    hu: [Title Text]
```
**NEVER use the simple format**: `title:\n  hu: [Title Text]`
**IMPORTANT**: showsequence must have empty string value `""`, not be completely empty

### Correct Sounds Field Format
**IMPORTANT**: Use language code, NOT 'music':
```yaml
sounds:
  - hu  # For Hungarian content
  - en  # For English content
```
**NEVER use**: `sounds:\n  - music`

### Complete Card.yaml Templates

#### Album Level card.yaml Template:
```yaml
category: music_audio
level: lp
sequence: -1
title:
  onthumbnail: true
  showsequence:
  orig: hu
  titles:
    hu: [Album Title]
storylines:
  hu: |
    <table class="playlist-table">
        <tr><td>1.</td><td>Track Title                    </td><td>Duration</td></tr>
        <tr><td>2.</td><td>Track Title                    </td><td>Duration</td></tr>
        ...
    </table>
performer: [Band Name]
date: [Year]
decade: [Decade]
sounds:
  - hu
genres:
  - alternative
origins:
  - hu
```

#### Track Level card.yaml Template:
```yaml
category: music_audio
primarymediatype: audio
level: record
sequence: [Track Number]
title:
  onthumbnail: true
  showsequence:
  orig: hu
  titles:
    hu: [Track Title]
lyrics:
  hu: |
    [Lyrics to be added]
performer: [Band Name]
date: [Year]
decade: [Decade]
length: [HH:MM:SS]
netstart: [HH:MM:SS]
netstop: 00:00:00
sounds:
  - hu
genres:
  - alternative
origins:
  - hu
```
- **CRITICAL FIELD ORDERING**:
  - **sequence field MUST come immediately after level field and before title field**
  - **storylines field MUST come immediately after title field and before performer field**
  - **length, netstart, netstop MUST come immediately after decade field**
  - **lyrics field MUST come after title field and before performer field**
  - **DO NOT place duration fields at the end of the file**
- **Time Format Requirements**:
  - **Track card.yaml**: length/netstart/netstop must use HH:MM:SS format (00:03:45, 00:06:32)
  - **Album storylines**: Use M:SS or MM:SS format (3:45, 6:32)
- **Genre Validation**: 
  - **IMPORTANT**: Before adding genres, verify codes exist in `/home/akoel/Projects/python/homeflix/var/www/homeflix/python/homeflix/translator/dictionary.yaml`
  - **Valid music genres include**: synthpop, new_wave, electronic, alternative, pop, rock, classical, jazz, ambient, etc.
  - **Location**: Check `genre: > music:` section in dictionary.yaml
- **Album Sequence**: 
  - **Set to -1** to let folder name control the order
  - **Location**: Must come immediately after `level` field and before `title` field

### Important Processing Rules

#### Missing Track Handling
- **NEVER reorder tracks** if some are missing from original numbering
- **Keep original track indexes** even if gaps exist (e.g., 01, 03, 04, 05 if track 02 is missing)
- **Skip missing numbers** in directory creation and storylines
- **Example**: If tracks 01, 03-11 exist, create directories 01, 03, 04, 05, 06, 07, 08, 09, 10, 11

#### Lyrics Processing
- **Empty lines must be truly empty** - no spaces or tabs
- **Clean whitespace** from blank lines between verses
- **Preserve verse structure** with proper empty line separation
- **Use proper encoding** (CP1250 or ISO-8859-2) for Hungarian characters
- **Extract from text files** when available, matching track titles

#### File Reconstruction
- **Backup existing lyrics** before restructuring
- **Reuse matching lyrics** when track titles correspond between albums
- **Update durations** when replacing MP3 files
- **Preserve metadata** during file system reconstruction

### Final Structure Verification
- ✅ MP3 files renamed according to naming rules
- ✅ Album card.yaml with metadata and storylines
- ✅ Track directories with proper structure (01-XX)
- ✅ Screenshots/thumbnails distributed to all tracks
- ✅ Actual MP3 durations extracted and updated
- ✅ MP3 files moved to respective track media folders
- ✅ Lyrics addition (automated process with virtual environment)

## Execution Requirements Reminder
**Before starting any album structure creation, ensure you have:**
1. **Band Name** (e.g., "Depeche Mode")
2. **Album Name** (e.g., "Speak & Spell") 
3. **Absolute Path** (e.g., "/path/to/album/folder")
4. **Screenshots & Thumbnails Folders** - Must exist in album folder:
   - `screenshots/` folder with album artwork/images (must contain files)
   - `thumbnails/` folder with thumbnail versions (must contain files)

**VALIDATION REQUIRED**: 
- Check if `screenshots/` and `thumbnails/` folders exist
- Verify both folders contain files (not empty)
- **REFUSE album generation** if folders are missing or empty
- **Report exactly what is missing**: "Missing screenshots folder", "Empty thumbnails folder", etc.

**Without all four pieces of information and valid folders, the process cannot be executed.**
