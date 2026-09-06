# Project Setup & Git Workflow Guide

This guide walks through setting up Git, connecting it to VS Code, and the branch/PR workflow we use for this repo.

---

## 1. Install Git

### Check if you already have Git
Open a terminal (Windows: Command Prompt or PowerShell / Mac: Terminal) and run:

```
git --version
```

If it prints a version number, skip to Step 2. If it says "command not found" or similar, install it below.

### Windows
1. Download the installer from https://git-scm.com/download/win
2. Run the installer, leaving default options selected (just click Next through the prompts)
3. Restart any open terminal/VS Code windows
4. Confirm install: `git --version`

### Mac
Option A — using the official installer:
1. Download from https://git-scm.com/download/mac
2. Run the installer and follow the prompts

Option B — using Homebrew (if you have it):
```
brew install git
```

Confirm install:
```
git --version
```

---

## 2. Set Your Git Identity

Git needs a name and email attached to your commits (only needs to be done once per computer):

```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## 3. Clone the Repository

In VS Code:
1. Open the Command Palette (`Ctrl+Shift+P` on Windows, `Cmd+Shift+P` on Mac)
2. Run `Git: Clone`
3. Paste the repository URL (copy it from the green "Code" button on GitHub)
4. Choose a folder to save it in, then open the cloned folder when prompted

Or via terminal:
```
git clone <repository-url>
```

---

## 4. Connect VS Code to GitHub

1. Click the Accounts icon in the bottom-left corner of VS Code
2. Choose "Sign in with GitHub" and follow the browser prompt to authorize
3. Once signed in, VS Code can push/pull and handle authentication automatically

If you're never prompted, just try cloning or pushing — VS Code will trigger the sign-in flow automatically when it needs it.

---

## 5. Branch Workflow

We don't push directly to `main`. Every change goes through a branch and a pull request.

### Step 1: Create a new branch
```
git checkout -b your-branch-name
```
Use a short, descriptive name (e.g. `fix-login-bug`, `add-navbar`).

### Step 2: Make your changes
Edit files as normal in VS Code.

### Step 3: Stage and commit your changes
```
git add .
git commit -m "Describe what you changed"
```

### Step 4: Push your branch to GitHub
```
git push -u origin your-branch-name
```
(The `-u` is only needed the first time you push this branch — after that, `git push` alone works.)

### Step 5: Open a Pull Request
1. Go to the repository on GitHub — you'll usually see a banner prompting "Compare & pull request"
2. Click it, add a title/description of your changes
3. Click "Create pull request"

### Step 6: Wait for review
The PR will be reviewed and merged into `main` once approved. You don't need to do anything else.

### Step 7: Sync your local main after a merge
Once your (or someone else's) branch is merged:
```
git checkout main
git pull
```
This updates your local `main` with the latest merged changes.

### Optional: Clean up merged branches
```
git branch -d your-branch-name
git push origin --delete your-branch-name
```

---

## Quick Command Reference

| Action | Command |
|---|---|
| Check Git version | `git --version` |
| Set name/email | `git config --global user.name "Name"` / `git config --global user.email "you@example.com"` |
| Clone repo | `git clone <url>` |
| Create + switch to branch | `git checkout -b branch-name` |
| Stage changes | `git add .` |
| Commit changes | `git commit -m "message"` |
| Push new branch | `git push -u origin branch-name` |
| Push (after first time) | `git push` |
| Switch branch | `git checkout branch-name` |
| Update local main | `git pull` (while on `main`) |
| View commit history | `git log` |
| Delete local branch | `git branch -d branch-name` |
| Delete remote branch | `git push origin --delete branch-name` |
