# 🎨 PRobot Frontend Presentation & Simulator Guide

This directory houses the React, Vite, and Tailwind CSS single-page presentation website and simulator.

---

## 1. Frontend Overview
The frontend presents a high-converting landing page built around the design aesthetics of the cosmic Raze theme:
- **Atmosphere**: Slate backdrops, glowing nebula halos, andOutfit typography.
- **State Routing**: Switches between Page 1 (Product Showcase) and Page 2 (Maintainer About & Architecture) using a clean floating glassmorphic navbar pill.
- **Interactive Simulator**: Features an interactive control deck where developers can trigger simulated GitHub webhook payloads and observe step-by-step console outputs and visual comment updates.

---

## 2. Tech Stack
- **Framework**: React 18
- **Build Server**: Vite 5
- **Styling**: Tailwind CSS (v3) + PostCSS
- **Typography**: Google Fonts "Outfit"

---

## 3. Project Structure

```
frontend/
├── src/
│   ├── assets/           # Workflow graphic, React & Vite SVGs
│   ├── App.jsx           # Master presentation application & state router
│   ├── index.css         # Tailwind imports, float keyframes, scrollbar styling
│   └── main.jsx          # Entry point
├── index.html            # Imports Google Fonts, sets title
├── postcss.config.js     # PostCSS configurations
├── tailwind.config.js    # Tailwind content path configurations
└── package.json          # Node modules versions
```

---

## 4. Main Pages and Interactive Sections

### Page 1: Product (Landing Page)
1. **Cosmic Hero**: Displays the customized dark mode illustration on the right side of a responsive grid layout. The illustration is framed inside a rotating orbital line and glowing portal backdrop with floating real-time telemetry badge indicators.
2. **Autonomous AI Engines**: A grid of 6 cards showing descriptions, inputs, outputs, and performance stats for bug triage, labeling, vector search, duplicate check, and PR review engines.
3. **E2E Interactive Webhook Simulator**: An interactive panel where users can trigger webhook payloads (Bug, Doc, Enhancement, Duplicate Check, PR Quality, Repository Knowledge, Release Notes, Onboarding) to print styled logs in a mockup console and show final comment mockups on GitHub.
4. **Mockup Dashboard**: Demonstrates metric panels and vector database similarity search scores.
5. **Tech Stack Badges**: Visual cards for FastAPI, PostgreSQL, Redis, Celery, Llama 3.3, Docker, ChromaDB, and the GitHub REST API.

### Page 2: Showcase & Details Page
1. **Maintainer Team**: Showcases the **Heaven Hill** automation group and **Hemant Dhaker** (Full Stack & AI Engineer, Automation Backend Engineer).
2. **Problem Statement**: Details common maintainer exhaustion pain points.
3. **Architecture Flowchart**: A vertical timeline showing webhook lifecycle coordinates.
4. **Future Scope**: Presents the 6 future expansion modules.
5. **FAQ Accordion**: A 6-card interactive accordion answering frequent questions.

---

## 5. Responsive Design & Layouts
- **Breakpoints**: Fits all standard screens using responsive Tailwind utilities (`grid-cols-1 md:grid-cols-2 lg:grid-cols-3` and `lg:grid-cols-12`).
- **Scrollable Payload Container**: The selector pane scrolls internally (`max-h-[380px]`) using a customized scrollbar thumb matching the cosmic theme, keeping the trigger button visible at the bottom and keeping the overall height aligned with the console outputs on the right.

---

## 6. Local Development Setup

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the hot-reloaded development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

---

## 7. Production Bundling
Build the minimized production assets:
```bash
npm run build
```
Vite will compile and output the optimized index, CSS, and JS bundle into the `dist/` directory.
