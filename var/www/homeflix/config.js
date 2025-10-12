// HomeFlix Frontend Configuration

const HomeFlix = {
    // Touch Gesture Configuration
    TOUCH: {
        SWIPE_RANGES: [
            { min: 50,  max: 79,  commands: 1 },  // Short swipe
            { min: 80,  max: 159, commands: 2 },  // Medium swipe
            { min: 160, max: 239, commands: 3 },  // Long swipe
            { min: 240, max: 319, commands: 4 },  // Very long swipe
            { min: 320, max: 999, commands: 5 }   // Extra long swipe
        ],
        MIN_SWIPE_DISTANCE: 50
    }
};