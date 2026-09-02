import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Comprehensive AdSense & AdsKeeper Policy Rules & Keywords
# Categorized with severity weights:
# HIGH (15+ penalty): Direct policy violation (Sexually explicit, severe violence, suicide, hate slurs, drugs/weapons)
# MEDIUM (5-10 penalty): High sensitivity (Death, gore descriptions, severe profanity, domestic violence)
# LOW (2-4 penalty): Mild sensitivity (Mild drama words, medical surgery, graveyard, contextual shock words)

POLICY_RULES = {
    "adult_explicit": {
        "label": "Adult & Sexually Explicit Content",
        "severity": "HIGH",
        "penalty": 20,
        "description": "Strictly prohibited by Google AdSense & AdsKeeper. Can cause immediate account suspension.",
        "patterns": [
            r"\bporn\b", r"\bxxx\b", r"\bhardcore\b", r"\bhentai\b", r"\bmasturbat\w*",
            r"\borgasm\w*", r"\bpenis\w*", r"\bvagina\w*", r"\bclitoris\w*", r"\berection\w*",
            r"\bblowjob\w*", r"\bcunnilingus\w*", r"\banal\s+sex\b", r"\bpedophil\w*",
            r"\bincest\w*", r"\brape\w*", r"\brapist\w*", r"\bmolest\w*", r"\bnon-consensual\b",
            r"\bsexually\s+explicit\b", r"\bnude\b", r"\bnudity\b", r"\berotic\w*"
        ]
    },
    "extreme_violence": {
        "label": "Extreme Violence, Gore & Self-Harm",
        "severity": "HIGH",
        "penalty": 20,
        "description": "Prohibited by AdSense. Depictions of suicide, self-harm, mutilation, or graphic gore.",
        "patterns": [
            r"\bsuicide\w*", r"\bkill\s+(himself|herself|myself|yourself|themselves)\b",
            r"\bslit\s+(wrists?|throat)\b", r"\bhang\s+(himself|herself|myself)\b",
            r"\bhanging\s+body\b", r"\bmutilat\w*", r"\bbehead\w*", r"\bdecapitat\w*",
            r"\bgruesome\b", r"\bbloodbath\b", r"\btortur\w*", r"\bslaughter\w*",
            r"\bstrangle\w*", r"\bgore\b", r"\bcorpse\w*", r"\bdead\s+body\b",
            r"\bdecomposing\b", r"\bburied\s+alive\b"
        ]
    },
    "hate_harassment": {
        "label": "Hate Speech & Dangerous Discrimination",
        "severity": "HIGH",
        "penalty": 25,
        "description": "Direct AdSense violation. Hate speech, discrimination against protected groups, or slurs.",
        "patterns": [
            r"\bnigger\w*", r"\bfaggot\w*", r"\bkike\w*", r"\bchink\w*", r"\bspic\w*",
            r"\bwetback\w*", r"\bwhite\s+supremac\w*", r"\bneo-nazi\w*", r"\bterrorist\s+attack\b",
            r"\bjihad\w*", r"\bgenocide\w*", r"\bethnic\s+cleansing\b"
        ]
    },
    "illegal_drugs_weapons": {
        "label": "Illegal Drugs & Weapons",
        "severity": "HIGH",
        "penalty": 20,
        "description": "AdSense restricted. Promotion or graphic abuse of illicit drugs or firearms.",
        "patterns": [
            r"\bcocaine\b", r"\bheroin\b", r"\bmethamphetamine\b", r"\bcrystal\s+meth\b",
            r"\bfentanyl\b", r"\bbomb\s+making\b", r"\bpipe\s+bomb\b", r"\bghost\s+gun\b",
            r"\bassault\s+rifle\b", r"\bweapon\s+dealer\b", r"\bhitman\b"
        ]
    },
    "profanity_vulgarity": {
        "label": "Severe Profanity & Vulgarity",
        "severity": "MEDIUM",
        "penalty": 10,
        "description": "Strong profanity can trigger AdSense content warnings and reduced ad bids.",
        "patterns": [
            r"\bfuck\w*", r"\bmotherfuck\w*", r"\bcunt\w*", r"\bwhore\w*", r"\bslut\w*",
            r"\bco[ck]ksucker\w*", r"\bbitch\w*", r"\basshole\w*", r"\bdickhead\w*"
        ]
    },
    "sensitive_shock_drama": {
        "label": "Sensitive Tragic & Shock Drama Terms",
        "severity": "LOW",
        "penalty": 4,
        "description": "Common in story drama (coffin, funeral, murder, poisoning, surgery). AdSense allows stories, but monitor density.",
        "patterns": [
            r"\bcoffin\w*", r"\bcasket\w*", r"\bfuneral\w*", r"\bmurder\w*", r"\bpoison\w*",
            r"\babandoned\s+at\s+the\s+airport\b", r"\blabor\b", r"\bmistress\w*", r"\badultery\b",
            r"\bcheating\s+husband\b", r"\bbrain\s+surgery\b", r"\blife\s+support\b",
            r"\bterminal\s+illness\b", r"\bdaughter's\s+funeral\b"
        ]
    }
}


@dataclass
class PolicyFlag:
    category: str
    category_label: str
    severity: str  # HIGH, MEDIUM, LOW
    word_or_phrase: str
    match_count: int
    context_snippets: List[str] = field(default_factory=list)


@dataclass
class PolicyAnalysisResult:
    score: int  # 0 to 100 (100 = 100% Safe)
    status: str  # SAFE, CAUTION, HIGH_RISK
    status_label: str
    status_color: str
    flags: List[PolicyFlag] = field(default_factory=list)
    total_flags: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    adsense_verdict: str = ""
    adskeeper_verdict: str = ""
    recommendation: str = ""

    @property
    def is_safe(self) -> bool:
        return self.status == "SAFE"


class AdSensePolicyAnalyzer:
    def __init__(self):
        # Precompile regexes
        self.compiled_rules = {}
        for cat_id, info in POLICY_RULES.items():
            compiled_patterns = [re.compile(p, re.IGNORECASE) for p in info["patterns"]]
            self.compiled_rules[cat_id] = {
                "info": info,
                "patterns": compiled_patterns
            }

    def analyze(self, title: str, body: str) -> PolicyAnalysisResult:
        full_text = f"{title}\n\n{body}"
        if not full_text.strip():
            return PolicyAnalysisResult(
                score=100,
                status="SAFE",
                status_label="Clean / No Text",
                status_color="#10b981",
                adsense_verdict="Safe for Monetization",
                adskeeper_verdict="Safe for Monetization",
                recommendation="No content to evaluate."
            )

        flags_dict: Dict[Tuple[str, str], PolicyFlag] = {}
        total_penalty = 0

        # Split text into sentences for context extraction
        sentences = re.split(r'(?<=[.!?])\s+', full_text)

        for cat_id, rule_data in self.compiled_rules.items():
            info = rule_data["info"]
            patterns = rule_data["patterns"]
            severity = info["severity"]
            penalty_per_match = info["penalty"]

            for pattern in patterns:
                matches = pattern.findall(full_text)
                if matches:
                    # Find matched string
                    for m in matches:
                        matched_word = m if isinstance(m, str) else m[0]
                        matched_word_lower = matched_word.lower()
                        key = (cat_id, matched_word_lower)

                        if key not in flags_dict:
                            # Extract context snippets
                            snippets = []
                            for sent in sentences:
                                if pattern.search(sent):
                                    # Highlight snippet
                                    clean_sent = sent.strip().replace("\n", " ")
                                    if len(clean_sent) > 120:
                                        clean_sent = clean_sent[:115] + "..."
                                    snippets.append(clean_sent)
                                    if len(snippets) >= 2:
                                        break

                            flags_dict[key] = PolicyFlag(
                                category=cat_id,
                                category_label=info["label"],
                                severity=severity,
                                word_or_phrase=matched_word_lower,
                                match_count=len(matches),
                                context_snippets=snippets
                            )

                    # Accumulate penalty with dampening for multiple occurrences
                    match_count = len(matches)
                    if severity == "HIGH":
                        total_penalty += penalty_per_match + min(15, (match_count - 1) * 5)
                    elif severity == "MEDIUM":
                        total_penalty += penalty_per_match + min(10, (match_count - 1) * 3)
                    else:  # LOW
                        # Low severity shock words are common in fictional stories, dampen heavily
                        total_penalty += min(12, penalty_per_match + (match_count - 1) * 1)

        # Calculate final score (0 - 100)
        score = max(0, 100 - total_penalty)

        flags_list = list(flags_dict.values())
        # Sort flags by severity (HIGH -> MEDIUM -> LOW) then by count
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        flags_list.sort(key=lambda x: (severity_order.get(x.severity, 3), -x.match_count))

        high_count = sum(1 for f in flags_list if f.severity == "HIGH")
        med_count = sum(1 for f in flags_list if f.severity == "MEDIUM")
        low_count = sum(1 for f in flags_list if f.severity == "LOW")

        # Determine Verdict
        if high_count > 0 or score < 60:
            status = "HIGH_RISK"
            status_label = "🚫 High Risk / Policy Alert"
            status_color = "#ef4444"  # Red
            adsense_verdict = "⚠️ High Ban Risk: Contains prohibited terms (Adult, Extreme Violence, or Hate)"
            adskeeper_verdict = "⚠️ Policy Warning: Risk of campaign rejection or account sanction"
            recommendation = "Do NOT publish with AdSense until high-risk terms are removed or rewritten."
        elif med_count > 0 or score < 85:
            status = "CAUTION"
            status_label = "⚠️ Moderate Sensitivity / Review Needed"
            status_color = "#f59e0b"  # Amber / Yellow
            adsense_verdict = "🟡 Caution: May receive limited ad demand or content warnings (Profanity/Sensationalism)"
            adskeeper_verdict = "🟡 Review Needed: Moderate drama terms detected"
            recommendation = "Review flagged phrases. Softening dramatic/vulgar terms will improve ad fill rates."
        else:
            status = "SAFE"
            status_label = "✅ 100% AdSense & AdsKeeper Safe"
            status_color = "#10b981"  # Emerald Green
            adsense_verdict = "🟢 Fully Compliant: Safe for maximum AdSense monetization"
            adskeeper_verdict = "🟢 Fully Compliant: Approved for AdsKeeper traffic"
            recommendation = "Article is clean and safe to publish on monetized blogs/sites."

        return PolicyAnalysisResult(
            score=score,
            status=status,
            status_label=status_label,
            status_color=status_color,
            flags=flags_list,
            total_flags=len(flags_list),
            high_risk_count=high_count,
            medium_risk_count=med_count,
            low_risk_count=low_count,
            adsense_verdict=adsense_verdict,
            adskeeper_verdict=adskeeper_verdict,
            recommendation=recommendation
        )
