/**
 * Matrix Display Component
 * Retro dot-matrix display with circular cells and smooth animations
 * Adapted for PRISM state visualization
 */

class Matrix {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            rows: options.rows || 7,
            cols: options.cols || 7,
            size: options.size || 10,
            gap: options.gap || 2,
            palette: options.palette || {
                on: 'rgba(138, 180, 248, 1)',  // PRISM blue
                off: 'rgba(138, 180, 248, 0.1)'
            },
            brightness: options.brightness || 1,
            fps: options.fps || 20,
            autoplay: options.autoplay !== undefined ? options.autoplay : true,
            loop: options.loop !== undefined ? options.loop : true,
            mode: options.mode || 'default',
            ...options
        };

        this.currentFrame = 0;
        this.frames = [];
        this.pattern = null;
        this.animationId = null;
        this.lastFrameTime = 0;
        this.isPlaying = false;
        this.levels = [];

        this.init();
    }

    init() {
        this.createSVG();
        if (this.options.autoplay && this.frames.length > 0) {
            this.play();
        }
    }

    createSVG() {
        const { rows, cols, size, gap } = this.options;
        const width = cols * (size + gap) - gap;
        const height = rows * (size + gap) - gap;

        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('width', width);
        this.svg.setAttribute('height', height);
        this.svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        this.svg.setAttribute('role', 'img');
        this.svg.setAttribute('aria-label', this.options.ariaLabel || 'Matrix display');
        this.svg.style.display = 'block';

        // Create cells
        this.cells = [];
        for (let row = 0; row < rows; row++) {
            this.cells[row] = [];
            for (let col = 0; col < cols; col++) {
                const cx = col * (size + gap) + size / 2;
                const cy = row * (size + gap) + size / 2;
                const r = size / 2;

                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', cx);
                circle.setAttribute('cy', cy);
                circle.setAttribute('r', r);
                circle.setAttribute('fill', this.options.palette.off);
                circle.style.transition = 'fill 0.1s ease-out';

                this.svg.appendChild(circle);
                this.cells[row][col] = circle;
            }
        }

        this.container.innerHTML = '';
        this.container.appendChild(this.svg);
    }

    setPattern(pattern) {
        this.pattern = pattern;
        this.frames = [];
        this.stop();
        this.render();
    }

    setFrames(frames) {
        this.frames = frames;
        this.pattern = null;
        this.currentFrame = 0;
        if (this.options.autoplay) {
            this.play();
        }
    }

    setLevels(levels) {
        this.levels = levels;
        if (this.options.mode === 'vu') {
            this.renderVU();
        }
    }

    render() {
        const data = this.pattern || (this.frames[this.currentFrame] || []);
        const { rows, cols, brightness, palette } = this.options;

        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                const value = (data[row] && data[row][col]) || 0;
                const adjustedValue = Math.max(0, Math.min(1, value * brightness));
                const color = this.interpolateColor(palette.off, palette.on, adjustedValue);
                this.cells[row][col].setAttribute('fill', color);
            }
        }
    }

    renderVU() {
        const { rows, cols } = this.options;
        
        for (let col = 0; col < cols; col++) {
            const level = this.levels[col] || 0;
            const litRows = Math.round(level * rows);
            
            for (let row = 0; row < rows; row++) {
                const isLit = (rows - row) <= litRows;
                const value = isLit ? 1 : 0;
                const color = value > 0 ? this.options.palette.on : this.options.palette.off;
                this.cells[row][col].setAttribute('fill', color);
            }
        }
    }

    interpolateColor(color1, color2, factor) {
        // Parse RGBA
        const parseRGBA = (color) => {
            const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
            if (match) {
                return {
                    r: parseInt(match[1]),
                    g: parseInt(match[2]),
                    b: parseInt(match[3]),
                    a: match[4] ? parseFloat(match[4]) : 1
                };
            }
            return { r: 0, g: 0, b: 0, a: 1 };
        };

        const c1 = parseRGBA(color1);
        const c2 = parseRGBA(color2);

        const r = Math.round(c1.r + (c2.r - c1.r) * factor);
        const g = Math.round(c1.g + (c2.g - c1.g) * factor);
        const b = Math.round(c1.b + (c2.b - c1.b) * factor);
        const a = c1.a + (c2.a - c1.a) * factor;

        return `rgba(${r}, ${g}, ${b}, ${a})`;
    }

    play() {
        if (this.isPlaying || this.frames.length === 0) return;
        
        this.isPlaying = true;
        this.lastFrameTime = performance.now();
        this.animate();
    }

    stop() {
        this.isPlaying = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    animate() {
        if (!this.isPlaying) return;

        const now = performance.now();
        const elapsed = now - this.lastFrameTime;
        const frameInterval = 1000 / this.options.fps;

        if (elapsed >= frameInterval) {
            this.render();
            
            if (this.options.onFrame) {
                this.options.onFrame(this.currentFrame);
            }

            this.currentFrame++;
            if (this.currentFrame >= this.frames.length) {
                if (this.options.loop) {
                    this.currentFrame = 0;
                } else {
                    this.stop();
                    return;
                }
            }

            this.lastFrameTime = now - (elapsed % frameInterval);
        }

        this.animationId = requestAnimationFrame(() => this.animate());
    }

    destroy() {
        this.stop();
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// ============================================================================
// Animation Presets for PRISM States
// ============================================================================

const MatrixPresets = {
    // Idle state - gentle pulse
    idle: {
        frames: generatePulse(7, 7, 24, 0.3),
        fps: 12
    },

    // Startup/Initializing - expanding rings
    startup: {
        frames: generateStartup(7, 7, 20),
        fps: 20
    },

    // Listening - wave pattern
    listening: {
        frames: generateWave(7, 7, 24),
        fps: 20
    },

    // Processing - spinner
    processing: {
        frames: generateSpinner(7, 7, 12),
        fps: 12
    },

    // Responding - outward pulse
    responding: {
        frames: generateResponding(7, 7, 16),
        fps: 16
    },

    // Executing - progress bar
    executing: {
        frames: generateExecuting(7, 7, 20),
        fps: 15
    },

    // Error - warning flash
    error: {
        frames: generateError(7, 7, 8),
        fps: 4
    },

    // Shutdown - fade out
    shutdown: {
        frames: generateShutdown(7, 7, 20),
        fps: 15
    }
};

// ============================================================================
// Animation Generators
// ============================================================================

function generatePulse(rows, cols, frameCount, intensity = 0.5) {
    const frames = [];
    const centerX = (cols - 1) / 2;
    const centerY = (rows - 1) / 2;
    const maxDist = Math.sqrt(centerX * centerX + centerY * centerY);

    for (let f = 0; f < frameCount; f++) {
        const frame = [];
        const phase = (f / frameCount) * Math.PI * 2;
        const pulse = (Math.sin(phase) + 1) / 2 * intensity;

        for (let row = 0; row < rows; row++) {
            frame[row] = [];
            for (let col = 0; col < cols; col++) {
                const dx = col - centerX;
                const dy = row - centerY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const normalizedDist = dist / maxDist;
                const value = pulse * (1 - normalizedDist * 0.5);
                frame[row][col] = Math.max(0, Math.min(1, value));
            }
        }
        frames.push(frame);
    }
    return frames;
}

function generateStartup(rows, cols, frameCount) {
    const frames = [];
    const centerX = (cols - 1) / 2;
    const centerY = (rows - 1) / 2;
    const maxDist = Math.sqrt(centerX * centerX + centerY * centerY);

    for (let f = 0; f < frameCount; f++) {
        const frame = [];
        const progress = f / frameCount;
        const radius = progress * maxDist * 1.5;

        for (let row = 0; row < rows; row++) {
            frame[row] = [];
            for (let col = 0; col < cols; col++) {
                const dx = col - centerX;
                const dy = row - centerY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                const ringDist = Math.abs(dist - radius);
                const value = Math.max(0, 1 - ringDist / 2);
                frame[row][col] = value;
            }
        }
        frames.push(frame);
    }
    return frames;
}

function generateWave(rows, cols, frameCount) {
    const frames = [];
    
    for (let f = 0; f < frameCount; f++) {
        const frame = [];
        const phase = (f / frameCount) * Math.PI * 2;

        for (let row = 0; row < rows; row++) {
            frame[row] = [];
            for (let col = 0; col < cols; col++) {
                const wave1 = Math.sin(col * 0.5 + phase) * 0.5 + 0.5;
                const wave2 = Math.sin(row * 0.5 + phase * 1.3) * 0.5 + 0.5;
                const value = (wave1 + wave2) / 2;
                frame[row][col] = value;
            }
        }
        frames.push(frame);
    }
    return frames;
}

function generateSpinner(rows, cols, frameCount) {
    const frames = [];
    const centerX = (cols - 1) / 2;
    const centerY = (rows - 1) / 2;

    for (let f = 0; f < frameCount; f++) {
        const frame = [];
        const angle = (f / frameCount) * Math.PI * 2;

        for (let row = 0; row < rows; row++) {
            frame[row] = [];
            for (let col = 0; col < cols; col++) {
                const dx = col - centerX;
                const dy = row - centerY;
                const cellAngle = Math.atan2(dy, dx);
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                const angleDiff = Math.abs(((cellAngle - angle + Math.PI) % (Math.PI * 2)) - Math.PI);
                const value = dist > 0.5 && dist < 3.5 ? Math.max(0, 1 - angleDiff / Math.PI) : 0;
                frame[row][col] = value;
            }
        }
        frames.push(frame);
    }
    return frames;
}

function generateResponding(rows, cols, frameCount) {
    const frames = [];
    const centerX = (cols - 1) / 2;
    const centerY = (rows - 1) / 2;
    const maxDist = Math.sqrt(centerX * centerX + centerY * centerY);

    for (let f = 0; f < frameCount; f++) {
        const frame = [];
        const progress = f / frameCount;
        const radius = progress * maxDist * 2;

        for (let row = 0; row < rows; row++) {
            frame[row] = [];
            for (let col = 0; col < cols; col++) {
                const dx = col - centerX;
                const dy = row - centerY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                const value = Math.max(0, 1 - Math.abs(dist - radius) / 2);
                frame[row][col] = value;
            }
        }
        frames.push(frame);
    }
    return frames;
}

function generateExecuting(rows, cols, frameCount) {
    const frames = [];
    
    for (let f = 0; f < frameCount; f++) {
        const frame = [];
        const progress = f / frameCount;
        const filledCols = Math.floor(progress * cols);

        for (let row = 0; row < rows; row++) {
            frame[row] = [];
            for (let col = 0; col < cols; col++) {
                const value = col < filledCols ? 1 : (col === filledCols ? 0.5 : 0);
                frame[row][col] = value;
            }
        }
        frames.push(frame);
    }
    return frames;
}

function generateError(rows, cols, frameCount) {
    const frames = [];
    
    for (let f = 0; f < frameCount; f++) {
        const frame = [];
        const isOn = f % 2 === 0;

        for (let row = 0; row < rows; row++) {
            frame[row] = [];
            for (let col = 0; col < cols; col++) {
                // X pattern
                const isX = (row === col) || (row === cols - col - 1);
                const value = isX && isOn ? 1 : 0;
                frame[row][col] = value;
            }
        }
        frames.push(frame);
    }
    return frames;
}

function generateShutdown(rows, cols, frameCount) {
    const frames = [];
    const centerX = (cols - 1) / 2;
    const centerY = (rows - 1) / 2;
    const maxDist = Math.sqrt(centerX * centerX + centerY * centerY);

    for (let f = 0; f < frameCount; f++) {
        const frame = [];
        const progress = 1 - (f / frameCount);

        for (let row = 0; row < rows; row++) {
            frame[row] = [];
            for (let col = 0; col < cols; col++) {
                const dx = col - centerX;
                const dy = row - centerY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const normalizedDist = dist / maxDist;
                
                const value = progress * (1 - normalizedDist);
                frame[row][col] = Math.max(0, value);
            }
        }
        frames.push(frame);
    }
    return frames;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Matrix, MatrixPresets };
}
