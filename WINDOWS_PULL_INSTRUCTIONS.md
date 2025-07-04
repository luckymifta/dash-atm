# Windows Pull Instructions for Reverted Branch

## Overview
These instructions will help you update your Windows machine to the reverted main branch (commit c06fcd5). This ensures your Windows development environment matches the current state of the repository after the reversion.

## Step-by-Step Instructions

### Method 1: Standard Pull (Recommended for Most Cases)

1. **Open Command Prompt or Git Bash**
   - Open Command Prompt or Git Bash on your Windows machine
   - Navigate to your dash-atm project directory:
   ```
   cd path\to\dash-atm
   ```

2. **Fetch the Latest Changes**
   - Fetch all the latest changes from the remote repository:
   ```
   git fetch origin
   ```

3. **Check Out and Reset to the Main Branch**
   - Make sure you're on the main branch:
   ```
   git checkout main
   ```
   - Reset your local main branch to match the remote:
   ```
   git reset --hard origin/main
   ```

4. **Verify the Reversion**
   - Check that you're at the correct commit:
   ```
   git log --oneline -n 1
   ```
   - The output should show: `c06fcd5 feat: implement event-based ATM availability chart for consistent x-axis granularity`

### Method 2: Clean Pull (For Resolving Conflicts or Complex Situations)

If you encounter issues with Method 1, or if you have local changes you want to discard completely:

1. **Save Any Important Work** 
   - If you have any uncommitted changes you want to keep, save them elsewhere first

2. **Hard Reset and Clean Pull**
   ```
   git fetch --all
   git checkout main
   git reset --hard origin/main
   ```

3. **Clean Untracked Files (Optional)**
   - If you want to remove all untracked files and directories:
   ```
   git clean -fd
   ```
   - Warning: This will delete all untracked files and directories in your working copy

## Troubleshooting

### If You Have Local Changes You Want to Keep
```
# Stash your changes before pulling
git stash
git reset --hard origin/main
git stash pop  # This may cause conflicts you'll need to resolve
```

### If You Get an Error About Untracked Files
```
# First try a standard clean
git clean -f

# If that doesn't work, use the more aggressive option
git clean -fd
```

### If You're Getting Weird Git Errors
Try clearing Git's cache:
```
git rm -r --cached .
git reset --hard origin/main
```

## Verification
After pulling, verify that you have the correct version by checking:
1. The commit hash matches c06fcd5
2. The cash information functionality has been removed
3. The additional imports (threading, deque) are not present in combined_atm_retrieval_script.py

## Next Steps
After successfully updating your Windows environment, refer to the MAIN_BRANCH_REVERSION.md document for information about what was reverted and the plan going forward.
