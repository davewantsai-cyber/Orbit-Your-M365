# Output: orbit_demo.gif
# Duration: 30 seconds of --dry-run TUI
# Requires: vhs (brew install vhs) + ttyd

Output orbit_demo.gif

Set Theme "Dracula"
Set FontSize 14
Set Width 1280
Set Height 720
Set Framerate 24

Type "cd ~/Projects/orbit-m365"
Enter
Sleep 500ms

Type ".venv/bin/python orbit.py --dry-run"
Enter
Sleep 8s

# Show the animated banner + quotes
Sleep 6s

# Navigate to tool select
Right
Sleep 2s
Right
Enter
Sleep 2s

# Back to home
Escape
Sleep 2s

# Show run screen
Right
Right
Right
Right
Right
Right
Enter
Sleep 3s

Escape
Sleep 1s

Ctrl+C
