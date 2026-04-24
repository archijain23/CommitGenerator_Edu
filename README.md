# 🎓 CommitGenerator_Edu

> **⚠️ EDUCATIONAL PURPOSES ONLY**  
> This tool is built strictly for learning Git internals, understanding commit metadata, and studying how version control systems handle timestamps. It must **never** be used to misrepresent contribution timelines in professional, academic, or open-source environments.

---

## 📌 What Is This?

`CommitGenerator_Edu` is a Python-based educational CLI tool that:

- Takes a **brand-new Git repository** (no prior history)
- Reads a **user-defined JSON config file** containing commit definitions
- Generates **realistic-looking commits** spread across a user-defined time window
- Randomly selects files and applies code changes to **mimic real human development patterns**
- Gives full control over **commit count**, **time range**, **messages**, and **file content**

---

## 🗂️ Project Structure

```
CommitGenerator_Edu/
├── core/
│   ├── __init__.py
│   ├── commit_engine.py       # Core commit generation logic
│   ├── time_distributor.py    # Distributes commits across time window
│   ├── file_mutator.py        # Randomly mutates files to simulate real changes
│   └── validator.py           # Validates JSON config before execution
├── config/
│   └── commits.json           # 📝 User-defined commit config (edit this!)
├── templates/
│   ├── python_snippets.json   # Code snippets for Python file mutations
│   └── js_snippets.json       # Code snippets for JS file mutations
├── utils/
│   ├── __init__.py
│   ├── logger.py              # Colored terminal logging
│   └── git_helpers.py         # Git utility wrappers
├── main.py                    # 🚀 CLI entry point
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration (`config/commits.json`)

All behavior is controlled via the JSON config file:

```json
{
  "repo_path": "./target-repo",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "time_window": {
    "start": "2026-04-25 10:00:00",
    "end": "2026-04-25 22:00:00",
    "timezone": "Asia/Kolkata"
  },
  "commits": [
    {
      "message": "feat: initialize project structure",
      "files": ["src/main.py", "src/utils.py"],
      "time_override": "2026-04-25 10:15:00"
    },
    {
      "message": "fix: resolve import error in utils",
      "files": ["src/utils.py"]
    },
    {
      "message": "docs: update README with setup instructions",
      "files": ["README.md"]
    }
  ],
  "options": {
    "num_commits": 8,
    "auto_distribute_time": true,
    "randomize_file_changes": true,
    "random_mutation_language": "python",
    "dry_run": false
  }
}
```

### Config Fields Explained

| Field | Description |
|-------|-------------|
| `repo_path` | Path to the target (new, empty) Git repository |
| `author.name` / `author.email` | Git author identity for all commits |
| `time_window.start` / `end` | IST time range for commit distribution |
| `time_window.timezone` | Timezone string (e.g. `Asia/Kolkata`, `UTC`) |
| `commits[].message` | Commit message for this entry |
| `commits[].files` | Files to stage for this commit |
| `commits[].time_override` | Optional: force this commit to a specific time |
| `options.num_commits` | Total commits to generate (if auto-distributing) |
| `options.auto_distribute_time` | Evenly spread commits across time window |
| `options.randomize_file_changes` | Inject random code mutations per commit |
| `options.random_mutation_language` | `python` or `js` for snippet injection |
| `options.dry_run` | Preview commits without writing to repo |

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
git clone https://github.com/archijain23/CommitGenerator_Edu.git
cd CommitGenerator_Edu
pip install -r requirements.txt
```

### 2. Set up your target repo
```bash
mkdir my-target-repo
cd my-target-repo
git init
git config user.name "Your Name"
git config user.email "you@example.com"
cd ..
```

### 3. Edit the config
```bash
nano config/commits.json
# Set repo_path to "./my-target-repo"
# Set your author details, time window, and commits
```

### 4. Run the generator
```bash
python main.py
# or with a custom config:
python main.py --config config/commits.json
```

### 5. Push the target repo to GitHub
```bash
cd my-target-repo
git remote add origin https://github.com/your-username/your-new-repo.git
git push -u origin main
```

---

## 🧠 How It Works

1. **Config Validation** — `validator.py` checks the JSON for required fields, valid timezone, and time range sanity.
2. **Time Distribution** — `time_distributor.py` spreads commits evenly (or randomly) across the `start`→`end` window, converting IST→UTC for Git env vars.
3. **File Mutation** — `file_mutator.py` picks files from the commit definition and optionally injects realistic code snippets from `templates/`.
4. **Commit Engine** — `commit_engine.py` sets `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` to identical UTC values, stages the files, and calls `git commit`.
5. **Logging** — `logger.py` prints colored, structured output so you can follow every step.

---

## 📚 Educational Use Cases

- Understanding `GIT_AUTHOR_DATE` vs `GIT_COMMITTER_DATE` and how Git stores metadata
- Learning how interactive rebase, `filter-branch`, and `filter-repo` rewrite history
- Studying Git's object model (blobs, trees, commits)
- Exploring how GitHub renders commit timestamps vs push timestamps
- Teaching/learning version control internals in workshops or classrooms

---

## ⚠️ Ethical Disclaimer

This tool is provided **for educational exploration of Git internals only**.

- ❌ Do NOT use this to fake contribution streaks on public GitHub profiles
- ❌ Do NOT use this to misrepresent work timelines in professional or academic settings
- ❌ Do NOT use this to deceive employers, professors, or hackathon judges
- ✅ DO use this to understand how Git stores and displays timestamps
- ✅ DO use this in sandboxed, throwaway repositories for learning
- ✅ DO use this with explicit permission from event organizers (educational demonstrations)

Misuse of this tool in deceptive contexts may violate platform Terms of Service (GitHub ToS Section 3) and academic integrity policies.

---

## 📦 Requirements

- Python 3.8+
- Git installed and in PATH
- `gitpython` >= 3.1.0
- `pytz` >= 2021.1
- `click` >= 8.0.0
- `colorama` >= 0.4.4

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.
