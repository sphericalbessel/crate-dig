Crate Dig — Project Spec & Setup Guide
What this document is
This is a plan-first spec. Nothing gets built until this document feels right. The project has two goals: ship a simple, useful music library tool, and set up a robust agentic development workflow that carries forward to every future project.

Part 1: GitHub & Local Environment Setup
GitHub cleanup
You have fewer than 5 repos, mostly experiments. The approach:

Archive, don't delete. Go to each repo's Settings > General > scroll to Danger Zone > Archive. This keeps the code accessible but signals "this isn't active." If any repo is truly empty or embarrassing, delete it — but archiving is safer and takes 10 seconds.
Keep the screen-scanner repo if it exists. You'll come back to it. Just archive it for now so it's clear it's paused.
Create a clean new repo for Crate Dig. This is your first properly structured project.

Local folder structure
Set up a single parent directory for all your dev projects. This is where every repo lives from now on.
~/dev/
  crate-dig/          # this project
  screen-scanner/     # future — clone back when ready
Don't overthink this. One folder, one repo per project, clone from GitHub when you need it. The ~/dev/ convention is standard and keeps things out of your messy Desktop.
GitHub repo setup for Crate Dig
Create the repo on GitHub first (with a README), then clone locally:
bashmkdir -p ~/dev
cd ~/dev
git clone git@github.com:YOUR_USERNAME/crate-dig.git
cd crate-dig
Initial repo structure
crate-dig/
├── CLAUDE.md              # Agent context file (see Part 3)
├── README.md              # Project description for humans
├── .gitignore             # Python + Node ignores
├── requirements.txt       # Python dependencies
├── backend/
│   ├── app.py             # Flask/FastAPI server
│   ├── scanner.py         # Music file discovery and metadata reading
│   └── tagger.py          # Metadata writing
├── frontend/
│   └── index.html         # Single-file UI (vanilla HTML/CSS/JS to start)
└── tests/
    └── test_scanner.py    # Basic tests for file reading
Why this structure: it's flat enough that you can see everything at a glance, but separated enough that backend and frontend don't bleed into each other. No frameworks, no build tools, no complexity you don't need yet.

Part 2: Crate Dig — Product Spec
The problem
You have music files scattered across multiple folders on your machine. Some have good metadata (artist, title, BPM, key, genre), some have partial metadata, some have none. You can't quickly see what you have, find things, or fix the messy tags.
The solution (v1)
A local web app that:

Scans one or more folders you point it at
Reads metadata from music files (MP3, FLAC, WAV, AIFF — whatever you actually have)
Displays your library in a clean, sortable table
Lets you edit metadata inline (click a cell, type, save)
Writes changes back to the actual files

That's it. No AI, no APIs, no cloud, no accounts. Local files in, local files out.
What v1 is NOT

Not a music player (maybe v2)
Not an auto-tagger (maybe v2 — could use Discogs API, audio fingerprinting, or AI)
Not a playlist builder (maybe v3)
Not deployed anywhere — runs on localhost only

Tech stack
Backend: Python + Flask

You know Python well. Flask is minimal and won't fight you.
mutagen library for reading/writing music file metadata (handles MP3, FLAC, WAV, AIFF, M4A)
Serves the frontend as a static file
Exposes a simple REST API: GET /tracks, PUT /tracks/:id

Frontend: Single HTML file with vanilla JS

No React, no build step, no npm for the frontend
A sortable table with editable cells
Minimal CSS that looks clean (you can make it nicer later)
Fetches data from the Flask API

Why this stack: You're a data scientist who knows Python. Flask is the thinnest possible web framework. Vanilla frontend means zero tooling overhead. The entire app is maybe 4-5 files. You can read and understand all of it.
Data model
Each track has:

id (hash of file path — stable identifier)
file_path (absolute path on disk)
file_name (just the filename)
file_format (mp3, flac, wav, etc.)
title (from metadata, or null)
artist (from metadata, or null)
album (from metadata, or null)
genre (from metadata, or null)
bpm (from metadata, or null — important for DJs)
key (from metadata, or null — important for DJs)
duration_seconds (from metadata)
file_size_mb (from file system)

No database. The source of truth is always the files themselves. The app reads metadata fresh on each scan. This keeps things simple and means you never have sync issues.
User flow

Start the app: python backend/app.py
Browser opens to localhost:5000
You see a config panel where you enter folder paths to scan (persisted in a simple JSON config file)
Click "Scan" — the app reads all music files in those folders
A table appears showing all tracks with their metadata
Click any cell to edit it
Click "Save" to write changes back to the file
Columns are sortable (click header to sort)
A search/filter bar at the top to find tracks quickly

Constraints

Must handle at least 1,000 files without choking
Must not corrupt files when writing metadata
Must work on macOS (your machine) — Linux and Windows are nice-to-haves but not v1 requirements
Must not require any external services or internet connection


Part 3: CLAUDE.md — Agent Context File
This is the file that goes in the root of your repo. It tells Claude Code (or any agent) everything it needs to know about the project, your preferences, and how to work with you. This is the "memory" file from the Reuben Jenkins post — persistent context that avoids re-explaining the same things every session.
markdown# CLAUDE.md — Crate Dig

## Project overview
Crate Dig is a local web app for scanning, viewing, and editing music file metadata. It runs on localhost, reads/writes ID3 and Vorbis tags via the mutagen library, and serves a vanilla HTML frontend through Flask.

## Tech stack
- Backend: Python 3.11+, Flask, mutagen
- Frontend: Single HTML file, vanilla JS, no build tools
- No database — metadata is read directly from files
- No external APIs in v1

## Project structure
- backend/ — Flask app, scanner, tagger modules
- frontend/ — Single index.html served as static file
- tests/ — pytest tests for backend logic
- requirements.txt — Python dependencies only

## Code style preferences
- Simple readable code over clever abstractions
- Plain pandas-style data manipulation where needed (but this project is mostly dicts and lists)
- No class hierarchies unless genuinely needed — functions and modules are fine
- Short, clear variable names
- Comments only where the "why" isn't obvious from the code

## Writing style (for README, comments, commit messages)
- No em dashes
- No bullet points in prose
- Short sentences, plain English
- Understated confidence, no hedging

## How to work with me
- Always start with a plan before writing code. Describe what you're going to do and why.
- If something is ambiguous in the spec, ask rather than assume.
- Keep changes small and testable. Don't rewrite three files at once.
- Run tests after changes. If tests don't exist for what you're changing, write them first.
- Don't add dependencies without explaining why the standard library won't work.

## Current status
- [x] Project scaffolding (files, folders, .gitignore, requirements.txt)
- [x] Scanner module — discover music files in given directories
- [x] Metadata reader — extract tags from discovered files using mutagen
- [ ] Flask API — GET /tracks endpoint returning JSON
- [ ] Frontend — basic table displaying track data
- [ ] Metadata editor — inline editing in the table
- [ ] Flask API — PUT /tracks/:id endpoint writing tags back
- [ ] Search and sort functionality
- [ ] Config persistence (folder paths saved between sessions)
- [ ] Error handling and edge cases (corrupted files, missing permissions, etc.)

## Known constraints
- mutagen handles MP3 (ID3), FLAC (Vorbis), WAV, AIFF, M4A
- No database — always read from files, which means scanning is O(n) on every load
- For v1 this is fine up to ~1,000 files. If it gets slow, add a lightweight cache later.

## Testing
- Run tests with: pytest tests/
- Test the scanner with a small folder of test files (include a few MP3s and FLACs with known metadata)

Part 4: The Workflow
This is the process you follow for every piece of work on this project. It matches the workflow described in the LinkedIn post you saved — plan mode first, then generation.
Step 1: Open Claude Code in the project directory
bashcd ~/dev/crate-dig
claude
Claude Code reads the CLAUDE.md automatically.
Step 2: Plan before building
For each new feature, start by asking Claude Code to plan:

"I want to build the scanner module that discovers music files in a directory. Plan mode: describe the approach, what functions we need, how we'll handle edge cases, and what tests to write. Don't write any code yet."

Read the plan. Push back on anything that feels overcomplicated. Iterate until it's right.
Step 3: Build incrementally
Once the plan is solid:

"OK, let's implement the scanner module as planned. Start with the file discovery function and its tests."

Small pieces. Test after each piece. Commit after each working increment.
Step 4: Git discipline
bashgit add -A
git commit -m "add scanner module with directory traversal and file type filtering"
git push
Commit messages should be lowercase, describe what changed, and be one line. Commit after every working increment, not at the end of a long session.
Step 5: Update CLAUDE.md
After each session, update the "Current status" checklist in CLAUDE.md. This is how the agent knows where you are next time.

Part 5: Build Order
Work through these in order. Each one is a single session or less.
Session 1: Scaffolding
Create the repo, set up the folder structure, install dependencies, verify mutagen can read a test file. Commit.
Session 2: Scanner + metadata reader
Build the module that walks directories, finds music files, and extracts metadata. Write tests. Commit.
Session 3: Flask API
Create the GET /tracks endpoint that returns scanned library as JSON. Verify with curl or browser. Commit.
Session 4: Frontend table
Build the HTML page that fetches from the API and displays tracks in a sortable table. Commit.
Session 5: Inline editing + write-back
Add click-to-edit on table cells and a PUT endpoint that writes tags back to files. This is the scariest part — test on copies of files first. Commit.
Session 6: Search, filter, polish
Add a search bar, column sorting, and general UI cleanup. Commit.
Session 7: Edge cases and README
Handle corrupted files gracefully, add proper error messages, write a clean README. Tag as v1.0. Commit.

Appendix: Tools and what they're for
ToolUse it forDon't use it forClaude CodeWriting code, planning, debugging inside the repoGeneral chat, researchCursorIDE with AI assist — good for reviewing and editing code Claude Code wroteRunning terminal agentsVercelDeploying public web apps (screen scanner later)This project (it's local only)Twill.aiDelegating routine tasks across multiple reposLearning stage — too much abstractionGitHubVersion control, backup, portfolioStoring music files or large binaries