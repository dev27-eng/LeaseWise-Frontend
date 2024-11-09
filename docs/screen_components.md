# Screen Components Documentation

## Welcome Screen
Located in `leasecheck/templates/welcome_screen.html`

### Components

1. **Logo Text**
   - Component: `.logo-text`
   - Purpose: Main branding element displaying "LeaseCheck"
   - Styling: Large, bold text with custom letter spacing
   - Responsive behavior: Scales down on mobile devices

2. **Logo Image**
   - Component: `.logo-wrapper` and `.logo-image`
   - Purpose: Visual branding with company logo
   - Performance optimizations:
     - Eager loading for critical above-fold content
     - Async decoding for better performance
     - Hardware-accelerated transforms
   - Accessibility: Includes proper alt text

3. **Verification Text**
   - Component: `.verify-text`
   - Purpose: Displays the main value proposition
   - Content: "Verify legal compliance easily"
   - Styling: Clean, readable font with proper contrast

4. **Start Review Button**
   - Component: `.start-review-btn`
   - Purpose: Primary CTA for starting the lease review process
   - Features:
     - High contrast green background
     - Large touch target for mobile
     - Hover state feedback
     - Rounded corners for modern look

## Onboarding Screen
Located in `leasecheck/templates/onboarding_screen.html`

### Components

1. **Welcome Header**
   - Component: `.welcome-header`
   - Purpose: Section header with green background
   - Content: Welcomes users to the platform

2. **Main Content Section**
   - Component: `.welcome-text`
   - Subcomponents:
     - `.main-title`: LeaseCheck branding
     - `.lead`: Legal compliance message
     - `.tagline`: Confidence-building message
     - `.description`: Platform value proposition

3. **Key Features Section**
   - Component: `.key-features`
   - Purpose: Highlights main platform capabilities
   - Features listed:
     - Legal Compliance
     - Risk Identification
     - User-Friendly Interface
     - Empowerment
     - Peace of Mind

4. **Call to Action Section**
   - Component: `.cta-section`
   - Purpose: Drives users to plan selection
   - Elements:
     - Ready message
     - Choose plan button

### Performance Optimizations

1. **Resource Loading**
   - Critical CSS preloading
   - Font display optimization
   - Image lazy loading where appropriate

2. **Rendering Optimizations**
   - Hardware acceleration for animations
   - Content containment for better paint performance
   - Will-change hints for animated elements

### Responsive Design

Both screens implement a mobile-first approach with:
- Fluid typography
- Flexible layouts
- Touch-friendly interactions
- Appropriate spacing adjustments
- Optimized image sizes
