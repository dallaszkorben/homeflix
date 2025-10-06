// Utility functions to get thumbnail container information

/**
 * Get the number of thumbnails in a specific container
 * @param {number} containerIndex - The index of the container (0-based)
 * @returns {number} Number of thumbnails in the container
 */
function getThumbnailCount(containerIndex) {
    const domThumbnails = $('#container-' + containerIndex + ' .thumbnail');
    return domThumbnails.length;
}

/**
 * Get the index of the currently focused (red border) thumbnail in a container
 * @param {number} containerIndex - The index of the container (0-based)
 * @returns {number} Index of the focused thumbnail (0-based), or -1 if none found
 */
function getFocusedThumbnailIndex(containerIndex) {
    const domThumbnails = $('#container-' + containerIndex + ' .thumbnail');
    
    for (let i = 0; i < domThumbnails.length; i++) {
        const borderColor = domThumbnails.eq(i).css('border-color');
        // Check if border color matches the focus color (red)
        if (borderColor === 'rgb(200, 0, 0)' || borderColor === thumbnail_border_color) {
            return i;
        }
    }
    return -1; // No focused thumbnail found
}

/**
 * Get thumbnail info for a specific container using existing controller
 * @param {ThumbnailController} oThumbnailController - The thumbnail controller instance
 * @param {number} containerIndex - The index of the container (0-based)
 * @returns {Object} Object with count and focusedIndex
 */
function getThumbnailInfo(oThumbnailController, containerIndex) {
    const scrollSection = oThumbnailController.getScrollSection();
    
    // Get count from DOM
    const count = getThumbnailCount(containerIndex);
    
    // Get focused index from controller's internal state
    const focusedIndex = scrollSection.focusedThumbnailList[containerIndex] || 0;
    
    return {
        count: count,
        focusedIndex: focusedIndex,
        focusedPosition: focusedIndex + 1 // 1-based position for display
    };
}

/**
 * Get info for the currently active container
 * @param {ThumbnailController} oThumbnailController - The thumbnail controller instance
 * @returns {Object} Object with containerIndex, count, focusedIndex, and focusedPosition
 */
function getCurrentContainerInfo(oThumbnailController) {
    const scrollSection = oThumbnailController.getScrollSection();
    const containerIndex = scrollSection.currentContainerIndex;
    const info = getThumbnailInfo(oThumbnailController, containerIndex);
    
    return {
        containerIndex: containerIndex,
        ...info
    };
}

/**
 * Get the index of the first fully visible thumbnail in a container
 * @param {number} containerIndex - The index of the container (0-based)
 * @returns {number} Index of first fully visible thumbnail, or 0 if none found
 */
function getFirstVisibleThumbnailIndex(containerIndex) {
    const domContainer = $('#container-' + containerIndex);
    const domThumbnails = domContainer.find('.thumbnail');
    
    for (let i = 0; i < domThumbnails.length; i++) {
        const thumbnail = domThumbnails.eq(i);
        const thumbnailLeft = thumbnail.position().left;
        const thumbnailWidth = thumbnail.outerWidth(true);
        
        if (thumbnailLeft >= 0 && thumbnailLeft + thumbnailWidth <= domContainer.width()) {
            return i;
        }
    }
    return 0;
}

/**
 * Get the index of the last fully visible thumbnail in a container
 * @param {number} containerIndex - The index of the container (0-based)
 * @returns {number} Index of last fully visible thumbnail, or last thumbnail index if none found
 */
function getLastVisibleThumbnailIndex(containerIndex) {
    const domContainer = $('#container-' + containerIndex);
    const domThumbnails = domContainer.find('.thumbnail');
    const containerWidth = domContainer.width();
    
    for (let i = domThumbnails.length - 1; i >= 0; i--) {
        const thumbnail = domThumbnails.eq(i);
        const thumbnailLeft = thumbnail.position().left;
        const thumbnailWidth = thumbnail.outerWidth(true);
        
        if (thumbnailLeft >= 0 && thumbnailLeft + thumbnailWidth <= containerWidth) {
            return i;
        }
    }
    return domThumbnails.length - 1;
}