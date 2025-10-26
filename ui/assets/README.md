# PRISM UI Assets

This directory contains icons and images for the PRISM application.

## Required Files

### Application Icons
- **icon.png** - Main application icon (256x256 or larger)
- **tray-icon.png** - System tray icon (16x16 or 32x32)

## Creating Icons

### Option 1: Use an Icon Generator
1. Visit [favicon.io](https://favicon.io/) or similar service
2. Create a simple icon with "P" or "PRISM" text
3. Download as PNG
4. Save as `icon.png` and `tray-icon.png`

### Option 2: Use Placeholder
For development, you can use simple colored squares:
- Blue/purple gradient for main icon
- Smaller version for tray icon

### Option 3: Design Custom
Create custom icons in your preferred design tool:
- Main icon: 256x256px, PNG with transparency
- Tray icon: 32x32px, PNG with transparency
- Use glassmorphic style matching the UI theme

## Icon Specifications

### icon.png
- **Size**: 256x256px (minimum)
- **Format**: PNG with transparency
- **Style**: Glassmorphic, modern
- **Colors**: Blue/purple gradient (#6366f1 to #8b5cf6)

### tray-icon.png
- **Size**: 32x32px (or 16x16px)
- **Format**: PNG with transparency
- **Style**: Simple, recognizable at small size
- **Colors**: Match main icon

## Temporary Solution

Until you create proper icons, the application will work but may show default Electron icons.

To add icons later:
1. Create or download icon files
2. Save them in this directory
3. Restart PRISM

## Example Icon Design

```
Main Icon (icon.png):
- Circular glassmorphic orb
- Blue-purple gradient
- Subtle glow effect
- Letter "P" or microphone symbol

Tray Icon (tray-icon.png):
- Simplified version of main icon
- Clear at small sizes
- Monochrome or simple color
```

---

**Note**: The application will function without custom icons, but adding them improves the professional appearance.
