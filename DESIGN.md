---
version: alpha
name: Mintly Onboarding System
description: Paperclip/SimCity-inspired mobile onboarding for natural-language financial agents.
colors:
  background: "#F4F1DC"
  surface: "#FFFBE8"
  surfaceAlt: "#DDF4D4"
  text: "#253326"
  muted: "#647160"
  border: "#263428"
  accent: "#1D7C5A"
  accentStrong: "#155B43"
  accentSoft: "#CFEFC4"
  success: "#247251"
typography:
  display:
    fontFamily: "ui-rounded, SF Pro Rounded, Avenir Next, system-ui, sans-serif"
    fontSize: "34px"
    fontWeight: 850
    lineHeight: 0.98
  body:
    fontFamily: "ui-rounded, SF Pro Rounded, Avenir Next, system-ui, sans-serif"
    fontSize: "15.5px"
    fontWeight: 500
    lineHeight: 1.52
rounded:
  sm: "16px"
  md: "22px"
  lg: "28px"
  device: "50px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "20px"
  lg: "24px"
  xl: "34px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "18px"
    padding: "0 20px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.accentStrong}"
    rounded: "18px"
    padding: "0 20px"
  phone-card:
    backgroundColor: "rgba(255,255,255,.72)"
    rounded: "{rounded.lg}"
    padding: "16px"
---

## Overview
Mintly now blends soft mint onboarding with a Paperclip/SimCity management feel: users guide small human-like financial agents using natural-language commands, with lightweight code-style traces that explain what the system will do.

## Colors
Use parchment-mint neutrals, visible grid lines, and deep ink borders. The accent green is reserved for primary action, active progress, enabled permissions, selected commands, and small simulated city elements.

## Typography
Use rounded system typography with compact display headings and readable 15.5px body copy. Keep captions at 12.5px or larger.

## Layout
Each phone screen follows status area, topbar with progress, content, and bottom actions. Maintain 24px side padding and 52px primary buttons.

## Elevation & Depth
Cards use paper surfaces with strong ink borders and offset shadows, closer to simulation controls than glassy finance UI. Code traces use dark ink panels with mint text.

## Shapes
Keep phone frames soft, but inner controls are more squared and tactile: 12px command cards, 10px terminal chips, 12px buttons, and 44–50px device frames.

## Components
- Progress indicator: three dots; completed/current dots expand and use accent green.
- Natural-language command card: human sentence first, code-style rule below.
- Permission row: two-line agent label with accessible switch state.
- Goal row: command sentence plus monospaced system translation.
- Success hint: compact status block explaining the editable human/code pairing.

## Do's and Don'ts
Do use realistic financial habit copy, natural-language commands, small simulated people/district cues, generous touch targets, and accessible contrast. Do not use external icons, bitmap images, fake links, or color-only state indicators.
