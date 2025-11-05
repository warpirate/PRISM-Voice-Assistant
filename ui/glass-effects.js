/**
 * PRISM Glass Effects
 * Modern glassmorphic UI enhancement for PRISM
 */

class GlassEffects {
    constructor() {
        this.initialized = false;
    }

    // Initialize glass effects when DOM is ready
    init() {
        if (this.initialized) return;
        
        // Add SVG filter for glass effects
        this.addGlassFilter();
        
        // Apply glass enhancements to elements
        this.applyGlassEffects();
        
        // Set up listeners for dynamic effects
        this.setupEventListeners();
        
        this.initialized = true;
        console.log('PRISM Glass Effects initialized');
    }

    // Add SVG filter for advanced glass effects
    addGlassFilter() {
        const filterSvg = document.createElement('svg');
        filterSvg.classList.add('glass-filter');
        filterSvg.innerHTML = `
            <defs>
                <filter id="glass-distortion" x="0%" y="0%" width="100%" height="100%" filterUnits="objectBoundingBox">
                    <feTurbulence type="fractalNoise" baseFrequency="0.01 0.01" numOctaves="2" seed="3" result="turbulence" />
                    <feGaussianBlur in="turbulence" stdDeviation="2" result="blur" />
                    <feDisplacementMap in="SourceGraphic" in2="blur" scale="10" xChannelSelector="R" yChannelSelector="G" />
                </filter>
                <filter id="glass-lighting">
                    <feGaussianBlur in="SourceAlpha" stdDeviation="10" result="blur" />
                    <feSpecularLighting in="blur" surfaceScale="5" specularConstant="0.8" specularExponent="20" lighting-color="white" result="specOut">
                        <fePointLight x="-5000" y="-10000" z="20000" />
                    </feSpecularLighting>
                    <feComposite in="specOut" in2="SourceAlpha" operator="in" result="specOut2" />
                    <feComposite in="SourceGraphic" in2="specOut2" operator="arithmetic" k1="0" k2="1" k3="1" k4="0" result="litPaint" />
                </filter>
            </defs>
        `;
        document.body.appendChild(filterSvg);
    }

    // Apply glass enhancements to UI elements
    applyGlassEffects() {
        // Main container
        const appContainer = document.getElementById('app');
        if (appContainer) {
            appContainer.classList.add('glass-container');
        }

        // Enhanced orb
        const orb = document.getElementById('prismOrb');
        if (orb) {
            orb.classList.add('glass-enhanced');
            // Add reflection and glow elements
            const orbInner = orb.querySelector('.orb-inner');
            if (orbInner) {
                // Add reflection layer
                const orbReflection = document.createElement('div');
                orbReflection.className = 'orb-reflection';
                orbInner.appendChild(orbReflection);
                
                // Add glow effect
                const orbGlow = document.createElement('div');
                orbGlow.className = 'orb-glow';
                orbInner.appendChild(orbGlow);
            }
        }

        // Enhanced conversation panel
        const conversationPanel = document.getElementById('conversationPanel');
        if (conversationPanel) {
            conversationPanel.classList.add('glass-enhanced');
            
            // Enhance existing messages
            const messages = conversationPanel.querySelectorAll('.message');
            messages.forEach(message => {
                message.classList.add('glass-enhanced');
            });
        }

        // Enhanced input area
        const inputArea = document.querySelector('.input-area');
        if (inputArea) {
            inputArea.classList.add('glass-enhanced');
            
            // Enhance buttons
            const voiceBtn = document.getElementById('voiceBtn');
            if (voiceBtn) {
                voiceBtn.classList.add('glass-enhanced');
            }
            
            const liveVoiceBtn = document.getElementById('liveVoiceBtn');
            if (liveVoiceBtn) {
                liveVoiceBtn.classList.add('glass-enhanced');
            }
            
            const sendBtn = document.getElementById('sendBtn');
            if (sendBtn) {
                sendBtn.classList.add('glass-btn');
            }
            
            // Enhance text input
            const textInput = document.getElementById('textInput');
            if (textInput) {
                textInput.classList.add('glass-enhanced');
            }
        }

        // Enhanced settings panel
        const settingsPanel = document.getElementById('settingsPanel');
        if (settingsPanel) {
            settingsPanel.classList.add('glass-enhanced');
        }
    }

    // Add glass effect to new messages dynamically
    enhanceNewMessage(messageElement) {
        if (messageElement) {
            messageElement.classList.add('glass-enhanced');
        }
    }

    // Set up observers and event listeners
    setupEventListeners() {
        // Observer for new messages
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            const observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === 1 && node.classList.contains('message')) {
                                this.enhanceNewMessage(node);
                            }
                        });
                    }
                });
            });
            
            observer.observe(messagesContainer, { childList: true });
        }
        
        // Add hover effects for depth
        document.addEventListener('mousemove', (e) => {
            this.handleParallaxEffect(e);
        });
    }

    // Create subtle parallax effect on mousemove
    handleParallaxEffect(e) {
        const mouseX = e.clientX;
        const mouseY = e.clientY;
        
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        // Calculate position ratio
        const ratioX = (mouseX - windowWidth / 2) / (windowWidth / 2);
        const ratioY = (mouseY - windowHeight / 2) / (windowHeight / 2);
        
        // Apply subtle transformation to app container
        const appContainer = document.getElementById('app');
        if (appContainer) {
            appContainer.style.transform = `translate3d(${ratioX * 5}px, ${ratioY * 5}px, 0) rotateX(${-ratioY}deg) rotateY(${ratioX}deg)`;
        }
    }
}

// Create and export the instance
const glassEffects = new GlassEffects();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { glassEffects };
}
