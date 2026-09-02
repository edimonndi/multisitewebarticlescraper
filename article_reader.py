import ctypes
import os
import sys
import threading
import time
import webbrowser
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from adsense_analyzer import AdSensePolicyAnalyzer, PolicyAnalysisResult
from scraper_engine import StoryArticle, StoryScraper, clean_pure_text

# Enable Windows DPI awareness & Taskbar Icon grouping
try:
    if sys.platform == "win32":
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("deainnovations.storyscraper.pro.2")
except Exception:
    pass

# CustomTkinter Setup
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    try:
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class PolicyReportDialog(ctk.CTkToplevel):
    """Detailed AdSense & AdsKeeper Policy Audit Window"""

    def __init__(self, parent, analysis_result: PolicyAnalysisResult, on_highlight_word=None):
        super().__init__(parent)

        self.title("🛡️ AdSense & AdsKeeper Policy Auditor — DEA Pro")
        self.geometry("720x620")
        self.minsize(580, 480)
        self.transient(parent)

        icon_path = get_resource_path("app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.result = analysis_result
        self.on_highlight_word = on_highlight_word

        self._build_ui()
        self.focus_force()

    def _build_ui(self):
        # 1. Header Card with Score
        score_card = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        score_card.pack(fill="x", padx=20, pady=(16, 10))

        top_row = ctk.CTkFrame(score_card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=12)

        # Left: Big Score Pill
        score_box = ctk.CTkFrame(top_row, fg_color=self.result.status_color, corner_radius=10, width=90, height=75)
        score_box.pack(side="left", padx=(0, 16))
        score_box.pack_propagate(False)

        score_num = ctk.CTkLabel(
            score_box,
            text=f"{self.result.score}",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="#ffffff"
        )
        score_num.pack(expand=True, pady=(4, 0))

        score_sub = ctk.CTkLabel(
            score_box,
            text="/ 100",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#ffffff"
        )
        score_sub.pack(expand=True, pady=(0, 4))

        # Right: Verdicts
        verdict_box = ctk.CTkFrame(top_row, fg_color="transparent")
        verdict_box.pack(side="left", fill="x", expand=True)

        status_badge = ctk.CTkLabel(
            verdict_box,
            text=self.result.status_label,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=self.result.status_color
        )
        status_badge.pack(anchor="w")

        adsense_lbl = ctk.CTkLabel(
            verdict_box,
            text=f"Google AdSense: {self.result.adsense_verdict}",
            font=ctk.CTkFont(size=12),
            text_color=("#334155", "#cbd5e1"),
            wraplength=480,
            justify="left"
        )
        adsense_lbl.pack(anchor="w", pady=(2, 1))

        adskeeper_lbl = ctk.CTkLabel(
            verdict_box,
            text=f"AdsKeeper: {self.result.adskeeper_verdict}",
            font=ctk.CTkFont(size=12),
            text_color=("#334155", "#cbd5e1"),
            wraplength=480,
            justify="left"
        )
        adskeeper_lbl.pack(anchor="w")

        # 2. Risk Counts Strip
        counts_strip = ctk.CTkFrame(score_card, fg_color=("#e2e8f0", "#0f172a"), corner_radius=8)
        counts_strip.pack(fill="x", padx=16, pady=(0, 12))

        c_row = ctk.CTkFrame(counts_strip, fg_color="transparent")
        c_row.pack(fill="x", padx=12, pady=6)

        ctk.CTkLabel(c_row, text=f"🔴 High Risk (Ban Hazard): {self.result.high_risk_count}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef4444").pack(side="left", padx=(0, 14))
        ctk.CTkLabel(c_row, text=f"🟡 Medium (Policy Caution): {self.result.medium_risk_count}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#f59e0b").pack(side="left", padx=(0, 14))
        ctk.CTkLabel(c_row, text=f"🔵 Low (Drama/Contextual): {self.result.low_risk_count}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8").pack(side="left")

        # 3. Flagged Words List
        list_card = ctk.CTkFrame(self, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        list_card.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        list_header = ctk.CTkFrame(list_card, fg_color="transparent")
        list_header.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            list_header,
            text=f"Detected Policy Terms & Context ({self.result.total_flags} found):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1e293b", "#f8fafc")
        ).pack(side="left")

        scroll_area = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        scroll_area.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        if not self.result.flags:
            clean_msg = ctk.CTkLabel(
                scroll_area,
                text="🎉 Excellent! Zero prohibited or sensitive words detected.\n\nThis article is 100% compliant with Google AdSense and AdsKeeper policies.",
                font=ctk.CTkFont(size=13),
                text_color=("#10b981", "#34d399"),
                justify="center"
            )
            clean_msg.pack(pady=40)
        else:
            for flag in self.result.flags:
                self._create_flag_item(scroll_area, flag)

    def _create_flag_item(self, parent, flag):
        item_frame = ctk.CTkFrame(parent, fg_color=("#f8fafc", "#0f172a"), corner_radius=8, border_width=1, border_color=("#e2e8f0", "#334155"))
        item_frame.pack(fill="x", pady=4, padx=4)

        header_row = ctk.CTkFrame(item_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=10, pady=(8, 2))

        sev_color = "#ef4444" if flag.severity == "HIGH" else ("#f59e0b" if flag.severity == "MEDIUM" else "#38bdf8")
        sev_badge = ctk.CTkLabel(
            header_row,
            text=f"[{flag.severity}]",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#ffffff",
            fg_color=sev_color,
            corner_radius=4,
            padx=6,
            pady=1
        )
        sev_badge.pack(side="left", padx=(0, 8))

        word_lbl = ctk.CTkLabel(
            header_row,
            text=f"\"{flag.word_or_phrase}\" ({flag.match_count}x) — {flag.category_label}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        )
        word_lbl.pack(side="left")

        if self.on_highlight_word:
            h_btn = ctk.CTkButton(
                header_row,
                text="🔍 Find in Text",
                width=80,
                height=22,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=("#cbd5e1", "#334155"),
                text_color=("#0f172a", "#f8fafc"),
                hover_color=("#94a3b8", "#475569"),
                corner_radius=4,
                command=lambda w=flag.word_or_phrase: self._find_and_highlight(w)
            )
            h_btn.pack(side="right")

        if flag.context_snippets:
            snippet_box = ctk.CTkFrame(item_frame, fg_color="transparent")
            snippet_box.pack(fill="x", padx=10, pady=(2, 8))
            for snip in flag.context_snippets:
                snip_lbl = ctk.CTkLabel(
                    snippet_box,
                    text=f"• \"{snip}\"",
                    font=ctk.CTkFont(family="Georgia", size=11, slant="italic"),
                    text_color=("#475569", "#94a3b8"),
                    wraplength=600,
                    justify="left"
                )
                snip_lbl.pack(anchor="w", pady=1)

    def _find_and_highlight(self, word: str):
        if self.on_highlight_word:
            self.on_highlight_word(word)


class StoryScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DEA Story Scraper & Reader Pro")
        self.geometry("1160x890")
        self.minsize(920, 690)

        # Set Window Icon
        icon_path = get_resource_path("app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Engines State
        self.policy_analyzer = AdSensePolicyAnalyzer()
        self.last_analysis: Optional[PolicyAnalysisResult] = None
        self.current_article: Optional[StoryArticle] = None
        self.scrape_thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.is_scraping = False

        # Reader Settings State
        self.font_size = 15
        self.font_family = "Georgia"

        # Build UI
        self._create_header()
        self._create_input_card()
        self._create_progress_bar()
        self._create_stats_toolbar()
        self._create_title_section()
        self._create_article_body_section()
        self._create_footer()

        # Keyboard shortcuts
        self.bind("<Control-v>", lambda e: self._paste_url())
        self.bind("<Control-c>", lambda e: None)
        self.bind("<Return>", lambda e: self.start_scrape())

    # ================= UI COMPONENTS =================

    def _create_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(14, 6))

        # Brand / Title
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        brand_label = ctk.CTkLabel(
            title_box,
            text="DEA STORY SCRAPER & READER",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=("#1e293b", "#38bdf8"),
        )
        brand_label.pack(side="left", padx=(0, 10))

        badge = ctk.CTkLabel(
            title_box,
            text="PRO v2.0",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=("#2563eb", "#1d4ed8"),
            text_color="#ffffff",
            corner_radius=6,
            padx=8,
            pady=2,
        )
        badge.pack(side="left")

        # Controls (Theme + Font Adjustments)
        ctrl_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        ctrl_box.pack(side="right")

        font_box = ctk.CTkFrame(ctrl_box, fg_color=("#e2e8f0", "#1e293b"), corner_radius=8)
        font_box.pack(side="left", padx=8)

        ctk.CTkLabel(font_box, text="Font:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#64748b", "#94a3b8")).pack(side="left", padx=(10, 4))

        self.font_family_menu = ctk.CTkOptionMenu(
            font_box,
            values=["Georgia (Serif)", "Segoe UI (Sans)", "Consolas (Mono)"],
            command=self._change_font_family,
            width=130,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=("#cbd5e1", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            button_color=("#94a3b8", "#475569")
        )
        self.font_family_menu.set("Georgia (Serif)")
        self.font_family_menu.pack(side="left", padx=4, pady=3)

        btn_font_dec = ctk.CTkButton(
            font_box, text="A-", width=28, height=26, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#cbd5e1", "#334155"), text_color=("#0f172a", "#f8fafc"), hover_color=("#94a3b8", "#475569"),
            command=self._decrease_font_size
        )
        btn_font_dec.pack(side="left", padx=2, pady=3)

        self.font_size_label = ctk.CTkLabel(font_box, text=f"{self.font_size}pt", width=36, font=ctk.CTkFont(size=11, weight="bold"))
        self.font_size_label.pack(side="left", padx=2)

        btn_font_inc = ctk.CTkButton(
            font_box, text="A+", width=28, height=26, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#cbd5e1", "#334155"), text_color=("#0f172a", "#f8fafc"), hover_color=("#94a3b8", "#475569"),
            command=self._increase_font_size
        )
        btn_font_inc.pack(side="left", padx=(2, 6), pady=3)

        self.theme_btn = ctk.CTkButton(
            ctrl_box,
            text="☀️ Light",
            width=75,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#e2e8f0", "#1e293b"),
            text_color=("#0f172a", "#f8fafc"),
            hover_color=("#cbd5e1", "#334155"),
            corner_radius=8,
            command=self._toggle_theme,
        )
        self.theme_btn.pack(side="left")

    def _create_input_card(self):
        card = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        card.pack(fill="x", padx=24, pady=6)

        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            row1,
            text="Article / Story URL:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#334155", "#94a3b8")
        ).pack(anchor="w", pady=(0, 4))

        input_row = ctk.CTkFrame(row1, fg_color="transparent")
        input_row.pack(fill="x")

        self.url_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Enter story URL (e.g. america-focus.com, feji.io, fanstopis.com, levanews.com, kaylestore.net, leadtohappiness.com, 1millionstories.net)...",
            height=38,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            border_width=1,
            border_color=("#cbd5e1", "#475569")
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        paste_btn = ctk.CTkButton(
            input_row,
            text="📋 Paste",
            width=78,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            corner_radius=8,
            command=self._paste_url
        )
        paste_btn.pack(side="left", padx=(0, 6))

        clear_btn = ctk.CTkButton(
            input_row,
            text="✕",
            width=38,
            height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#cbd5e1", "#334155"),
            text_color=("#475569", "#cbd5e1"),
            hover_color=("#94a3b8", "#475569"),
            corner_radius=8,
            command=self._clear_url
        )
        clear_btn.pack(side="left")

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 12))

        self.fetch_btn = ctk.CTkButton(
            row2,
            text="⚡ Fetch Full Story",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            corner_radius=8,
            command=self.start_scrape
        )
        self.fetch_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            row2,
            text="⏹ Stop",
            width=80,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            corner_radius=8,
            state="disabled",
            command=self.stop_scrape
        )
        self.stop_btn.pack(side="left", padx=(0, 15))

        preset_label = ctk.CTkLabel(
            row2,
            text="Quick Examples:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        )
        preset_label.pack(side="left", padx=(10, 6))

        self.preset_menu = ctk.CTkOptionMenu(
            row2,
            values=[
                "Select a sample URL...",
                "America Focus (97 Parts)",
                "Feji Stories (9 Parts)",
                "Fanstopis (3 Parts)",
                "Levanews (3 Parts)",
                "1 Million Stories (3 Parts)",
                "Kayle Store (1 Part)",
                "Lead to Happiness (1 Part)",
                "Happy Soul Shop (1 Part)",
            ],
            command=self._load_preset_url,
            width=195,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=("#cbd5e1", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            button_color=("#94a3b8", "#475569")
        )
        self.preset_menu.pack(side="left")

    def _create_progress_bar(self):
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=24, pady=(2, 4))

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            height=5,
            corner_radius=3,
            fg_color=("#e2e8f0", "#1e293b"),
            progress_color=("#38bdf8", "#0284c7")
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 3))

        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="Ready. Enter an article URL above and click 'Fetch Full Story'.",
            font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8")
        )
        self.status_label.pack(anchor="w")

    def _create_stats_toolbar(self):
        self.toolbar_frame = ctk.CTkFrame(self, fg_color=("#f8fafc", "#0f172a"), corner_radius=10, border_width=1, border_color=("#e2e8f0", "#334155"))
        self.toolbar_frame.pack(fill="x", padx=24, pady=(4, 6))

        self.meta_box = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        self.meta_box.pack(side="left", padx=12, pady=6)

        self.stats_label = ctk.CTkLabel(
            self.meta_box,
            text="📊 Info: No story loaded yet",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#64748b", "#94a3b8")
        )
        self.stats_label.pack(side="left", padx=(0, 10))

        self.safety_badge = ctk.CTkButton(
            self.meta_box,
            text="🛡️ AdSense: Ready to Audit",
            width=175,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#e2e8f0", "#1e293b"),
            text_color=("#64748b", "#94a3b8"),
            hover_color=("#cbd5e1", "#334155"),
            corner_radius=6,
            command=self.open_policy_report
        )
        self.safety_badge.pack(side="left")

        btn_box = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        btn_box.pack(side="right", padx=12, pady=6)

        self.save_txt_btn = ctk.CTkButton(
            btn_box,
            text="💾 Save TXT",
            width=88,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#cbd5e1", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            hover_color=("#94a3b8", "#475569"),
            corner_radius=6,
            command=self.save_as_txt
        )
        self.save_txt_btn.pack(side="left", padx=3)

        self.save_md_btn = ctk.CTkButton(
            btn_box,
            text="📄 Save MD",
            width=84,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#cbd5e1", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            hover_color=("#94a3b8", "#475569"),
            corner_radius=6,
            command=self.save_as_markdown
        )
        self.save_md_btn.pack(side="left", padx=3)

        self.save_html_btn = ctk.CTkButton(
            btn_box,
            text="🌐 Save HTML",
            width=92,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#cbd5e1", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            hover_color=("#94a3b8", "#475569"),
            corner_radius=6,
            command=self.save_as_html
        )
        self.save_html_btn.pack(side="left", padx=3)

    def _create_title_section(self):
        title_card = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#1e293b"), corner_radius=10, border_width=1, border_color=("#e2e8f0", "#334155"))
        title_card.pack(fill="x", padx=24, pady=(2, 6))

        top_row = ctk.CTkFrame(title_card, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(8, 4))

        ctk.CTkLabel(
            top_row,
            text="📌 Article Title:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#2563eb", "#38bdf8")
        ).pack(side="left")

        self.copy_title_btn = ctk.CTkButton(
            top_row,
            text="📋 Copy Title",
            width=100,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            corner_radius=6,
            command=self.copy_title_to_clipboard
        )
        self.copy_title_btn.pack(side="right")

        self.title_entry = ctk.CTkEntry(
            title_card,
            placeholder_text="Story title will appear here...",
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            corner_radius=6,
            border_width=1,
            border_color=("#cbd5e1", "#475569")
        )
        self.title_entry.pack(fill="x", padx=14, pady=(0, 10))

    def _create_article_body_section(self):
        body_card = ctk.CTkFrame(self, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        body_card.pack(fill="both", expand=True, padx=24, pady=(2, 8))

        body_toolbar = ctk.CTkFrame(body_card, fg_color="transparent")
        body_toolbar.pack(fill="x", padx=16, pady=(10, 6))

        ctk.CTkLabel(
            body_toolbar,
            text="📖 Clean Article Body:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#334155", "#cbd5e1")
        ).pack(side="left")

        btn_group = ctk.CTkFrame(body_toolbar, fg_color="transparent")
        btn_group.pack(side="right")

        self.audit_btn = ctk.CTkButton(
            btn_group,
            text="🛡️ Audit Policy",
            width=105,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#8b5cf6", "#7c3aed"),
            hover_color=("#7c3aed", "#6d28d9"),
            corner_radius=6,
            command=self.open_policy_report
        )
        self.audit_btn.pack(side="left", padx=4)

        self.clean_btn = ctk.CTkButton(
            btn_group,
            text="🧹 Clean Text",
            width=100,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#f59e0b", "#d97706"),
            hover_color=("#d97706", "#b45309"),
            corner_radius=6,
            command=self.clean_text_action
        )
        self.clean_btn.pack(side="left", padx=4)

        self.copy_article_btn = ctk.CTkButton(
            btn_group,
            text="📋 Copy Article",
            width=115,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            corner_radius=6,
            command=self.copy_article_to_clipboard
        )
        self.copy_article_btn.pack(side="left", padx=4)

        self.text_area = ctk.CTkTextbox(
            body_card,
            wrap="word",
            font=ctk.CTkFont(family=self.font_family, size=self.font_size),
            corner_radius=10,
            fg_color="transparent",
            text_color=("#0f172a", "#f8fafc"),
            padx=20,
            pady=16,
        )
        self.text_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.text_area.insert(
            "1.0",
            "Welcome to DEA Story Scraper & Reader Pro with AdSense Policy Auditor!\n\n"
            "Features:\n"
            "• Title & Body are displayed separately for convenient 1-click copying.\n"
            "• Zero advertisements, zero divider lines (====, ----, ━━━━), and zero clutter.\n"
            "• Section and Chapter headers are preserved naturally.\n"
            "• Built-in AdSense & AdsKeeper Policy Auditor checks for prohibited or risky monetization words.\n\n"
            "Paste a story URL above and click '⚡ Fetch Full Story' to begin!"
        )

    def _create_footer(self):
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=24, pady=(0, 10))

        brand_text = ctk.CTkLabel(
            footer_frame,
            text="Developed by DEA Innovations  •  ",
            font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"),
        )
        brand_text.pack(side="left")

        link_label = ctk.CTkLabel(
            footer_frame,
            text="www.deainnovations.com",
            font=ctk.CTkFont(size=12, weight="bold", underline=True),
            text_color=("#2563eb", "#38bdf8"),
            cursor="hand2"
        )
        link_label.pack(side="left")
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://www.deainnovations.com"))

        ready_label = ctk.CTkLabel(
            footer_frame,
            text="AdSense & AdsKeeper Policy Safety Shield Active",
            font=ctk.CTkFont(size=11),
            text_color=("#94a3b8", "#64748b")
        )
        ready_label.pack(side="right")

    # ================= LOGIC & ACTIONS =================

    def _paste_url(self):
        try:
            clipboard = self.clipboard_get().strip()
            if clipboard:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, clipboard)
        except Exception:
            pass

    def _clear_url(self):
        self.url_entry.delete(0, "end")

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current.lower() == "dark":
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(text="🌙 Dark")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(text="☀️ Light")

    def _increase_font_size(self):
        if self.font_size < 28:
            self.font_size += 2
            self._update_reader_font()

    def _decrease_font_size(self):
        if self.font_size > 11:
            self.font_size -= 2
            self._update_reader_font()

    def _change_font_family(self, choice: str):
        if "Serif" in choice:
            self.font_family = "Georgia"
        elif "Mono" in choice:
            self.font_family = "Consolas"
        else:
            self.font_family = "Segoe UI"
        self._update_reader_font()

    def _update_reader_font(self):
        self.font_size_label.configure(text=f"{self.font_size}pt")
        self.text_area.configure(font=ctk.CTkFont(family=self.font_family, size=self.font_size))

    def _load_preset_url(self, choice: str):
        presets = {
            "America Focus (97 Parts)": "https://america-focus.com/a-battered-suitcase-on-my-kitchen-floor-ended-my-twenty-three-year-marriage/",
            "Feji Stories (9 Parts)": "https://humanhearttales.feji.io/full-story-she-stole-my-wedding-dress-then-the-security-footage-started-playing/",
            "Fanstopis (3 Parts)": "https://fanstopis.com/my-wife-was-about-to-be-burie",
            "Levanews (3 Parts)": "https://levanews.com/hours-after-my-divorce-became-final-my-former-mother-in-law-tried-to-charge-a-48000-auction-purchase-to-my-credit-card-but-i-had-already-canceled-it-by-the-next-morning-my-ex-husband-was-having/",
            "1 Million Stories (3 Parts)": "https://1millionstories.net/minutes-before-my-brain-surgery-my-husband-leaned-close-and-admitted-your-friend-and-i-have-a-nine-year-old-daughter-he-was-counting-on-the-operation-erasing-my-memory-a/",
            "Kayle Store (1 Part)": "https://kaylestore.net/my-husband-reserved-seats-7a-and-7b-to-escape-with-another-woman-but-he-forgot-that-after-12-years-i-knew-every-one-of-his-lies/",
            "Lead to Happiness (1 Part)": "https://leadtohappiness.com/stay-with-the-doctors-im-choosing-her-my-husband-left-me-bl%f0%9f%87%aaeding-in-the-er-to-chase-his-mistress-then-he-returned-to-an-empty-bay-and-learned-th/",
            "Happy Soul Shop (1 Part)": "https://happysoulshop.com/we-adopted-a-girl-in-a-wheelchair-but-her-first-words-about-our-basement-left-us-frozen/",
        }
        if choice in presets:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, presets[choice])

    def start_scrape(self):
        url = self.url_entry.get().strip().strip("'\"<> ")
        if not url:
            messagebox.showwarning("Missing URL", "Please enter or paste a valid story URL first.")
            return

        if self.is_scraping:
            return

        self.is_scraping = True
        self.cancel_event.clear()
        self.current_article = None

        # Clean UI state for new scrape
        self.fetch_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="Connecting to website...", text_color=("#2563eb", "#38bdf8"))
        self.stats_label.configure(text="📊 Info: Fetching story...", text_color=("#64748b", "#94a3b8"))
        self.safety_badge.configure(
            text="🛡️ Auditing Policy...",
            fg_color=("#e2e8f0", "#1e293b"),
            text_color=("#64748b", "#94a3b8")
        )
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, "Fetching title...")
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", "⏳ Fetching and cleaning story parts... Please wait a moment.\n")

        # Launch scraper thread
        self.scrape_thread = threading.Thread(target=self._scrape_worker, args=(url,), daemon=True)
        self.scrape_thread.start()

    def stop_scrape(self):
        if self.is_scraping:
            self.cancel_event.set()
            self.status_label.configure(text="Stopping scraper...", text_color=("#dc2626", "#f87171"))
            self.stop_btn.configure(state="disabled")

    def _scrape_worker(self, url: str):
        start_time = time.time()
        scraper = StoryScraper()

        def progress_cb(msg: str, part_num: int, total_est: int, pct: float):
            self.after(0, self._update_progress, msg, part_num, total_est, pct)

        try:
            article = scraper.scrape(url, progress_callback=progress_cb, cancel_event=self.cancel_event)
            elapsed = time.time() - start_time
            self.after(0, self._on_scrape_success, article, elapsed)
        except Exception as e:
            self.after(0, self._on_scrape_error, str(e))

    def _update_progress(self, msg: str, part_num: int, total_est: int, pct: float):
        self.status_label.configure(text=msg, text_color=("#2563eb", "#38bdf8"))
        if total_est > 0 and pct > 0:
            self.progress_bar.set(min(1.0, pct))
        else:
            current = self.progress_bar.get()
            self.progress_bar.set((current + 0.05) % 1.0)

    def _on_scrape_success(self, article: StoryArticle, elapsed: float):
        self.is_scraping = False
        self.current_article = article
        self.fetch_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_bar.set(1.0)

        # 1. Update Separate Title Box
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, article.title)

        # 2. Update Stats Toolbar
        meta_text = (
            f"📖 {article.total_parts} Parts  |  "
            f"📝 {article.total_words:,} Words  |  "
            f"⏱️ ~{article.reading_time_minutes} Min Read  |  "
            f"🌐 Source: {article.domain}"
        )
        self.stats_label.configure(text=meta_text, text_color=("#10b981", "#34d399"))

        # 3. Populate Clean Article Body Text Box (Preserving section headers, no divider lines)
        self.text_area.delete("1.0", "end")
        clean_body = article.to_pure_body()
        self.text_area.insert("1.0", clean_body)

        # 4. Run AdSense & AdsKeeper Policy Analysis
        self._run_policy_analysis(article.title, clean_body)

        # 5. Update Status Bar
        self.status_label.configure(
            text=f"✅ Completed in {elapsed:.1f}s — Loaded {article.total_parts} parts. Policy Score: {self.last_analysis.score}/100",
            text_color=("#10b981", "#34d399")
        )

    def _on_scrape_error(self, err_msg: str):
        self.is_scraping = False
        self.current_article = None
        self.fetch_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_bar.set(0)

        self.title_entry.delete(0, "end")
        self.stats_label.configure(text="📊 Info: No story loaded (Fetch error)", text_color=("#dc2626", "#f87171"))
        self.safety_badge.configure(
            text="🛡️ AdSense: Ready to Audit",
            fg_color=("#e2e8f0", "#1e293b"),
            text_color=("#64748b", "#94a3b8")
        )
        self.status_label.configure(text=f"❌ Error: {err_msg}", text_color=("#dc2626", "#f87171"))
        self.text_area.delete("1.0", "end")
        self.text_area.insert(
            "1.0",
            f"⚠️ Could not load story\n"
            f"{'-' * 40}\n\n"
            f"Details: {err_msg}\n\n"
            f"Suggestions:\n"
            f"• Verify the entire URL was copied (some URLs get cut off on social media).\n"
            f"• Check that your internet connection is active and the website is reachable."
        )

    def _run_policy_analysis(self, title: str, body: str):
        """Audits the title and body for AdSense & AdsKeeper content safety."""
        analysis = self.policy_analyzer.analyze(title, body)
        self.last_analysis = analysis

        if analysis.status == "SAFE":
            badge_text = f"🛡️ AdSense Safe: {analysis.score}/100 ✅"
            fg_col = ("#d1fae5", "#064e3b")
            text_col = ("#065f46", "#34d399")
        elif analysis.status == "CAUTION":
            badge_text = f"🛡️ AdSense Caution: {analysis.score}/100 ⚠️"
            fg_col = ("#fef3c7", "#78350f")
            text_col = ("#92400e", "#fde68a")
        else:
            badge_text = f"🛡️ AdSense Risk: {analysis.score}/100 🚫"
            fg_col = ("#fee2e2", "#7f1d1d")
            text_col = ("#991b1b", "#fca5a5")

        self.safety_badge.configure(
            text=badge_text,
            fg_color=fg_col,
            text_color=text_col,
            hover_color=("#cbd5e1", "#334155")
        )

    def open_policy_report(self):
        """Opens the full AdSense & AdsKeeper Policy Auditor window."""
        title = self.title_entry.get().strip()
        body = self.text_area.get("1.0", "end").strip()

        self._run_policy_analysis(title, body)

        if not self.last_analysis:
            messagebox.showinfo("Policy Auditor", "Please fetch or enter a story first to run the policy audit.")
            return

        PolicyReportDialog(self, self.last_analysis, on_highlight_word=self.highlight_word_in_reader)

    def highlight_word_in_reader(self, word: str):
        """Highlights instances of a flagged word in the text area."""
        self.text_area.tag_remove("highlight", "1.0", "end")
        if not word:
            return

        self.text_area._textbox.tag_configure("highlight", background="#f59e0b", foreground="#000000")

        start_pos = "1.0"
        first_match = None
        while True:
            start_pos = self.text_area._textbox.search(word, start_pos, stopindex="end", nocase=True)
            if not start_pos:
                break
            if not first_match:
                first_match = start_pos
            end_pos = f"{start_pos}+{len(word)}c"
            self.text_area._textbox.tag_add("highlight", start_pos, end_pos)
            start_pos = end_pos

        if first_match:
            self.text_area._textbox.see(first_match)
            self.status_label.configure(
                text=f"🔍 Highlighted occurrences of '{word}' in the reader.",
                text_color=("#f59e0b", "#fbbf24")
            )

    def copy_title_to_clipboard(self):
        """Copies ONLY the article title."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showinfo("Empty", "No title to copy.")
            return

        self.clipboard_clear()
        self.clipboard_append(title)

        prev_text = self.copy_title_btn.cget("text")
        self.copy_title_btn.configure(text="✓ Copied!", fg_color=("#10b981", "#059669"))
        self.after(1600, lambda: self.copy_title_btn.configure(text=prev_text, fg_color=("#3b82f6", "#2563eb")))

    def copy_article_to_clipboard(self):
        """Copies ONLY the clean article story body (preserving section headers)."""
        content = self.text_area.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Empty", "No article body text to copy.")
            return

        cleaned_content = clean_pure_text(content)

        self.clipboard_clear()
        self.clipboard_append(cleaned_content)

        prev_text = self.copy_article_btn.cget("text")
        self.copy_article_btn.configure(text="✓ Copied Article!", fg_color=("#10b981", "#059669"))
        self.after(1800, lambda: self.copy_article_btn.configure(text=prev_text, fg_color=("#10b981", "#059669")))

    def clean_text_action(self):
        """Cleans the body text area, removing divider lines and ads while PRESERVING section/chapter headers."""
        content = self.text_area.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Empty", "No text in the body to clean.")
            return

        cleaned = clean_pure_text(content)
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", cleaned)

        self._run_policy_analysis(self.title_entry.get().strip(), cleaned)

        prev_text = self.clean_btn.cget("text")
        self.clean_btn.configure(text="✓ Cleaned!", fg_color=("#10b981", "#059669"))
        self.status_label.configure(
            text="✨ Cleaned body: Removed divider lines & ads (Story and chapter titles preserved).",
            text_color=("#10b981", "#34d399")
        )
        self.after(1800, lambda: self.clean_btn.configure(text=prev_text, fg_color=("#f59e0b", "#d97706")))

    def save_as_txt(self):
        content = self.text_area.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("No Story", "Please fetch a story before saving.")
            return

        title = self.title_entry.get().strip() or "story"
        default_name = self._sanitize_filename(title) + ".txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"{title}\n\n{content}")
            messagebox.showinfo("Saved", f"Story saved successfully as Plain Text:\n{os.path.basename(file_path)}")

    def save_as_markdown(self):
        content = self.text_area.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("No Story", "Please fetch a story before saving.")
            return

        title = self.title_entry.get().strip() or "Story"
        if self.current_article:
            md_content = self.current_article.to_markdown()
        else:
            md_content = f"# {title}\n\n{content}"

        default_name = self._sanitize_filename(title) + ".md"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
            initialfile=default_name
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            messagebox.showinfo("Saved", f"Story saved successfully as Markdown:\n{os.path.basename(file_path)}")

    def save_as_html(self):
        if not self.current_article:
            messagebox.showwarning("No Story", "Please fetch a story before saving.")
            return

        default_name = self._sanitize_filename(self.current_article.title) + ".html"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=default_name
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.current_article.to_html(theme=ctk.get_appearance_mode().lower()))
            if messagebox.askyesno("Saved", f"Story saved as offline HTML reader:\n{os.path.basename(file_path)}\n\nWould you like to open it in your browser?"):
                webbrowser.open(f"file:///{os.path.abspath(file_path)}")

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        clean = re.sub(r'[\\/*?:"<>|]', "", name)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:80] or "story"


if __name__ == "__main__":
    app = StoryScraperApp()
    app.mainloop()