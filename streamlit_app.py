import html
import io
import json
import os
import re
import time
from typing import Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components

from adsense_analyzer import AdSensePolicyAnalyzer, PolicyAnalysisResult, POLICY_RULES
from scraper_engine import StoryArticle, StoryPart, StoryScraper, clean_pure_text

# Set Page Config - auto state collapses sidebar on mobile screens by default
st.set_page_config(
    page_title="DEA Story Scraper & Reader Pro",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="auto"
)


def highlight_text_in_html(body_text: str, target_word: Optional[str], active_index: int = 1) -> Tuple[str, int]:
    """
    Escapes HTML and highlights all occurrences of target_word.
    Distinguishes the active occurrence with prominent glow, white outline, #X/Y badge, and active ID.
    Returns (highlighted_html, total_matches).
    """
    if not body_text:
        return "", 0
    escaped_body = html.escape(body_text)
    if not target_word or not target_word.strip():
        return escaped_body, 0

    escaped_target = html.escape(target_word.strip())
    # Match whole word or exact pattern case-insensitively
    pattern = re.compile(rf"\b({re.escape(escaped_target)})\b", re.IGNORECASE)
    matches = list(pattern.finditer(escaped_body))
    if not matches:
        pattern = re.compile(re.escape(escaped_target), re.IGNORECASE)
        matches = list(pattern.finditer(escaped_body))

    total_matches = len(matches)
    if total_matches == 0:
        return escaped_body, 0

    # Ensure active_index is 1-indexed and clamped in range [1, total_matches]
    clamped_index = ((active_index - 1) % total_matches) + 1

    result = []
    last_pos = 0
    for idx, match in enumerate(matches, start=1):
        result.append(escaped_body[last_pos:match.start()])
        matched_text = match.group(0)
        
        if idx == clamped_index:
            # Active occurrence: bright pulsating glowing amber, white outline, and occurrence badge
            badge_html = f'<span style="font-size: 0.72em; background: #0f172a; color: #38bdf8; border-radius: 3px; padding: 1px 5px; margin-left: 5px; vertical-align: middle; border: 1px solid #38bdf8; letter-spacing: 0;">#{idx}/{total_matches}</span>'
            result.append(
                f'<mark id="active-highlight-mark" class="active-mark-glow" style="background-color: #f59e0b; color: #000000; font-weight: 900; border-radius: 5px; padding: 3px 8px; border: 2.5px solid #ffffff; display: inline-block; box-shadow: 0 0 20px rgba(245, 158, 11, 1); scroll-margin: 160px 0;">{matched_text}{badge_html}</mark>'
            )
        else:
            # Passive occurrence: softer highlight
            result.append(
                f'<mark class="passive-mark-soft" style="background-color: rgba(245, 158, 11, 0.35); color: #f8fafc; font-weight: 700; border-radius: 4px; padding: 2px 6px; border: 1px dashed rgba(245, 158, 11, 0.85); display: inline-block;">{matched_text}</mark>'
            )
        last_pos = match.end()
    
    result.append(escaped_body[last_pos:])
    return "".join(result), total_matches


def render_copy_button(text_to_copy: str, button_label: str = "📋 Copy", success_label: str = "✓ Copied!", key: str = "copy_btn", bg_color: str = "#2563eb"):
    """Renders a 1-click browser clipboard copy button with visual feedback."""
    escaped_json = json.dumps(text_to_copy)
    html_code = f"""
    <div style="margin: 0; padding: 0; width: 100%;">
        <button id="{key}" onclick="copyText_{key}()" style="
            width: 100%;
            background-color: {bg_color};
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            text-align: center;
        ">
            {button_label}
        </button>
        <script>
            function copyText_{key}() {{
                var text = {escaped_json};
                if (navigator.clipboard && window.isSecureContext) {{
                    navigator.clipboard.writeText(text).then(function() {{
                        showCopied_{key}();
                    }}, function() {{
                        fallbackCopy_{key}(text);
                    }});
                }} else {{
                    fallbackCopy_{key}(text);
                }}
            }}
            function fallbackCopy_{key}(text) {{
                var textArea = document.createElement("textarea");
                textArea.value = text;
                textArea.style.position = "fixed";
                textArea.style.left = "-999999px";
                textArea.style.top = "-999999px";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {{
                    document.execCommand('copy');
                    showCopied_{key}();
                }} catch (err) {{
                    console.error('Copy failed', err);
                }}
                document.body.removeChild(textArea);
            }}
            function showCopied_{key}() {{
                var btn = document.getElementById("{key}");
                if (btn) {{
                    var orig = btn.innerHTML;
                    var origBg = btn.style.backgroundColor;
                    btn.innerHTML = "{success_label}";
                    btn.style.backgroundColor = "#10b981";
                    setTimeout(function() {{
                        btn.innerHTML = orig;
                        btn.style.backgroundColor = origBg;
                    }}, 2200);
                }}
            }}
        </script>
    </div>
    """
    components.html(html_code, height=44)


# Custom CSS for modern UI design and reader aesthetics
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0284c7 0%, #38bdf8 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.6rem !important;
        }
        .metric-val {
            font-size: 1.2rem !important;
        }
    }
    .sub-header {
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(51, 65, 85, 0.8);
        border-radius: 12px;
        padding: 14px 18px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .metric-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .story-title-banner {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f8fafc;
        padding: 12px 18px;
        background: rgba(30, 41, 59, 0.8);
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        margin: 1.2rem 0;
    }
    .footer-box {
        text-align: center;
        padding: 24px 0 10px 0;
        font-size: 0.85rem;
        color: #64748b;
        border-top: 1px solid rgba(51, 65, 85, 0.5);
        margin-top: 40px;
    }
    .footer-box a {
        color: #38bdf8;
        text-decoration: none;
        font-weight: 600;
    }
    @keyframes pulseActiveMark {
        0% {
            box-shadow: 0 0 10px rgba(245, 158, 11, 0.9), 0 0 20px rgba(245, 158, 11, 0.5);
            border-color: #ffffff;
        }
        50% {
            box-shadow: 0 0 25px rgba(245, 158, 11, 1), 0 0 45px rgba(251, 191, 36, 0.95);
            border-color: #38bdf8;
        }
        100% {
            box-shadow: 0 0 10px rgba(245, 158, 11, 0.9), 0 0 20px rgba(245, 158, 11, 0.5);
            border-color: #ffffff;
        }
    }
    .active-mark-glow {
        animation: pulseActiveMark 1.5s infinite ease-in-out !important;
        scroll-margin: 160px 0 !important;
    }
    .passive-mark-soft {
        scroll-margin: 160px 0 !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "article" not in st.session_state:
    st.session_state.article = None
if "policy_result" not in st.session_state:
    st.session_state.policy_result = None
if "edited_title" not in st.session_state:
    st.session_state.edited_title = ""
if "cleaned_body" not in st.session_state:
    st.session_state.cleaned_body = ""
if "highlight_word" not in st.session_state:
    st.session_state.highlight_word = None
if "highlight_index" not in st.session_state:
    st.session_state.highlight_index = 1


# ================= SIDEBAR CONTROLS =================
with st.sidebar:
    st.image("app_icon.png" if os.path.exists("app_icon.png") else "https://raw.githubusercontent.com/edimonndi/multisitewebarticlescraper/main/app_icon.png", width=64)
    st.title("Settings & Options")
    
    st.markdown("---")
    st.subheader("⚡ Quick Example URLs")
    sample_presets = {
        "Select a sample URL...": "",
        "America Focus (97 Parts)": "https://america-focus.com/a-battered-suitcase-on-my-kitchen-floor-ended-my-twenty-three-year-marriage/",
        "Feji Stories (9 Parts)": "https://humanhearttales.feji.io/full-story-she-stole-my-wedding-dress-then-the-security-footage-started-playing/",
        "Fanstopis (3 Parts)": "https://fanstopis.com/my-wife-was-about-to-be-burie",
        "Levanews (3 Parts)": "https://levanews.com/hours-after-my-divorce-became-final-my-former-mother-in-law-tried-to-charge-a-48000-auction-purchase-to-my-credit-card-but-i-had-already-canceled-it-by-the-next-morning-my-ex-husband-was-having/",
        "1 Million Stories (3 Parts)": "https://1millionstories.net/minutes-before-my-brain-surgery-my-husband-leaned-close-and-admitted-your-friend-and-i-have-a-nine-year-old-daughter-he-was-counting-on-the-operation-erasing-my-memory-a/",
        "Kayle Store (1 Part)": "https://kaylestore.net/my-husband-reserved-seats-7a-and-7b-to-escape-with-another-woman-but-he-forgot-that-after-12-years-i-knew-every-one-of-his-lies/",
        "Lead to Happiness (1 Part)": "https://leadtohappiness.com/stay-with-the-doctors-im-choosing-her-my-husband-left-me-bl%f0%9f%87%aaeding-in-the-er-to-chase-his-mistress-then-he-returned-to-an-empty-bay-and-learned-th/",
        "The Celebritist (1 Part)": "https://thecelebritist.com/i-lost-my-daughter-last-year-five/",
        "Aliacar News (1 Part)": "https://aliacar.net.tr/husbands-with-these-2-bad-habits-may-put-their-wives-at-higher-risk-of-breast-cancer-stop-them-now-before-they-harm-the-whole-family/",
        "Happy Soul Shop (1 Part)": "https://happysoulshop.com/we-adopted-a-girl-in-a-wheelchair-but-her-first-words-about-our-basement-left-us-frozen/",
        "AmoMedia (1 Part)": "https://amomedia.com/661995-my-fiancee-kept-assuring-me-that-she.html",
        "LaptopsVilla (2 Parts)": "https://laptopsvilla.com/25-instances-where-the-simpsons-anticipated-the-future/",
    }
    selected_preset = st.selectbox("Load Target Preset", list(sample_presets.keys()))
    preset_url_val = sample_presets[selected_preset] if selected_preset != "Select a sample URL..." else ""

    st.markdown("---")
    st.subheader("🌐 Proxy & Geo-Unblock")
    use_proxy = st.checkbox("Enable Proxy Routing", value=False, help="Route scraping requests through an HTTP/SOCKS5 proxy to bypass regional geo-blocks and firewall timeouts (e.g. Levanews).")
    proxy_address = st.text_input("Proxy Address / URL", placeholder="e.g. http://127.0.0.1:8080 or socks5://...", disabled=not use_proxy)
    
    if use_proxy and proxy_address:
        if st.button("🧪 Test Proxy Connection", use_container_width=True):
            with st.spinner("Testing proxy connection..."):
                ok, msg = StoryScraper.test_proxy_connection(proxy_address)
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

    st.markdown("---")
    st.subheader("📖 Reader Style")
    font_choice = st.selectbox("Reading Font", ["Georgia (Serif)", "Segoe UI (Sans-Serif)", "Consolas (Monospace)"])
    font_family_css = "Georgia, serif" if "Georgia" in font_choice else ("'Segoe UI', sans-serif" if "Segoe" in font_choice else "Consolas, monospace")
    font_size = st.slider("Font Size (px)", min_value=14, max_value=24, value=18, step=1)

    st.markdown("---")
    st.markdown("""
    **DEA Story Scraper & Reader Pro**  
    Developed by [DEA Innovations](https://www.deainnovations.com)  
    • by [github.com/edimonndi](https://github.com/edimonndi)
    """)


# ================= MAIN APP HEADER =================
st.markdown('<div class="main-header">📖 DEA Story Scraper & Reader Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-Page Article Extraction, Automated Text Cleaning & AdSense Policy Safety Shield</div>', unsafe_allow_html=True)


# ================= INPUT TABS =================
tab1, tab2 = st.tabs(["⚡ URL Scraper", "📝 Manual Paste & Clean"])

# Tab 1: URL Scraper
with tab1:
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        input_url = st.text_input(
            "Enter Story URL:",
            value=preset_url_val,
            placeholder="https://america-focus.com/... or laptopsvilla.com, feji.io, fanstopis.com, levanews.com, kaylestore.net...",
            label_visibility="collapsed"
        )
    with col_btn:
        scrape_clicked = st.button("⚡ Fetch Story", type="primary", use_container_width=True)

    if scrape_clicked:
        if not input_url.strip():
            st.warning("⚠️ Please enter or select a story URL first.")
        else:
            progress_bar = st.progress(0, text="Connecting to website...")
            status_placeholder = st.empty()
            
            def progress_cb(msg: str, part_num: int, total_est: int, pct: float):
                clamped_pct = max(0.0, min(1.0, pct)) if total_est > 0 else 0.5
                progress_bar.progress(clamped_pct, text=msg)
                status_placeholder.info(f"⏳ {msg}")

            try:
                active_proxy = proxy_address.strip() if use_proxy and proxy_address.strip() else None
                scraper = StoryScraper(proxy=active_proxy)
                
                start_time = time.time()
                article = scraper.scrape(input_url, progress_callback=progress_cb)
                elapsed = time.time() - start_time
                
                progress_bar.progress(1.0, text=f"✅ Completed in {elapsed:.1f}s!")
                status_placeholder.success(f"✅ Successfully scraped {article.total_parts} part(s) and {article.total_words:,} words in {elapsed:.1f} seconds!")

                st.session_state.article = article
                st.session_state.edited_title = article.title
                st.session_state.cleaned_body = article.to_pure_body()
                st.session_state.highlight_word = None
                st.session_state.highlight_index = 1

                # Audit Policy
                analyzer = AdSensePolicyAnalyzer()
                st.session_state.policy_result = analyzer.analyze(article.title, st.session_state.cleaned_body)
                
            except Exception as e:
                progress_bar.empty()
                status_placeholder.error(f"❌ Scrape Error: {str(e)}")
                if "timeout" in str(e).lower() or "connection" in str(e).lower() or "403" in str(e).lower():
                    st.info("💡 **Tip:** If this website blocks your country/server IP (e.g. Levanews), enable Proxy Routing in the sidebar settings.")

# Tab 2: Manual Paste
with tab2:
    st.markdown("Paste raw text below (from documents, manual copies, or websites) to format, calculate metrics, audit for AdSense policy, and export.")
    manual_title_input = st.text_input("Story Title (Optional):", value=st.session_state.edited_title or "Untitled Story")
    manual_body_input = st.text_area("Paste Story Text:", height=220, placeholder="Paste your raw story text here...")
    
    if st.button("🧹 Clean Text & Audit Story", type="primary"):
        if not manual_body_input.strip():
            st.warning("⚠️ Please paste some story text first.")
        else:
            cleaned = clean_pure_text(manual_body_input)
            cleaned = StoryScraper.clean_text(cleaned)
            
            paras = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
            if not paras:
                paras = [cleaned]

            title = manual_title_input.strip() or "Untitled Story"
            synthetic_article = StoryArticle(
                title=title,
                original_url="Manual Paste",
                domain="Manual Paste",
                parts=[StoryPart(part_num=1, url="Manual Paste", paragraphs=paras)]
            )

            st.session_state.article = synthetic_article
            st.session_state.edited_title = title
            st.session_state.cleaned_body = cleaned
            st.session_state.highlight_word = None
            st.session_state.highlight_index = 1

            analyzer = AdSensePolicyAnalyzer()
            st.session_state.policy_result = analyzer.analyze(title, cleaned)
            st.success("✨ Story cleaned, formatted, and policy audited successfully!")


# ================= STORY DISPLAY & AUDITOR =================
if st.session_state.article and st.session_state.cleaned_body:
    st.markdown("---")
    
    # 1. Metrics Strip
    art: StoryArticle = st.session_state.article
    words = len(st.session_state.cleaned_body.split())
    read_time = max(1, round(words / 220))
    score = st.session_state.policy_result.score if st.session_state.policy_result else 100
    status_label = st.session_state.policy_result.status_label if st.session_state.policy_result else "Safe"

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{art.total_parts}</div><div class="metric-lbl">Total Parts</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{words:,}</div><div class="metric-lbl">Total Words</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="metric-val">~{read_time} min</div><div class="metric-lbl">Reading Time</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{html.escape(art.domain[:18])}</div><div class="metric-lbl">Domain</div></div>', unsafe_allow_html=True)
    with m5:
        score_color = "#10b981" if score >= 85 else ("#f59e0b" if score >= 60 else "#ef4444")
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:{score_color};">{score}/100</div><div class="metric-lbl">Safety Score</div></div>', unsafe_allow_html=True)

    # 2. AdSense & AdsKeeper Policy Safety Shield Expander
    if st.session_state.policy_result:
        res: PolicyAnalysisResult = st.session_state.policy_result
        badge_icon = "✅" if res.status == "SAFE" else ("⚠️" if res.status == "CAUTION" else "🚫")
        
        with st.expander(f"🛡️ **AdSense & AdsKeeper Policy Auditor — {badge_icon} {res.status_label} ({res.score}/100)**", expanded=(res.status != "SAFE")):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.markdown(f"**Google AdSense Verdict:** {res.adsense_verdict}")
            with col_v2:
                st.markdown(f"**AdsKeeper Verdict:** {res.adskeeper_verdict}")

            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.markdown(f"🔴 **High Risk (Ban Hazard):** {res.high_risk_count}")
            with col_r2:
                st.markdown(f"🟡 **Medium Risk (Caution):** {res.medium_risk_count}")
            with col_r3:
                st.markdown(f"🔵 **Low Risk (Contextual):** {res.low_risk_count}")

            if res.flags:
                st.markdown("#### Detected Sensitive Terms & Context:")
                for idx, flag in enumerate(res.flags):
                    sev_badge = "🔴 HIGH" if flag.severity == "HIGH" else ("🟡 MEDIUM" if flag.severity == "MEDIUM" else "🔵 LOW")
                    desc = POLICY_RULES.get(flag.category, {}).get("description", "")
                    
                    flag_col1, flag_col2 = st.columns([3.6, 2.4])
                    with flag_col1:
                        st.markdown(f"**`{flag.word_or_phrase}`** ({sev_badge} · *{flag.category_label}*) — {flag.match_count} occurrence(s)")
                        if desc:
                            st.caption(f"_{desc}_")
                    with flag_col2:
                        is_active = (st.session_state.get("highlight_word") == flag.word_or_phrase)
                        if is_active:
                            cur_idx = ((st.session_state.get("highlight_index", 1) - 1) % max(1, flag.match_count)) + 1
                            if flag.match_count > 1:
                                btn_prev_c, btn_next_c, btn_clr_c = st.columns([1, 1.4, 0.8])
                                with btn_prev_c:
                                    if st.button("⏮", key=f"prev_flag_{idx}_{flag.word_or_phrase}", help="Previous occurrence", use_container_width=True):
                                        st.session_state.highlight_index = flag.match_count if cur_idx == 1 else (cur_idx - 1)
                                        st.rerun()
                                with btn_next_c:
                                    if st.button(f"⏭ {cur_idx}/{flag.match_count}", key=f"next_flag_{idx}_{flag.word_or_phrase}", type="primary", help="Go to next occurrence in story", use_container_width=True):
                                        st.session_state.highlight_index = 1 if cur_idx >= flag.match_count else (cur_idx + 1)
                                        st.rerun()
                                with btn_clr_c:
                                    if st.button("✕", key=f"clr_flag_{idx}_{flag.word_or_phrase}", help="Clear highlight", use_container_width=True):
                                        st.session_state.highlight_word = None
                                        st.session_state.highlight_index = 1
                                        st.rerun()
                            else:
                                btn_act_c, btn_clr_c = st.columns([2, 1])
                                with btn_act_c:
                                    st.button("✓ Highlighted", key=f"act_flag_{idx}_{flag.word_or_phrase}", disabled=True, use_container_width=True)
                                with btn_clr_c:
                                    if st.button("✕", key=f"clr_flag_{idx}_{flag.word_or_phrase}", help="Clear highlight", use_container_width=True):
                                        st.session_state.highlight_word = None
                                        st.session_state.highlight_index = 1
                                        st.rerun()
                        else:
                            label = f"🔍 Find ({flag.match_count})" if flag.match_count > 1 else "🔍 Find in Story"
                            if st.button(label, key=f"find_flag_{idx}_{flag.word_or_phrase}", use_container_width=True):
                                st.session_state.highlight_word = flag.word_or_phrase
                                st.session_state.highlight_index = 1
                                st.rerun()

                    for snip in flag.context_snippets:
                        st.markdown(f"> *\"{snip}\"*")
            else:
                st.success("🎉 No policy risk keywords found! Content is fully monetizable with Google AdSense and AdsKeeper.")

    # 3. Editable Title Section
    st.markdown("### 📌 Article Title")
    col_t1, col_t2 = st.columns([5, 2])
    with col_t1:
        new_title = st.text_input("Title:", value=st.session_state.edited_title or art.title, label_visibility="collapsed")
        if new_title != st.session_state.edited_title:
            st.session_state.edited_title = new_title
            art.title = new_title
    with col_t2:
        render_copy_button(st.session_state.edited_title or art.title, button_label="📋 Copy Title", success_label="✓ Title Copied!", key="btn_copy_title", bg_color="#2563eb")

    # 4. Clean Story Body & Actions
    col_hdr, col_acts = st.columns([3, 3])
    with col_hdr:
        st.markdown("### 📖 Clean Article Body")
    with col_acts:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🧹 Clean Text", use_container_width=True):
                cleaned = clean_pure_text(st.session_state.cleaned_body)
                cleaned = StoryScraper.clean_text(cleaned)
                st.session_state.cleaned_body = cleaned
                st.session_state.highlight_word = None
                st.session_state.highlight_index = 1
                st.toast("✨ Story body cleaned and formatted!", icon="🧹")
                st.rerun()
        with b2:
            render_copy_button(st.session_state.cleaned_body, button_label="📋 Copy Article", success_label="✓ Article Copied!", key="btn_copy_article", bg_color="#059669")

    # Generate highlighted HTML, active count, and reader rendering
    highlighted_html, total_matches = highlight_text_in_html(
        st.session_state.cleaned_body,
        st.session_state.get("highlight_word"),
        st.session_state.get("highlight_index", 1)
    )
    
    current_active_idx = ((st.session_state.get("highlight_index", 1) - 1) % max(1, total_matches)) + 1 if total_matches > 0 else 1

    # Active Highlight Navigation Toolbar
    if st.session_state.get("highlight_word") and total_matches > 0:
        hl_col_info, hl_col_nav, hl_col_clear = st.columns([4.2, 3.2, 1.2])
        with hl_col_info:
            st.info(f"🔍 Finding **`{st.session_state.highlight_word}`** — Occurrence **{current_active_idx} of {total_matches}**")
        with hl_col_nav:
            if total_matches > 1:
                p_col, n_col = st.columns(2)
                with p_col:
                    if st.button("⏮ Previous", key="reader_prev_btn", use_container_width=True):
                        st.session_state.highlight_index = total_matches if current_active_idx == 1 else (current_active_idx - 1)
                        st.rerun()
                with n_col:
                    if st.button(f"⏭ Next ({current_active_idx}/{total_matches})", key="reader_next_btn", type="primary", use_container_width=True):
                        st.session_state.highlight_index = 1 if current_active_idx >= total_matches else (current_active_idx + 1)
                        st.rerun()
            else:
                st.caption("_(Single occurrence found in story)_")
        with hl_col_clear:
            if st.button("✕ Clear", key="reader_clear_btn", use_container_width=True):
                st.session_state.highlight_word = None
                st.session_state.highlight_index = 1
                st.rerun()
    elif st.session_state.get("highlight_word") and total_matches == 0:
        st.warning(f"⚠️ No matches found for '{st.session_state.highlight_word}' in the cleaned body.")

    # Reader Content Box with auto-scroll script
    scroll_script = ""
    if st.session_state.get("highlight_word") and total_matches > 0:
        scroll_script = (
            '<img src="x" style="display:none;" onerror="'
            '(function(){'
            '  function performScroll(){'
            '    var el = document.getElementById(\'active-highlight-mark\');'
            '    var box = document.getElementById(\'story-reader-container\');'
            '    if (el) {'
            '      try {'
            '        el.scrollIntoView({ behavior: \'smooth\', block: \'center\', inline: \'nearest\' });'
            '      } catch(e) { el.scrollIntoView(true); }'
            '      if (box) {'
            '        var rect = box.getBoundingClientRect();'
            '        if (rect.top < 80 || rect.top > (window.innerHeight - 160)) {'
            '          try {'
            '            box.scrollIntoView({ behavior: \'smooth\', block: \'start\' });'
            '          } catch(e) {}'
            '        }'
            '      }'
            '    }'
            '  }'
            '  setTimeout(performScroll, 60);'
            '  setTimeout(performScroll, 220);'
            '  setTimeout(performScroll, 550);'
            '})();" />'
        )

    st.markdown(
        f"""
        <div id="story-reader-container" style="
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(51, 65, 85, 0.8);
            border-radius: 12px;
            padding: 28px 36px;
            font-family: {font_family_css};
            font-size: {font_size}px;
            line-height: 1.85;
            color: #f1f5f9;
            white-space: pre-wrap;
            max-height: 600px;
            overflow-y: auto;
            text-align: justify;
        ">{highlighted_html}{scroll_script}</div>
        """,
        unsafe_allow_html=True
    )

    # 5. Export Downloads Row
    st.markdown("### 💾 Export & Download")
    d1, d2, d3 = st.columns(3)
    
    # Generate export files
    file_base = re.sub(r'[\\/*?:"<>|]', "", st.session_state.edited_title)[:60].strip() or "story"
    
    # TXT
    txt_data = f"{st.session_state.edited_title}\n\n{st.session_state.cleaned_body}".encode("utf-8")
    with d1:
        st.download_button(
            label="💾 Download Plain Text (.txt)",
            data=txt_data,
            file_name=f"{file_base}.txt",
            mime="text/plain",
            use_container_width=True
        )

    # Markdown
    if art:
        art.title = st.session_state.edited_title
        md_content = art.to_markdown()
    else:
        md_content = f"# {st.session_state.edited_title}\n\n{st.session_state.cleaned_body}"
    with d2:
        st.download_button(
            label="📄 Download Markdown (.md)",
            data=md_content.encode("utf-8"),
            file_name=f"{file_base}.md",
            mime="text/markdown",
            use_container_width=True
        )

    # HTML Reader
    if art:
        art.title = st.session_state.edited_title
        html_content = art.to_html(theme="dark")
    else:
        html_content = f"<html><body><h1>{html.escape(st.session_state.edited_title)}</h1><p>{html.escape(st.session_state.cleaned_body)}</p></body></html>"
    with d3:
        st.download_button(
            label="🌐 Download Offline HTML Reader (.html)",
            data=html_content.encode("utf-8"),
            file_name=f"{file_base}.html",
            mime="text/html",
            use_container_width=True
        )


# ================= FOOTER =================
st.markdown(
    """
    <div class="footer-box">
        Developed by <a href="https://www.deainnovations.com" target="_blank">DEA Innovations</a> &bull; 
        by <a href="https://github.com/edimonndi" target="_blank">github.com/edimonndi</a> &bull; 
        Multi-Page Story Scraper & Policy Safety Shield
    </div>
    """,
    unsafe_allow_html=True
)
