// HomeFlix Utility Functions

/**
 * Join path components with separator
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