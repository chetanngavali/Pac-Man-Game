# Pac-Man Game

A simple, colorful Pac-Man-style game built with Pygame. Includes menus, sound effects, three levels, and ghost AI.

## Quick Start

1. Install Python 3.9+.
2. Create and activate a virtual environment:
   - Windows PowerShell:
     - `python -m venv .venv`
     - `.\.venv\Scripts\Activate.ps1`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Run the game:
   - `python pacman.py`

## Controls

- Arrow Keys or WASD: Move
- ESC: Pause / Back to menu
- R: Restart current level
- Enter: Next level (after win)

## Features

- Three levels with increasing difficulty
- Ghosts with chase/flee behaviors
- Power pellets that frighten ghosts
- Particle effects and simple background music
- Main menu, level select, settings with volume sliders
- Progress indicator during gameplay

## Files

- `pacman.py` – main game
- `requirements.txt` – Python dependencies
- `.gitignore` – common ignores for Python projects

## Troubleshooting

- If you have no sound, make sure your audio device is available and not exclusively used by another app.
- If Pygame fails to initialize, try running the game from a regular local folder (not a network drive) and ensure Python and pip are on PATH.

## License

Specify a license if you plan to share publicly (e.g., MIT).