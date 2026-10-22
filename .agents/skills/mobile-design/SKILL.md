---
name: mobile-design
description: Mobile-first design thinking and decision-making for responsive web and mobile apps. Enforces touch-first mechanics (min 44x44px touch targets), 8-point grid, thumb-zone ergonomics, bottom-sheet patterns, and battery/performance optimization.
category: design
version: 1.0.0
---

# Mobile Design System Skill

> **Philosophy:** Touch-first. Ergonomic thumb-zone. Platform-respectful. Battery & performance conscious.
> **Core Principle:** Mobile is NOT a shrunken desktop. Design for mobile constraints first.

## Core Rules & Ergonomics

### 1. Touch-First Mechanics (Fitts's Law)
* **Minimum Touch Target**: 44px × 44px for iOS HIG, 48px × 48px for Android Material Design.
* **Touch Spacing**: At least 8px to 12px gap between adjacent interactive targets to prevent accidental mis-taps.
* **Thumb Zone Architecture**:
  * Place primary actions, search/filter controls, and sticky navigation in the bottom third of the viewport.
  * Avoid placing mission-critical single-action buttons in the top corners without bottom alternatives.

### 2. Spacing & Visual Hierarchy (8-Point Grid)
* Base spacing units on 4px and 8px (8, 12, 16, 20, 24, 32, 40, 48px).
* **60/30/10 Color Distribution**:
  * 60% neutral background surface.
  * 30% readable structural text and cards.
  * 10% high-contrast accent/action color.
* **Typography Floor**: Minimum 12px for micro-metadata, 14px for body text, 16px for input fields (to prevent iOS auto-zoom on focus).

### 3. Native Mobile Interaction Patterns
* **Bottom Sheets & Drawers**: On screens < 768px, convert dropdowns and modal dialogs into native-feeling slide-up bottom sheets with safe-area insets (`env(safe-area-inset-bottom)`).
* **Direct Navigation**: Sticky bottom navigation bars must provide fast one-tap switching between core tabs (Browse, Filter, AI Chat, Saved, Profile).
* **Instant Feedback**: Every tap must provide instant visual feedback (active states, opacity changes, spring curves).

### 4. Performance & Memory
* **Progressive Batching**: Render lists in batches (20–25 items) rather than mounting 10,000 DOM nodes simultaneously.
* **Hardware Acceleration**: Use CSS `transform` and `opacity` for animations; avoid animating layout properties like `height`, `top`, or `margin`.
