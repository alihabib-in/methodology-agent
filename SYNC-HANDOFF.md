# Parallel Development Hand-Off Guide

How to run this project on a second laptop using OpenCode + GitHub, and keep two
machines in sync without conflicts.

Repo: `https://github.com/alihabib-in/methodology-agent.git` — default branch `master`.

---

## 1. Initial Setup (new laptop)

### 1.1 Install OpenCode

Windows (WSL2 recommended for best compatibility):

```powershell
wsl --install
# inside the WSL shell:
curl -fsSL https://opencode.ai/install | bash
```

Windows (native, no WSL):

```powershell
npm install -g opencode-ai
# or:  choco install opencode
# or:  scoop install opencode
```

macOS / Linux:

```bash
curl -fsSL https://opencode.ai/install | bash
# or:  brew install anomalyco/tap/opencode
```

### 1.2 Set Git identity

Must match what you use on GitHub:

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

### 1.3 Authenticate GitHub (choose one)

```bash
# Option A — GitHub CLI (simplest for HTTPS):
gh auth login
# GitHub.com > HTTPS > authenticate via browser

# Option B — SSH:
ssh-keygen -t ed25519 -C "you@example.com"
cat ~/.ssh/id_ed25519.pub   # paste into GitHub → Settings → SSH and GPG keys
```

### 1.4 Connect OpenCode to your AI provider

```bash
opencode            # launch the TUI, then run:
/connect            # choose a provider and paste your API key
```

---

## 2. Repository Mirroring (clone)

### 2.1 Confirm the source machine is fully pushed (on the old laptop)

```bash
git status -sb                          # should show "## master...origin/master"
git log origin/master..HEAD --oneline   # empty = nothing unpushed
```

### 2.2 Clone on the new laptop

```bash
# HTTPS:
git clone https://github.com/alihabib-in/methodology-agent.git

# or SSH:
git clone git@github.com:alihabib-in/methodology-agent.git

cd methodology-agent
git branch --show-current   # should print "master"
```

### 2.3 Initialize OpenCode for the project

```bash
opencode
/init          # analyzes the repo and creates AGENTS.md
```

Then commit `AGENTS.md` so both machines share the same project context:

```bash
git add AGENTS.md
git commit -m "Add OpenCode project context (AGENTS.md)"
git push origin master
```

> Machine-specific files (e.g. `frontend/.env` with your LAN IP, `models/*.gguf`)
> are git-ignored. Recreate/adjust them on the new laptop; never commit them.

---

## 3. Sync Workflow (two machines, one repo)

### 3.1 Pull before starting work

```bash
cd methodology-agent
git fetch origin
git pull --rebase origin master
```

`--rebase` replays your local commits on top of the remote, keeping history linear.

### 3.2 Commit often (small, atomic commits)

```bash
git status -sb
git add <specific files>      # prefer explicit paths over "git add -A"
git commit -m "feat(api): add gap-assessment endpoint"
```

### 3.3 Push after each logical chunk

```bash
git push origin master
```

### 3.4 Check sync state at any time

```bash
git status -sb                          # ahead/behind summary
git log origin/master..HEAD --oneline   # commits you haven't pushed
git log HEAD..origin/master --oneline   # remote commits you don't have yet
```

### 3.5 Handling merge conflicts

```bash
# 1. Fix the <<<<<<< / ======= / >>>>>>> blocks in the conflicted files
# 2. Mark them resolved:
git add <fixed-file>

# 3a. If rebasing — continue:
git rebase --continue
#    (abort with: git rebase --abort)

# 3b. If merging — commit the merge:
git commit -m "Merge origin/master"
```

Then `git push origin master`.

---

## 4. Weekend Workflow (daily routine)

### Start of every session (whichever machine)

```bash
git pull --rebase origin master
```

### End of every session — the "hand-off" ritual

```bash
git add -A
git commit -m "WIP: <what you did>"
git push origin master
```

### Switching machines mid-day

```bash
# Machine A (before walking away):
git push origin master

# Machine B (when sitting down):
git pull --rebase origin master
```

### Rules to avoid conflicts

1. **Never start without pulling first** — stale checkouts cause most conflicts.
2. **Always push before switching machines.** If you can't push, `git status -sb`
   and note the "ahead by N" as your reminder.
3. **Don't edit the same files on both machines concurrently.** If unavoidable,
   keep changes tiny and push frequently.
4. **Commit `AGENTS.md` changes too** — it keeps OpenCode's project context
   consistent across machines.

Single-line weekend loop when bouncing between machines:

```bash
git pull --rebase origin master && git add -A && git commit -m "sync" && git push origin master
```
