# Using VS Code with Taekwondo Scrapers

## Why VS Code Helps

VS Code makes working with the scrapers **much easier**:

✅ **Integrated Terminal** - Run scrapers directly in VS Code
✅ **Python Extension** - Syntax highlighting, debugging, IntelliSense
✅ **File Explorer** - Easy navigation of data directories
✅ **Built-in Git** - Track changes to your scrapers
✅ **Extensions** - Jupyter notebooks, CSV viewers, Excel viewers
✅ **Debugging** - Step through scraper code if issues arise

---

## 🚀 Quick Setup

### 1. Open Project in VS Code

```bash
# From command line
cd "C:\Users\l.gallagher\OneDrive - Team Saudi\Documents\Performance Analysis\Sport Detailed Data\Taekwondo"
code .
```

Or in VS Code: `File > Open Folder` → Select Taekwondo directory

---

### 2. Install Recommended Extensions

Press `Ctrl+Shift+X` to open Extensions, then install:

**Essential:**
- ✅ **Python** (Microsoft) - Python support
- ✅ **Pylance** (Microsoft) - IntelliSense for Python

**Highly Recommended:**
- ✅ **Excel Viewer** (GrapeCity) - View Excel files in VS Code
- ✅ **Rainbow CSV** (mechatroner) - Color-coded CSV viewing
- ✅ **Markdown All in One** - Preview markdown docs
- ✅ **GitLens** - Enhanced Git support

**Optional but Useful:**
- ⭐ **Jupyter** - Run notebooks inline
- ⭐ **Python Indent** - Better indentation
- ⭐ **Path Intellisense** - Autocomplete file paths

---

### 3. Configure Python Interpreter

1. Press `Ctrl+Shift+P`
2. Type: "Python: Select Interpreter"
3. Choose your Python installation (should auto-detect)

---

### 4. Create VS Code Tasks (Optional but Recommended)

Create `.vscode/tasks.json` in your project:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Scrape All Data (Smart Update)",
            "type": "shell",
            "command": "${command:python.interpreterPath}",
            "args": ["scrape_all_data.py"],
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "problemMatcher": []
        },
        {
            "label": "Scrape All Data (Force Full)",
            "type": "shell",
            "command": "${command:python.interpreterPath}",
            "args": ["scrape_all_data.py", "--force-full"],
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "problemMatcher": []
        },
        {
            "label": "Quick Test Endpoints",
            "type": "shell",
            "command": "${command:python.interpreterPath}",
            "args": ["quick_test.py"],
            "problemMatcher": []
        },
        {
            "label": "Run Performance Analyzer",
            "type": "shell",
            "command": "${command:python.interpreterPath}",
            "args": ["performance_analyzer.py"],
            "problemMatcher": []
        },
        {
            "label": "Launch Dashboard",
            "type": "shell",
            "command": "streamlit",
            "args": ["run", "dashboard.py"],
            "problemMatcher": []
        }
    ]
}
```

**Run tasks:** `Ctrl+Shift+P` → "Tasks: Run Task" → Select task

---

### 5. Create Launch Configurations (for Debugging)

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Scrape All Data",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/scrape_all_data.py",
            "console": "integratedTerminal",
            "args": []
        },
        {
            "name": "Python: Quick Test",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/quick_test.py",
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
```

**Debug:** Press `F5` or click Run icon in sidebar

---

## 🎯 Recommended Workflow in VS Code

### Method 1: Using Integrated Terminal (Easiest)

1. Open Terminal: `Ctrl+` ` (backtick) or `View > Terminal`
2. Run commands directly:
   ```bash
   python scrape_all_data.py --force-full
   python performance_analyzer.py
   streamlit run dashboard.py
   ```

### Method 2: Using Tasks (Faster)

1. Press `Ctrl+Shift+P`
2. Type "Tasks: Run Task"
3. Select task from list (e.g., "Scrape All Data (Smart Update)")
4. Task runs in dedicated terminal

### Method 3: Using Run Button (Visual)

1. Open `scrape_all_data.py`
2. Click ▶️ (Play button) in top-right
3. Script runs in terminal

---

## 📊 Viewing Data in VS Code

### CSV Files
1. Install "Rainbow CSV" extension
2. Open any `.csv` file
3. Data is color-coded by column
4. Click "Align" in status bar for pretty formatting

### Excel Files
1. Install "Excel Viewer" extension
2. Open any `.xlsx` file
3. View as spreadsheet directly in VS Code

### Markdown Documentation
1. Open any `.md` file
2. Press `Ctrl+Shift+V` for preview
3. Or click preview icon in top-right

---

## 🐛 Debugging Scrapers

If a scraper fails:

1. Open the Python file (e.g., `scrape_all_data.py`)
2. Click left of line numbers to add breakpoints (red dots)
3. Press `F5` to start debugging
4. Use debug controls:
   - **F10** - Step over
   - **F11** - Step into
   - **F5** - Continue
5. Inspect variables in left sidebar

---

## 📁 Recommended Folder Structure in VS Code

```
Explorer Sidebar (Ctrl+Shift+E):
├── 📄 scrape_all_data.py ⭐ MAIN SCRIPT
├── 📄 quick_test.py
├── 📄 performance_analyzer.py
├── 📄 dashboard.py
│
├── 📁 data/
│   ├── 📁 rankings/
│   ├── 📁 competitions/
│   └── 📁 athletes/
│
├── 📁 taekwondo_data/
│   └── 📁 rankings/
│
├── 📄 QUICK_START_GUIDE.md ⭐
├── 📄 SCRAPER_FIX.md
└── 📄 FINAL_SOLUTION.txt
```

**Pin important files:** Right-click → "Pin Tab"

---

## ⚡ Useful VS Code Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+` ` | Toggle terminal |
| `Ctrl+Shift+P` | Command palette |
| `Ctrl+P` | Quick file open |
| `F5` | Start debugging |
| `Ctrl+Shift+V` | Preview markdown |
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+J` | Toggle panel (terminal/output) |
| `Ctrl+Shift+E` | Explorer |
| `Ctrl+Shift+F` | Search across files |
| `Ctrl+K Ctrl+S` | Keyboard shortcuts |

---

## 🔧 Create Custom Snippets

1. `Ctrl+Shift+P` → "Preferences: Configure User Snippets"
2. Select "Python"
3. Add:

```json
{
  "Run Master Scraper": {
    "prefix": "scrape",
    "body": [
      "# Run master scraper with smart updates",
      "python scrape_all_data.py"
    ]
  },
  "Force Full Scrape": {
    "prefix": "scrapefull",
    "body": [
      "# Force full historical scrape",
      "python scrape_all_data.py --force-full --year-from ${1:2015}"
    ]
  }
}
```

Type `scrape` + Tab to auto-expand

---

## 📊 Monitor Scraping Progress in VS Code

### Option 1: Split Terminal View
1. Open terminal: `Ctrl+` `
2. Click split terminal icon (⊞)
3. Run scraper in one, monitor files in other:
   ```bash
   # Terminal 1:
   python scrape_all_data.py

   # Terminal 2:
   watch -n 5 ls -lh data/rankings/
   ```

### Option 2: Output Panel
- Scraper output appears in Output panel
- Switch between terminals easily

---

## 🎨 Customize VS Code for Data Work

### Settings for Better Python Experience

`Ctrl+,` to open Settings, then add:

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.autoSave": "afterDelay",
  "terminal.integrated.defaultProfile.windows": "Command Prompt"
}
```

---

## 🚀 Run Scraper with One Click

### Create a Run Configuration

1. Click Run icon in sidebar (Ctrl+Shift+D)
2. Click "create a launch.json file"
3. Select "Python File"
4. Now press F5 to run any open Python file!

---

## 📝 Bonus: Git Integration

VS Code has built-in Git:

1. Initialize repo (if not done):
   - `Ctrl+Shift+P` → "Git: Initialize Repository"

2. View changes:
   - Source Control icon (Ctrl+Shift+G)

3. Commit changes:
   - Stage files → Enter message → Commit

4. Add `.gitignore`:
   ```
   __pycache__/
   *.pyc
   .scrape_metadata.json
   data/
   taekwondo_data/
   *.log
   ```

---

## ✅ Quick Start in VS Code

1. **Open Folder:**
   ```bash
   code "C:\Users\l.gallagher\OneDrive - Team Saudi\Documents\Performance Analysis\Sport Detailed Data\Taekwondo"
   ```

2. **Open Terminal:** `Ctrl+` `

3. **Run Master Scraper:**
   ```bash
   python scrape_all_data.py --force-full
   ```

4. **View Results:**
   - Click `data/` folder in Explorer
   - Open CSV files with Rainbow CSV
   - Preview markdown docs

---

## 💡 Tips

- **Split Editor:** `Ctrl+\` to view code and docs side-by-side
- **Multi-Cursor:** `Alt+Click` to edit multiple lines
- **Zen Mode:** `Ctrl+K Z` for distraction-free coding
- **Command Palette:** `Ctrl+Shift+P` is your friend!

---

**Ready to use VS Code?** Run: `code .` in your Taekwondo directory!
