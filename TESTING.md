# 🧪 Testing Guide — CommitGenerator_Edu

This guide walks you through every test you should run to verify
the tool works correctly before using it for real.

---

## ⚙️ Setup (Do This First)

```bash
# Clone the tool
git clone https://github.com/archijain23/CommitGenerator_Edu.git
cd CommitGenerator_Edu

# Install dependencies
pip install -r requirements.txt

# Verify install
python -c "import git; import pytz; import click; import colorama; print('All dependencies OK')"
```

---

## Test 1 — Dependency Check
```bash
python -c "import git; import pytz; import click; import colorama; print('All dependencies OK')"
```
**Expected:** `All dependencies OK`  
**Fail means:** Run `pip install -r requirements.txt` again

---

## Test 2 — Config Validation (valid config)
```bash
python main.py --config config/commits.json --dry-run
```
**Expected output:**
```
[OK]    Config validated successfully
[WARN]  repo_path './my-target-repo' is relative. It will resolve to: /your/path/my-target-repo
[DRY RUN] The following commits would be created:
[DEBUG] Step 1: 'feat: initialize project structure...' @ UTC 2026-04-25T04:30:00 | Files: [...]
...
[DRY RUN complete] No changes were made to the repository.
```
**What to check:**
- All 10 commits listed
- Timestamps are between `2026-04-25T04:30:00` and `2026-04-25T16:30:00` UTC
  (= 10:00 AM to 10:00 PM IST)
- No error messages

---

## Test 3 — Config Validation (broken config)

Create `config/test_bad.json`:
```json
{
  "repo_path": "./test-repo",
  "author": {"name": "Test"},
  "time_window": {
    "start": "2026-04-25 22:00:00",
    "end": "2026-04-25 10:00:00",
    "timezone": "Asia/Kolkata"
  },
  "commits": [
    {"message": "test", "files": [], "time_override": "25-April-2026"}
  ],
  "options": {"num_commits": 1}
}
```

```bash
python main.py --config config/test_bad.json --dry-run
```
**Expected — should show ALL these errors:**
```
[ERROR] Config validation failed:
[ERROR]   → Missing author field: 'email'
[ERROR]   → time_window.start must be strictly before time_window.end
[ERROR]   → Commit #1: 'time_override' invalid format '25-April-2026'. Use: YYYY-MM-DD HH:MM:SS
```
**What to check:** Validator catches all 3 errors and exits cleanly.

---

## Test 4 — Real Run on Fresh Repo

```bash
# Create a brand new empty target repo
mkdir test-target-repo
cd test-target-repo
git init
cd ..

# Update config to point to it
# Edit config/commits.json: set "repo_path": "./test-target-repo"

# Run for real (no --dry-run)
python main.py --verbose
```

**Expected output:**
```
[OK]    Config validated successfully
[INFO]  Initialized new repo at: /path/to/test-target-repo
[INFO]  Working directory set to: /path/to/test-target-repo
[OK]    [1/10] 'feat: initialize project structure...' @ 2026-04-25T04:30:00 UTC
[OK]    [2/10] 'chore: add .gitignore and requirements' @ 2026-04-25T05:37:00 UTC
...
[OK]    [10/10] 'chore: final cleanup and version bump' @ 2026-04-25T16:18:00 UTC
✅ Done! 10 commit(s) written to: /path/to/test-target-repo
```

**What to check:**
- 10 commits written, no errors
- Files created inside `test-target-repo/`

---

## Test 5 — Verify Commit Timestamps (MOST IMPORTANT)

```bash
cd test-target-repo

# Check all commit dates
git log --pretty=format:"%h | %ai | %s"
```

**Expected — every date should be 2026-04-25, times between 10:00 and 22:00 IST:**
```
a1b2c3d | 2026-04-25 21:45:00 +0530 | chore: final cleanup
e4f5g6h | 2026-04-25 19:30:00 +0530 | docs: write README
...
z9y8x7w | 2026-04-25 10:15:00 +0530 | feat: initialize project
```

**What to check:**
- Date column shows `2026-04-25` for ALL commits ✅
- Times are between `10:00` and `22:00` (IST = +0530) ✅
- Author and committer dates MATCH (run `git log --format="%ai | %ci | %s"`) ✅

```bash
# Verify author date == committer date for every commit
git log --format="%ai | %ci | %s"
# Both date columns should be IDENTICAL on each line
```

---

## Test 6 — Verify Author Identity

```bash
git log --pretty=format:"%an <%ae> | %s"
```

**Expected:** Every line shows the name/email from your `config/commits.json`
```
Your Name <you@example.com> | feat: initialize project structure
Your Name <you@example.com> | chore: add .gitignore
...
```

---

## Test 7 — Verify Files Were Created and Changed

```bash
# Check all files that exist in the repo
find . -not -path './.git/*' -type f

# Check that each file has multiple additions (mutations per commit)
cat src/main.py
# Should show original header + code snippets appended per commit
```

---

## Test 8 — Push to GitHub and Check Display

```bash
# Create a NEW empty repo on GitHub first (no README, no .gitignore)
# Then:
git remote add origin https://github.com/YOUR-USERNAME/YOUR-NEW-REPO.git
git push -u origin main
```

Go to: `https://github.com/YOUR-USERNAME/YOUR-NEW-REPO/commits/main`

**What to check on GitHub:**
- All commits show **Apr 25, 2026** date ✅
- Click any commit → hover the timestamp → tooltip shows exact time within 10AM-10PM IST ✅
- Author name matches your config ✅
- Commit messages match your JSON ✅

---

## Test 9 — num_commits Padding Test

Edit `config/commits.json`:
- Set `"num_commits": 15` (more than the 10 defined commits)

```bash
python main.py --dry-run --verbose
```

**Expected:** 15 commits listed, cycling back through original 10 for the last 5.

---

## Test 10 — Edge Case: Empty Files List

Add this commit to your JSON `commits` array:
```json
{"message": "chore: housekeeping", "files": []}
```

```bash
python main.py --dry-run --verbose
```

**Expected:** Dry run shows the commit with a placeholder file `.edu_log`

For real run: `git log` should show the commit, and `.edu_log` file exists in repo.

---

## ✅ Full Test Checklist

| Test | What It Checks | Must Pass |
|------|---------------|----------|
| 1 | Dependencies installed | ✅ |
| 2 | Dry run with valid config | ✅ |
| 3 | Validator catches bad config | ✅ |
| 4 | Real run creates commits | ✅ |
| 5 | Timestamps in correct IST window | ✅ CRITICAL |
| 6 | Author identity correct | ✅ CRITICAL |
| 7 | Files created and mutated | ✅ |
| 8 | GitHub displays correct dates | ✅ CRITICAL |
| 9 | num_commits padding works | ✅ |
| 10 | Empty files list handled | ✅ |

---

## 🚨 If Something Goes Wrong

```bash
# Reset and start over cleanly
rm -rf test-target-repo
mkdir test-target-repo && cd test-target-repo && git init && cd ..
python main.py --verbose
```

> ⚠️ Never delete the `.git` folder inside CommitGenerator_Edu itself —
> only delete/recreate your **target** repo folder.
