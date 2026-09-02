# DEA Story Scraper & Reader Pro 📖⚡

**Developed by DEA Innovations**  
Website: [www.deainnovations.com](https://www.deainnovations.com)

---

## 🌟 Overview
**DEA Story Scraper & Reader Pro** is a modern Windows desktop application designed to scrape, clean, audit, and consolidate multi-part and single-part stories from various web platforms into a clean, distraction-free reading experience.

It features a built-in **Google AdSense & AdsKeeper Policy Safety Auditor**, separate 1-click **Title & Body copying**, font customization, dark/light themes, and export tools.

---

## 🚀 Key Features

### 1. 🛡️ AdSense & AdsKeeper Content Policy Auditor
- Automatically audits both the **Title** and **Article Body** upon fetching or editing.
- Generates a **Monetization Safety Score (0–100)** with clear categorization:
  - 🟢 **Safe & Monetizable**: 100% compliant with Google AdSense and AdsKeeper guidelines.
  - 🟡 **Caution / Moderate Sensitivity**: Review flagged drama or profanity terms.
  - 🔴 **High Risk / Policy Alert**: Flags prohibited adult, severe violence, or hate terms to protect accounts from ad bans.
- **Interactive Policy Report Dialog**:
  - Breakdown of detected policy keywords by severity.
  - **`🔍 Find in Text`** button automatically highlights flagged words directly in the reader for easy editing.

### 2. 📌 Separated Title & Clean Body Architecture
- **Article Title Card**: Isolated title with dedicated **`📋 Copy Title`** button.
- **Clean Article Body**: Contains **ONLY pure story text** without headers, URLs, or symbol dividers (`====`, `----`, `━━━━`).
- **Preserved Story Headings**: Retains all author headings (`<h1>`–`<h6>`), chapter markers, subtitles, dialog quotes, and narrative structure.
- **`📋 Copy Article`**: 1-click instant clipboard copy with visual feedback.
- **`🧹 Clean Text`**: Cleans pasted text from external sources.
- **Metadata Stats Strip**: Displays Part count, Word count, Reading time, and Source domain outside the article body.

### 3. 🌐 Supported Multi-Site Scraper Engine
- **America Focus (`america-focus.com`)**: Handles continuous pagination up to 97+ parts.
- **Human Heart Tales / Feji (`humanhearttales.feji.io`)**: Automatic slug progression (`full-story-...` to `part-2-...`, `part-3-...`).
- **Fanstopis (`fanstopis.com`)**: Scrapes `?part=2`, `?part=3` multi-part stories.
- **Levanews (`levanews.com`)**: Scrapes `?part=2`, `?part=3` multi-part stories.
- **1 Million Stories (`1millionstories.net`)**: Scrapes multi-part stories.
- **Kayle Store (`kaylestore.net`)**: Single-part long-form stories with full `<h1>`–`<h6>` header preservation.
- **Lead to Happiness (`leadtohappiness.com`)**: Single-part stories.
- **Top Thuy Sinh (`tv.topthuysinh.com`)**: Single-part stories.
- **Happy Soul Shop (`happysoulshop.com`)**: Single-part stories.
- **Universal Fallback**: Detects query, slash, or link-based pagination across any standard WordPress or news blog.

### 4. 🎨 Modern Windows UI & Reader Controls
- Built with **CustomTkinter** with seamless **Dark Mode** and **Light Mode** support.
- Live progress bar, Cancel/Stop button, and fast presets dropdown.
- Font family menu (**Georgia Serif**, **Segoe UI Sans**, **Consolas Mono**) and dynamic font scaling (`A-` / `A+`).
- Export formats: **Plain Text (`.txt`)**, **Markdown (`.md`)**, and styled offline **HTML Reader (`.html`)**.

---

## 📦 How to Install & Run

### 1. Run the Standalone Application (No Python Required)
Run the compiled standalone Windows executable directly:
- Double-click [`dist/MultiPageStoryReader.exe`](file:///c:/Users/Admin/Desktop/Aplikacioni%20per%20scraper/dist/MultiPageStoryReader.exe)

### 2. Run from Source Code (Python)
Ensure Python 3.10+ is installed:
```bash
pip install -r requirements.txt
python article_reader.py
```

### 3. Re-build the `.exe` Executable
To package your changes into a single-file executable anytime:
- Double-click `build_exe.bat`
- Or run:
```bash
pyinstaller --clean article_reader.spec
```

---

## 🧪 Testing

Run the automated test suites:
```bash
# Unit tests
python -m unittest test_scraper_engine.py

# Test across all 10 supported platforms
python test_all_target_sites.py
```

---

## 🏢 Author & License
- **Developed by**: DEA Innovations
- **Website**: [www.deainnovations.com](https://www.deainnovations.com)
- **Repository**: [github.com/edimonndi/multisitewebarticlescraper](https://github.com/edimonndi/multisitewebarticlescraper)
