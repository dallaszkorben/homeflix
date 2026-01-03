# Tracklist Modification Guide for HomeFlix Music Albums

## Overview
This guide covers how to modify and add tracklists to existing music album card.yaml files in the HomeFlix media collection. The process involves converting plain text tracklists to standardized HTML table format and ensuring completeness.

## Tracklist Format Standards

### HTML Table Structure
All tracklists must use the standardized HTML table format:

```yaml
storylines:
  [language]: |
    <table class="playlist-table">
        <tr><td>1. </td><td>Track Title</td>                <td>Duration</td></tr>
        <tr><td>2. </td><td>Another Track</td>              <td>Duration</td></tr>
        <tr><td>10.</td><td>Track with longer number</td>   <td>Duration</td></tr>
    </table>
```

### Key Formatting Rules
1. **Track Numbers**: Use format `1. ` for single digits, `10.` for double digits
2. **Alignment**: Track titles should be left-aligned with consistent spacing
3. **Duration Format**: Use M:SS or MM:SS format (3:45, 10:18)
4. **Language Code**: Match the `orig:` field in the album metadata
5. **Class Name**: Always use `class="playlist-table"`

## Language Detection and Matching

### Determining Language
Check the album's `orig:` field to determine the correct language:
- `orig: hu` → Use `storylines: hu:`
- `orig: en` → Use `storylines: en:`
- `orig: de` → Use `storylines: de:`

### Common Language Codes
- `hu` - Hungarian
- `en` - English  
- `de` - German
- `fr` - French
- `it` - Italian

## Track Discovery Process

### Finding Track Information
1. **Check Directory Structure**: Look for numbered track directories (01, 02, 03, etc.)
2. **Examine Media Files**: Find MP3/FLAC/WAV files in track directories
3. **Extract Durations**: Use ffprobe to get accurate track lengths
4. **Parse Track Names**: Extract titles from filenames or directory names

### Duration Extraction Command
```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$file" 2>/dev/null | awk '{printf "%d:%02d", $1/60, $1%60}'
```

### Track Name Cleaning
- Remove file extensions (.mp3, .flac, etc.)
- Replace dots with spaces in track names
- Handle special characters appropriately
- Preserve proper capitalization and punctuation

## Common Issues and Solutions

### Missing Tracks
**Problem**: Tracklist incomplete, missing tracks at the end
**Solution**: 
1. Check all numbered directories in the album folder
2. Look for tracks beyond the expected range (e.g., track 16 when only 15 listed)
3. Verify with directory listing: `ls -1 | grep "^[0-9]" | sort -n`

### Plain Text Format
**Problem**: Existing tracklist in plain text format
**Solution**: Convert to HTML table format while preserving track order and information

**Before (Plain Text)**:
```yaml
storylines:
  hu: |
    1.	Track Title			3:45
    2.	Another Track			4:12
```

**After (HTML Table)**:
```yaml
storylines:
  hu: |
    <table class="playlist-table">
        <tr><td>1. </td><td>Track Title</td>      <td>3:45</td></tr>
        <tr><td>2. </td><td>Another Track</td>    <td>4:12</td></tr>
    </table>
```

### Inconsistent Numbering
**Problem**: Track directories don't follow sequential numbering (01, 03, 04, 05 - missing 02)
**Solution**: 
- Keep original track numbers, don't renumber
- Skip missing numbers in the tracklist
- Maintain the original album's track sequence

## Batch Processing Workflow

### Step 1: Identify Albums Needing Updates
Look for albums with:
- Missing `storylines:` section
- Plain text tracklist format
- Incomplete track listings

### Step 2: Systematic Processing
For each album directory:
1. Check `card.yaml` for current tracklist format
2. Identify the language code from `orig:` field
3. Scan track directories for complete track list
4. Extract track names and durations
5. Convert to HTML table format
6. Update the `card.yaml` file

### Step 3: Verification
After updates:
- Verify all tracks are included
- Check duration format consistency
- Ensure HTML table structure is correct
- Confirm language code matches album metadata

## Example Conversion Scripts

### Track Discovery Script
```bash
for i in {01..20}; do
  dir="/path/to/album/$i"
  if [ -d "$dir" ]; then
    file=$(find "$dir" -name "*.mp3" -o -name "*.flac" -o -name "*.wav" | head -1)
    if [ -n "$file" ]; then
      duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$file" 2>/dev/null | awk '{printf "%d:%02d", $1/60, $1%60}')
      trackname=$(basename "$file" | sed 's/\.[^.]*$//' | sed 's/.*-[0-9][0-9]-//' | sed 's/\./ /g')
      echo "$i. $trackname - $duration"
    fi
  fi
done
```

### HTML Table Generation
Use the discovered track information to generate the HTML table format, ensuring proper alignment and formatting.

## Quality Assurance

### Validation Checklist
- [ ] All track directories checked for completeness
- [ ] Track names properly formatted and readable
- [ ] Durations in correct M:SS or MM:SS format
- [ ] HTML table structure valid
- [ ] Language code matches album metadata
- [ ] No missing tracks at the end of albums
- [ ] Consistent formatting across all albums

### Common Validation Commands
```bash
# Check for numbered directories
ls -1 /path/to/album | grep "^[0-9]" | sort -n

# Verify track count matches storylines
grep -c "<tr><td>" /path/to/album/card.yaml

# Check for missing storylines sections
grep -L "storylines:" /path/to/*/card.yaml
```

## Best Practices

1. **Always backup** card.yaml files before modification
2. **Verify completeness** by checking all track directories
3. **Maintain consistency** in formatting across albums
4. **Preserve original information** - don't modify track names unnecessarily
5. **Use proper language codes** matching the album's original language
6. **Test HTML validity** to ensure proper table structure
7. **Document any anomalies** found during processing

## Integration with HomeFlix

The updated tracklists integrate with the HomeFlix system by:
- Providing structured data for web interface display
- Enabling proper track navigation and selection
- Supporting multi-language content presentation
- Maintaining consistency with the overall data architecture

This standardized approach ensures all music albums in the HomeFlix collection have complete, properly formatted tracklists that enhance the user experience and maintain data integrity.
