# Audio Poster Aspect Ratio Solution

## Problem
HTML5 video player poster images lose aspect ratio on LG OLED TVs during audio playback due to `.fake-fullscreen` CSS forcing `width: 100vw` and `height: 100vh`.

## Solution
Separate poster image from video element using CSS background-image:

### JavaScript (container.js)
```javascript
if (medium_dict["media_type"] === "audio") {
    player.addEventListener('loadeddata', function() {
        document.documentElement.style.setProperty('--audio-poster-url', `url(${this.poster})`);
        this.classList.add('audio-player');
        this.poster = ''; // Remove poster from video element
    });
}
```

### CSS (stylesheet.css)
```css
.fake-fullscreen.audio-player {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-image: var(--audio-poster-url) !important;
}
```

## Key Insight
Don't fight video element behavior - bypass it by using container background for poster image with proper aspect ratio preservation.