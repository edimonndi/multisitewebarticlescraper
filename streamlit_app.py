import html
import io
import os
import re
import time
from typing import Optional

import streamlit as st

from adsense_analyzer import AdSensePolicyAnalyzer, PolicyAnalysisResult, POLICY_RULES
from scraper_engine import StoryArticle, StoryPart, StoryScraper, clean_pure_text

# Set Page Config
st.set_page_config(
    page_title="DEA Story Scraper & Reader Pro",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            placeholder="https://america-focus.com/... or feji.io, fanstopis.com, levanews.com, kaylestore.net...",
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
                for flag in res.flags:
                    sev_badge = "🔴 HIGH" if flag.severity == "HIGH" else ("🟡 MEDIUM" if flag.severity == "MEDIUM" else "🔵 LOW")
                    desc = POLICY_RULES.get(flag.category, {}).get("description", "")
                    st.markdown(f"**`{flag.word_or_phrase}`** ({sev_badge} · *{flag.category_label}*) — {flag.match_count} occurrence(s)")
                    if desc:
                        st.caption(f"_{desc}_")
                    for snip in flag.context_snippets:
                        st.markdown(f"> *\"{snip}\"*")
            else:
                st.success("🎉 No policy risk keywords found! Content is fully monetizable with Google AdSense and AdsKeeper.")

    # 3. Editable Title Section
    st.markdown("### 📌 Article Title")
    new_title = st.text_input("Title:", value=st.session_state.edited_title or art.title, label_visibility="collapsed")
    if new_title != st.session_state.edited_title:
        st.session_state.edited_title = new_title
        art.title = new_title

    # 4. Clean Story Body & Actions
    col_hdr, col_acts = st.columns([3, 2])
    with col_hdr:
        st.markdown("### 📖 Clean Article Body")
    with col_acts:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🧹 Clean Text", use_container_width=True):
                cleaned = clean_pure_text(st.session_state.cleaned_body)
                cleaned = StoryScraper.clean_text(cleaned)
                st.session_state.cleaned_body = cleaned
                st.rerun()
        with b2:
            st.button("📋 Ready to Copy", use_container_width=True, help="Select and copy text directly from the reader box below.")

    # Reader Content Box
    st.markdown(
        f"""
        <div style="
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
        ">{html.escape(st.session_state.cleaned_body)}</div>
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
