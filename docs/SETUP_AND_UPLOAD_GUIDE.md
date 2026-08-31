# 🚀 GitHub Setup, Hosting & Upload Guide for LinForge

This guide walks you through setting up, uploading, and hosting **LinForge** on GitHub so that anyone around the world can launch it with a single terminal command:

```bash
curl -fsSL https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/linforge/main/install.sh | bash
```

---

## 1. Repository Name & Human-Written GitHub Description

When creating your GitHub repository, use the following recommended details for maximum discovery, clarity, and SEO:

- **Repository Name**: `linforge` *(or `kubuntu-util` if you want a distro-specific brand)*
- **Tagline / Description**:
  > *The ultimate Linux post-install setup, gaming optimization, hardware doctor, and system maintenance suite — like Chris Titus WinUtil, but supercharged for Kubuntu, Ubuntu & Linux.*
- **Website URL** *(Optional)*: `https://<YOUR_GITHUB_USERNAME>.github.io/linforge/`
- **Topics / Tags**:
  `linux`, `kubuntu`, `ubuntu`, `winutil`, `linutil`, `gaming-linux`, `driver-installer`, `system-maintenance`, `kde-plasma`, `debian`, `fedora`, `flatpak`, `pipewire`, `steam-deck`, `system-cleaner`, `troubleshooting`
- **Visibility**: `Public`
- **License**: `MIT License`

---

## 2. Step-by-Step Initial Upload (Git Push)

Open your terminal in the project root directory (`d:\Projects\Actual-Projects\Other\H-N\K\Kubuntu-Util(Gemini)` or on Linux in your project folder) and follow these exact steps:

### Option A: Using the GitHub CLI (`gh`) (Fastest & Easiest)

```bash
# 1. Initialize git repository (if not already done)
git init -b main

# 2. Stage all files
git add .

# 3. Create initial commit
git commit -m "feat: Initial release of LinForge Linux setup & maintenance suite"

# 4. Create and push repository to GitHub automatically
gh repo create linforge --public --source=. --remote=origin --push
```

---

### Option B: Using Standard Git & GitHub Web UI

1. Go to [https://github.com/new](https://github.com/new).
2. Enter Repository name: **`linforge`**.
3. Choose **Public**.
4. Leave *"Initialize this repository with a README"* **unchecked** (we already have our comprehensive README.md).
5. Click **Create repository**.
6. Run the following terminal commands in your local project folder:

```bash
# 1. Initialize local git repository
git init -b main

# 2. Stage all files
git add .

# 3. Commit the codebase
git commit -m "feat: Initial release of LinForge Linux setup & maintenance suite"

# 4. Link your remote GitHub repository (replace with your GitHub username)
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/linforge.git

# 5. Push to main branch
git push -u origin main
```

---

## 3. Configuring the One-Line Curl Launch Command

In `install.sh`, locate line 57:
```bash
git clone --depth 1 https://github.com/maddox-h/linforge.git "$TMP_DIR"
```
Replace `maddox-h` with your own GitHub username if you are hosting it under your personal account.

Once pushed, your universal one-liner will immediately work anywhere:

```bash
curl -fsSL https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/linforge/main/install.sh | bash
```

---

## 4. Setting Up GitHub Releases & Version Tags

Creating official GitHub releases allows users to download specific stable bundles and gives your project credibility:

```bash
# Tag the initial version
git tag -a v1.0.0 -m "LinForge v1.0.0 - Production Release"
git push origin v1.0.0

# Create the release using GitHub CLI
gh release create v1.0.0 --title "LinForge v1.0.0 — The Ultimate Linux Setup Suite" --notes "Initial public release featuring 100+ app store catalog, Driver Doctor, Gaming sysctl tweaks, PipeWire audio repair, and deep system cleaner."
```

---

## 5. Setting Up a Short Vanity URL *(Optional)*

To make your command as short and clean as Chris Titus's (`christitus.com/linux`), you can:

1. **Option 1: Using GitHub Pages**:
   - Enable GitHub Pages in your repository settings under **Settings -> Pages** (Source: `Deploy from a branch`, Branch: `main`, Folder: `/docs` or `/`).
   - Place an `index.html` or redirection script in your root/docs.

2. **Option 2: Free URL Redirection (e.g. `is.gd`, `tinyurl.com`, or custom domain)**:
   - Shorten `https://raw.githubusercontent.com/<USER>/linforge/main/install.sh` to something memorable like `https://get.linforge.io` or `https://is.gd/linforge`.
   - Then users can launch simply by:
     ```bash
     curl -fsSL https://is.gd/linforge | bash
     ```

---

## 6. How to Push Future Updates & New Apps

When you add new applications to `src/data/apps.json` or new tweaks to `src/data/tweaks.json`:

```bash
# 1. Run the test suite to ensure all data and syntax is valid
python3 -m unittest discover -s tests -p "test_*.py"

# 2. Stage and commit changes
git add .
git commit -m "feat(apps): add new applications and gaming tweaks"

# 3. Push to GitHub
git push origin main
```

Every user who launches LinForge via the curl command will automatically receive your latest updates instantly!
