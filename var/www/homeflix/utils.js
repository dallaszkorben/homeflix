// HomeFlix Utility Functions

/**
 * Join path components with separator and clean up duplicate separators
 *
 * @param {Array<string>} parts - Array of path segments to join
 * @param {string} [sep='/'] - Separator character (defaults to '/')
 * @returns {string} Clean path with no duplicate separators
 *
 * @description
 * This function safely joins path segments and removes duplicate separators that
 * can occur when path components have trailing/leading separators.
 *
 * @example
 * // Real HomeFlix usage
 * pathJoin([hit["source_path"], "media", media])
 * // If source_path = "/var/www/homeflix/MEDIA/Movies/"
 * // and media = "American.Beauty-1999.mkv"
 * // Returns: "/var/www/homeflix/MEDIA/Movies/media/American.Beauty-1999.mkv"
 *
 * @behavior
 * 1. Joins array elements with separator: ['a', 'b'] → 'a/b'
 * 2. Creates regex to match 1+ consecutive separators: /\/{1,}/g
 * 3. Replaces all matches with single separator: 'a//b///c' → 'a/b/c'
 */
function pathJoin(parts, sep) {
    var separator = sep || '/';
    var replace = new RegExp(separator + '{1,}', 'g');
    return parts.join(separator).replace(replace, separator);
}

/**
 * Generate hash code for string
 */
String.prototype.hashCode = function() {
    var hash = 0, i, chr;
    if (this.length === 0) return hash;
    for (i = 0; i < this.length; i++) {
        chr = this.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
}

/**
 * String format function - substitute substrings
 * Usage: "hello {0}".format("0", "world")
 */
String.prototype.format = function () {
    var i = 0, args = arguments;
    return this.replace("{" + args[0] + "}", function () {
        return typeof args[1] != 'undefined' ? args[1] : '';
    });
};

/**
 * Get existing cookie value
 */
function getExistingCookie(key) {
    let name = key + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return null;
}

/**
 * Get cookie with default value
 */
function getCookie(key, defaultValue) {
    let value = getExistingCookie(key);
    if(value == null) {
        value = defaultValue;
        document.cookie = key + "=" + value;
    }
    return value;
}

/**
 * Set cookie value
 */
function setCookie(key, value) {
    document.cookie = key + "=" + value;
}

/**
 * Format seconds to HH:MM:SS timecode
 */
function formatSecondsToTimeCode(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * Convert HH:MM:SS timecode to seconds
 */
function formatTimeCodeToSeconds(timeCode) {
    const [hours, minutes, seconds] = timeCode.split(':').map(Number);
    return (hours * 3600) + (minutes * 60) + seconds;
}

/**
 * API utility for making requests
 */
function makeRequest(method, path, data = null) {
    return $.ajax({
        method: method,
        url: `http://${host}${port}${path}`,
        async: false,
        dataType: "json",
        data: data
    });
}

/**
 * CSS utility for setting multiple CSS properties
 */
function setCSSProperties(properties) {
    const root = document.querySelector(':root');
    Object.entries(properties).forEach(([prop, value]) => {
        root.style.setProperty(prop, value);
    });
}

/**
 * Dialog factory for creating consistent dialog configurations
 */
function createDialog(config) {
    return {
        resizable: config.resizable || false,
        height: config.height || "auto",
        width: config.width || 400,
        modal: config.modal !== false,
        title: config.title,
        buttons: config.buttons,
        open: config.open,
        beforeClose: config.beforeClose,
        close: config.close
    };
}

// Cache device detection result
let _deviceTypeCache = null;

function getDeviceType() {
    if (_deviceTypeCache) return _deviceTypeCache;

    const isTV = /TV|SmartTV|SMART-TV|NetCast|webOS.TV/i.test(navigator.userAgent);
    const isMobile = (
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|AppleWebKit|Safari/i.test(navigator.userAgent)
        && 'ontouchstart' in window
        && window.innerWidth <= 1024
    );
    const isDesktop = !isMobile && !isTV;

//    alert("isTV: " + isTV + "\nisMobile: " + isMobile + "\nuserAgent: " + navigator.userAgent + "\ninnerWidth: " + window.innerWidth + "\ninnerHeight: " + window.innerHeight);

    _deviceTypeCache = { isTV, isMobile, isDesktop };
//    _deviceTypeCache = { isTV: true, isMobile: false, isDesktop: false };
    return _deviceTypeCache;
}

// Global device type variables (run once)
const { isTV, isMobile, isDesktop } = getDeviceType();
