**multi-phase trading bot setup**.

---

````markdown
# 📘 Git Guide for Ajeet Trader - Trading Bot

A reference for managing the version control of your multi-phase trading bot project using Git and GitHub.

---

## 🚀 Project Workflow

### 📂 Branching Structure

| Phase | Branch Name     | Description                             |
|-------|------------------|-----------------------------------------|
| 1     | `phase-1`        | Base system: strategy engine, backtest  |
| 2     | `phase-2`        | AI auto-retraining, dashboards          |
| 3+    | `phase-3`, etc.  | Further improvements                    |
| -     | `main`           | Mirrors latest stable or production     |

---

## 🌱 Daily Use Git Commands

| Task | Command |
|------|---------|
| Check current status | `git status` |
| Add all changes | `git add .` |
| Commit with message | `git commit -m "your message"` |
| Push to GitHub | `git push origin <branch>` |
| Pull updates | `git pull origin <branch>` |
| Switch to another branch | `git checkout <branch>` |
| See all branches | `git branch -a` |

---

## 🌿 Branch Management

### Create and Push New Phase Branch

```bash
git checkout -b phase-2         # Create phase 2 branch
git push origin phase-2         # Push to GitHub
````

### Switch Between Phases

```bash
git checkout phase-1
git checkout phase-2
```

---

## 🏷️ Tags (Release Snapshots)

### Create and Push a Tag

```bash
git tag v1.0-phase1
git push origin v1.0-phase1
```

### Checkout a Tag (Read-Only)

```bash
git checkout tags/v1.0-phase1
```

### Create Editable Branch from Tag

```bash
git switch -c debug-phase1 tags/v1.0-phase1
```

---

## 🧰 Useful Git Tools

| Task                                | Command                            |
| ----------------------------------- | ---------------------------------- |
| View commit log                     | `git log --oneline --graph --all`  |
| Show changes before commit          | `git diff`                         |
| Uncommit last commit (keep changes) | `git reset --soft HEAD~1`          |
| Uncommit & discard changes ⚠️       | `git reset --hard HEAD~1`          |
| Temporarily save uncommitted work   | `git stash`                        |
| Reapply stash                       | `git stash apply`                  |
| Delete a local branch               | `git branch -d phase-2`            |
| Delete a remote branch              | `git push origin --delete phase-2` |

---

## 🔁 Workflow Summary

### Create a New Phase

```bash
git checkout phase-1
git checkout -b phase-2
git push origin phase-2
```

### Tag Current Stable Version

```bash
git tag v1.0-phase1
git push origin v1.0-phase1
```

### Merge Phase 2 into Main

```bash
git checkout main
git merge phase-2
git push origin main
```

---

## 🧭 Tips

* Use `git switch -` to quickly return to your previous branch.
* Keep each phase as a **separate branch** for clean version tracking.
* Use tags like `v1.0-phase1`, `v1.1-phase2` to **mark stable milestones**.

---

**Maintainer:** Ajeet Kumar Gupta
**Repo:** [ajeet-trader/trading\_bot](https://github.com/ajeet-trader/trading_bot)

```

---

```
