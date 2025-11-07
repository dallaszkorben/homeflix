# HomeFlix Data Architecture & Synchronization

## Overview
HomeFlix uses a complex multi-layered data synchronization system where four critical data structures must remain perfectly aligned at all times. Any operation that modifies thumbnail order requires careful synchronization across all layers.

## Critical Data Structures

### 1. DOM Elements (Visual Layer)
- **Location**: Browser DOM tree under `#container-{index}`
- **Purpose**: Visual representation and user interaction
- **Structure**: Sequential `.thumbnail` elements with IDs like `container-0-thumbnail-2`
- **Key Properties**:
  - Position determines visual order
  - IDs encode container and position information
  - Click event listeners attached to each element
  - CSS styling for focus (red borders)

### 2. Data Array (thumbnailList)
- **Location**: `thumbnailContainerList[containerIndex].thumbnailList[]`
- **Purpose**: Core data storage for all thumbnail information
- **Structure**: Array of `Thumbnail` objects
- **Key Properties**:
  - Contains media metadata (title, image, progress, etc.)
  - Position must match DOM element position
  - Used by `getThumbnail(index)` for data retrieval

### 3. Focus Tracking (focusedThumbnailList)
- **Location**: `focusedThumbnailList[containerIndex]`
- **Purpose**: Tracks which thumbnail has focus (red border)
- **Structure**: Array of integers (indices, not objects)
- **Key Properties**:
  - Stores thumbnail position indices
  - Used for applying red border styling
  - Must be updated when thumbnails move positions

### 4. Continuous Play Arrays
- **Location**: `thumbnail.function_for_selection.continuous`
- **Purpose**: Sequential media playback from any starting point
- **Structure**: Each thumbnail has its own array containing all subsequent media
- **Key Properties**:
  - Each array starts from thumbnail's position to end
  - Contains full media objects with id, source_path, title_orig, etc.
  - Must be rebuilt when order changes

## Data Flow Architecture

### User Click → Media Playback
1. User clicks thumbnail DOM element
2. Click handler extracts container and thumbnail indices from DOM ID
3. `getThumbnail(index)` retrieves data from thumbnailList array
4. `getFunctionForSelection()` returns continuous play array
5. Media controller uses continuous array for sequential playback

### Focus Management
1. `focusedThumbnailList[containerIndex]` stores current focus index
2. `focus()` method applies red border to DOM element at that index
3. `showDetails()` retrieves thumbnail data using focus index
4. Description panel updates with focused thumbnail's metadata

## Synchronization Requirements

### During Randomization
All four data structures must be updated simultaneously:

1. **DOM Reordering**: Physical rearrangement of visual elements
2. **Data Array Sync**: Reorder thumbnailList to match new DOM positions
3. **Focus Index Update**: Adjust focus tracking to follow moved thumbnail
4. **ID Updates**: Update DOM IDs to reflect new positions
5. **Event Listener Restoration**: Re-attach click handlers lost during DOM manipulation
6. **Continuous Array Rebuild**: Regenerate sequential play arrays for new order

### Critical Synchronization Points
- **Position Consistency**: DOM position = data array position = ID suffix
- **Event Handler Integrity**: Click listeners must survive DOM manipulation
- **Focus Continuity**: Red border must follow the actual focused thumbnail
- **Playback Accuracy**: Continuous arrays must reflect actual visual order

## Common Pitfalls

### Lost Event Listeners
- jQuery's `empty()` and `append()` remove event listeners
- Must re-attach click handlers after DOM manipulation
- Use element references, not selectors, for event binding

### Index Misalignment
- DOM position and data array position must always match
- Focus indices become invalid after reordering
- Continuous arrays become incorrect if not rebuilt

### ID Encoding Issues
- Thumbnail IDs encode position information: `container-{container}-thumbnail-{position}`
- Click handlers parse IDs to determine which thumbnail was clicked
- IDs must be updated to reflect new positions after shuffling

## Implementation Patterns

### Safe Randomization Pattern
```javascript
// 1. Generate shuffle order
let indices = Fisher-Yates-shuffle(originalIndices);

// 2. Sync data array
reorderDataArray(indices);

// 3. Sync DOM elements  
reorderDOMElements(indices);

// 4. Update IDs and restore events
updateIDsAndEvents();

// 5. Update focus tracking
updateFocusTracking(indices);

// 6. Rebuild continuous arrays
rebuildContinuousArrays();
```

### Focus Preservation Pattern
```javascript
// Before shuffle: remember which thumbnail is focused
let focusedThumbnail = getCurrentFocusedThumbnail();

// After shuffle: find where that thumbnail moved
let newPosition = findThumbnailNewPosition(focusedThumbnail, indices);
focusedThumbnailList[containerIndex] = newPosition;
```

## Data Structure Dependencies

```
User Click
    ↓
DOM ID Parsing → Container Index + Thumbnail Index
    ↓
Data Retrieval → thumbnailList[containerIndex][thumbnailIndex]
    ↓
Focus Update → focusedThumbnailList[containerIndex] = thumbnailIndex
    ↓
Continuous Play → thumbnail.function_for_selection.continuous
    ↓
Media Playback
```

This architecture ensures seamless user experience while maintaining data integrity across all application layers.