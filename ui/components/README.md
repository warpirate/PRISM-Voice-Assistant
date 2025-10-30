# PRISM Matrix Display Component

## Overview

The Matrix component is a retro dot-matrix display with circular cells and smooth animations, specifically designed for PRISM's state visualization system.

## Features

- **State-based animations**: Unique animations for each PRISM state
- **SVG rendering**: Crisp, scalable graphics
- **Smooth transitions**: Optimized frame-based animations
- **Customizable**: Configurable colors, sizes, and speeds
- **Accessible**: ARIA labels and semantic markup

## PRISM State Animations

### 1. **Startup** (1.5 seconds)
- Expanding ring animation
- Plays once when PRISM initializes
- Transitions to idle state automatically

### 2. **Idle**
- Gentle pulsing pattern
- Low intensity (30% brightness variation)
- Continuous loop at 12 FPS

### 3. **Listening**
- Wave pattern animation
- Indicates active voice input
- Smooth sine wave at 20 FPS

### 4. **Processing**
- Rotating spinner
- Shows AI is thinking
- 12 FPS rotation

### 5. **Responding**
- Outward pulse effect
- Indicates assistant is speaking
- 16 FPS smooth expansion

### 6. **Executing**
- Progress bar animation
- Shows action execution
- Left-to-right fill at 15 FPS

### 7. **Error**
- Warning flash (X pattern)
- Rapid blinking at 4 FPS
- High visibility alert

### 8. **Shutdown**
- Fade out from center
- Plays once during shutdown
- Smooth 15 FPS fade

## Usage

### Basic Initialization

```javascript
const matrixInstance = new Matrix(containerElement, {
    rows: 7,
    cols: 7,
    size: 12,
    gap: 3,
    palette: {
        on: 'rgba(138, 180, 248, 1)',
        off: 'rgba(138, 180, 248, 0.08)'
    }
});
```

### Changing States

```javascript
// Use preset animations
setMatrixState('listening');
setMatrixState('processing');
setMatrixState('error');
```

### Custom Patterns

```javascript
// Static pattern
const customPattern = [
    [1, 0, 1, 0, 1, 0, 1],
    [0, 1, 0, 1, 0, 1, 0],
    // ... 7 rows total
];
matrixInstance.setPattern(customPattern);

// Custom animation frames
const customFrames = [frame1, frame2, frame3];
matrixInstance.setFrames(customFrames);
matrixInstance.options.fps = 20;
matrixInstance.play();
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `rows` | number | 7 | Number of rows in matrix |
| `cols` | number | 7 | Number of columns in matrix |
| `size` | number | 10 | Cell diameter in pixels |
| `gap` | number | 2 | Gap between cells in pixels |
| `palette.on` | string | - | Color for active cells (CSS color) |
| `palette.off` | string | - | Color for inactive cells (CSS color) |
| `brightness` | number | 1 | Global brightness multiplier (0-1) |
| `fps` | number | 20 | Animation frame rate |
| `autoplay` | boolean | true | Start animation automatically |
| `loop` | boolean | true | Loop animation continuously |
| `ariaLabel` | string | - | Accessibility label |
| `onFrame` | function | - | Callback on frame change |

## API Methods

### `setPattern(pattern)`
Display a static pattern (2D array of brightness values 0-1).

### `setFrames(frames)`
Set animation frames and reset to first frame.

### `setLevels(levels)` 
Update VU meter levels (array of 0-1 values per column).

### `play()`
Start or resume animation.

### `stop()`
Stop animation and clear animation frame.

### `render()`
Manually render current frame.

### `destroy()`
Clean up and remove from DOM.

## Integration with PRISM

The Matrix component is automatically initialized in `renderer.js`:

1. **Startup**: Shows expanding ring animation for 1.5 seconds
2. **State changes**: Automatically updates via `setState()` function
3. **Backend sync**: Responds to WebSocket state messages from Python backend

## Performance

- Optimized for 7×7 grids (49 cells)
- Uses `requestAnimationFrame` for smooth 60fps rendering
- Cell updates via SVG attribute changes (GPU accelerated)
- Minimal CPU usage during animations
- Proper cleanup on component destruction

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Electron 12+ (PRISM uses Electron 28+)

## Customization

### Changing Colors

Edit the palette in `renderer.js`:

```javascript
palette: {
    on: 'rgba(138, 180, 248, 1)',   // Active cell color
    off: 'rgba(138, 180, 248, 0.08)' // Inactive cell color
}
```

### Adjusting Size

Modify in `setupMatrix()`:

```javascript
size: 12,  // Cell diameter
gap: 3,    // Space between cells
```

### Custom Animations

Add new presets to `MatrixPresets` object in `matrix.js`:

```javascript
MatrixPresets.myAnimation = {
    frames: generateMyAnimation(7, 7, 20),
    fps: 15
};
```

## Troubleshooting

### Matrix not appearing
- Check console for "Matrix display element not found"
- Verify `matrix.js` is loaded before `renderer.js`
- Ensure `#matrixDisplay` element exists in HTML

### Animation stuttering
- Reduce FPS in preset configuration
- Check system performance
- Verify no blocking operations in main thread

### Wrong colors
- Check palette configuration in `setupMatrix()`
- Verify CSS color format (rgba recommended)
- Check brightness multiplier setting

## Future Enhancements

- [ ] Audio-reactive mode (sync with microphone input)
- [ ] Custom pattern editor
- [ ] Transition effects between states
- [ ] 3D depth effects
- [ ] Particle effects overlay
- [ ] User-configurable animations via settings panel
