# Git Setup and GitHub Integration Guide

This guide explains how to set up Git on your Raspberry Pi and work with the GitHub repository for easy updates and branch switching.

## Why Use Git?

Using Git with your installation provides several benefits:
- ✅ **Easy updates**: Pull latest changes with one command
- ✅ **Branch switching**: Test new features without affecting your working setup
- ✅ **Version control**: Roll back if something breaks
- ✅ **No manual file copying**: Changes sync automatically from GitHub

## Initial Setup

### 1. Install Git (if not already installed)

Git should be installed automatically by `install.sh`, but if needed:

```bash
sudo apt-get update
sudo apt-get install -y git
```

Verify installation:
```bash
git --version
# Should show: git version 2.x.x
```

### 2. Configure Git

Set your identity (replace with your information):

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Optional but recommended settings:
```bash
# Use main as default branch name
git config --global init.defaultBranch main

# Enable colored output
git config --global color.ui auto

# Set default editor
git config --global core.editor nano
```

Verify your configuration:
```bash
git config --list
```

### 3. If Cloning Fresh from GitHub

If you're setting up from scratch (not using `install.sh`):

```bash
cd ~
git clone https://github.com/KennyNeal/HA-Calendar.git
cd HA-Calendar
```

If the directory already exists, verify it's a Git repository:
```bash
cd ~/HA-Calendar
git status
```

## Working with Branches

### View Available Branches

```bash
# List local branches
git branch

# List all branches (including remote)
git branch -a

# See current branch
git branch --show-current
```

### Switch Between Branches

```bash
# First, fetch latest branch information
git fetch origin

# Switch to main branch
git checkout main

# Switch to a feature branch
git checkout Dynamic-size

# Create and switch to a new branch tracking remote
git checkout -b Dynamic-size origin/Dynamic-size
```

### Get Latest Updates

```bash
# On any branch, pull latest changes
git pull

# Or more verbosely
git fetch origin
git merge origin/main  # or whatever branch you're on
```

## Common Workflows

### Updating to Latest Main Branch

```bash
cd ~/HA-Calendar
git checkout main
git pull
python3 src/main.py  # Test the changes
```

### Testing a New Feature Branch

```bash
cd ~/HA-Calendar

# Save any local changes first
git stash

# Switch to feature branch
git fetch origin
git checkout Dynamic-size

# Test it
python3 src/main.py

# Switch back to main if needed
git checkout main
git stash pop  # Restore your local changes
```

### Keeping Config Files Safe

Your `config/config.yaml` file is in `.gitignore`, so it won't be affected by branch switches or updates. However, it's good practice to back it up:

```bash
cp config/config.yaml config/config.yaml.backup
```

## Handling Conflicts

### If You Have Local Changes

When switching branches or pulling updates with local modifications:

**Option 1: Stash (temporary save)**
```bash
git stash push -m "My local changes"
git checkout other-branch
# ... do your work ...
git checkout original-branch
git stash pop  # Restore changes
```

**Option 2: Discard local changes** (⚠️ Use with caution!)
```bash
git checkout -- .  # Discard ALL local changes
```

**Option 3: Commit your changes**
```bash
git add .
git commit -m "My local modifications"
# Your changes are now saved as a commit
```

### If Files Are Preventing Branch Switch

Sometimes untracked files conflict with branch switching:

```bash
# Move conflicting files to a backup directory
mkdir -p .backup
mv conflicting-file.txt .backup/

# Then try switching again
git checkout desired-branch
```

## Useful Git Commands

### Check Status
```bash
git status                    # See modified/untracked files
git log --oneline -10        # See last 10 commits
git diff                     # See what changed
git diff main..Dynamic-size  # Compare two branches
```

### Undo Changes
```bash
git checkout -- filename.py  # Discard changes to one file
git reset --hard            # Discard ALL changes (⚠️ dangerous!)
git clean -fd               # Remove untracked files
```

### Branch Management
```bash
git branch -d branch-name    # Delete local branch
git fetch --prune           # Clean up old remote branches
```

## Automation with Git

### Auto-update Script

Create a script to automatically update from GitHub:

```bash
nano ~/update-calendar.sh
```

Add:
```bash
#!/bin/bash
cd ~/HA-Calendar
echo "Updating HA-Calendar from GitHub..."
git fetch origin
git pull
echo "Restarting calendar service..."
pkill -f "python3 src/main.py"
python3 src/main.py
echo "Update complete!"
```

Make executable:
```bash
chmod +x ~/update-calendar.sh
```

Run when needed:
```bash
~/update-calendar.sh
```

## Troubleshooting

### "fatal: not a git repository"
```bash
cd ~/HA-Calendar
ls -la .git  # Check if .git directory exists
# If missing, you may need to clone fresh
```

### "Your branch is behind origin/main"
```bash
git pull  # Pull the latest changes
```

### "You have divergent branches"
```bash
# Usually safe to just pull
git pull --rebase
# Or reset to match remote
git reset --hard origin/main
```

### "Permission denied" when pushing
You don't need to push changes unless you're a contributor. Just pull to get updates.

### Accidentally deleted something important
```bash
# Restore from last commit
git checkout HEAD -- filename.py

# Or restore everything
git reset --hard HEAD
```

## SSH Keys (Optional, for Contributors)

If you need to contribute changes back to the repository:

### Generate SSH Key
```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
cat ~/.ssh/id_ed25519.pub  # Copy this to GitHub
```

### Add to GitHub
1. Go to GitHub.com → Settings → SSH Keys
2. Click "New SSH key"
3. Paste your public key
4. Save

### Switch Remote to SSH
```bash
git remote set-url origin git@github.com:KennyNeal/HA-Calendar.git
git remote -v  # Verify
```

## Best Practices

1. **Always fetch before switching branches**: `git fetch origin`
2. **Stash or commit local changes** before pulling
3. **Back up your config file** regularly
4. **Test in mock mode first** after pulling updates
5. **Read commit messages** to understand what changed: `git log`
6. **Stay on a stable branch** (main) unless testing features

## Getting Help

```bash
git help              # General help
git help checkout     # Help for specific command
man git               # Full manual
```

## Additional Resources

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com/
- **Git Cheat Sheet**: https://education.github.com/git-cheat-sheet-education.pdf
- **HA-Calendar Repository**: https://github.com/KennyNeal/HA-Calendar
