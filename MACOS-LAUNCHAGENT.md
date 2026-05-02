# macOS LaunchAgent for Recipe Library

This document explains how to start the Recipe Library container automatically at macOS login using a user [`LaunchAgent`](scripts/com.cuisine-recipes-library.webapp.plist).

## Files

- [`scripts/macos-launch-recipe-library.sh`](scripts/macos-launch-recipe-library.sh): wrapper script that starts the application with [`start-docker.sh`](start-docker.sh)
- [`scripts/com.cuisine-recipes-library.webapp.plist`](scripts/com.cuisine-recipes-library.webapp.plist): LaunchAgent definition for macOS

## How it works

The macOS agent runs [`/bin/bash -lc`](scripts/com.cuisine-recipes-library.webapp.plist) and sets a local `PROJECT_DIR` variable before calling [`scripts/macos-launch-recipe-library.sh`](scripts/macos-launch-recipe-library.sh).

The wrapper script then:

1. changes to the project directory
2. ensures the [`logs/`](logs/) directory exists
3. launches [`start-docker.sh`](start-docker.sh)
4. appends output to [`logs/macos-launch.log`](logs/macos-launch.log)

## Install

Copy the LaunchAgent file into your user LaunchAgents folder:

```bash
mkdir -p ~/Library/LaunchAgents
cp ./scripts/com.cuisine-recipes-library.webapp.plist ~/Library/LaunchAgents/
chmod 644 ~/Library/LaunchAgents/com.cuisine-recipes-library.webapp.plist
chmod +x ./scripts/macos-launch-recipe-library.sh
```

Load it immediately:

```bash
launchctl unload ~/Library/LaunchAgents/com.cuisine-recipes-library.webapp.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.cuisine-recipes-library.webapp.plist
```

Or with the modern command form:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.cuisine-recipes-library.webapp.plist 2>/dev/null || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cuisine-recipes-library.webapp.plist
```

After login, macOS will run the agent automatically.

## Check status

```bash
launchctl list | grep cuisine-recipes-library
```

Inspect logs:

```bash
tail -f ./logs/macos-launch.log
tail -f ./logs/macos-launchagent.out.log
tail -f ./logs/macos-launchagent.err.log
```

## Stop or disable

Unload the agent:

```bash
launchctl unload ~/Library/LaunchAgents/com.cuisine-recipes-library.webapp.plist
```

Or:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.cuisine-recipes-library.webapp.plist
```

Remove the file if you no longer want startup execution:

```bash
rm -f ~/Library/LaunchAgents/com.cuisine-recipes-library.webapp.plist
```

## Important notes

- [`LaunchAgent`](scripts/com.cuisine-recipes-library.webapp.plist) starts when your user session logs in, not before the graphical session exists.
- The current [`plist`](scripts/com.cuisine-recipes-library.webapp.plist) contains the project path for this machine: `/Users/fredericfadda/ffadev/cuisine-recipes-library`.
- If the project moves, update both [`scripts/macos-launch-recipe-library.sh`](scripts/macos-launch-recipe-library.sh) and [`scripts/com.cuisine-recipes-library.webapp.plist`](scripts/com.cuisine-recipes-library.webapp.plist).
- If Docker Desktop or Podman is not ready yet at login, the startup may fail and should be checked in the log files.
- [`start-docker.sh`](start-docker.sh) currently runs [`docker-compose up --build`](start-docker.sh:85) or [`podman-compose up --build`](start-docker.sh:85), so the LaunchAgent keeps the process attached while the container stack is running.