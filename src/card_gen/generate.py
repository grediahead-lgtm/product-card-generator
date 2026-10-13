"""Titles and descriptions from product attributes by templates. No AI, no invention:
only the attributes you provide appear in the text, and every problem is reported."""
import hashlib
import re

PLACEHOLDER = re.compile(r"\{(\w+)\}")
RISKY = ["найкращ", "лучш", "№1", "100%", "гарантуємо", "гарантируем", "дешевш", "дешевле всех", "лікує", "лечит", "ідеальн", "идеальн"]


def fill(template, attrs):
    """Fills {placeholders}. Returns (text, missing). A part in [square brackets] is dropped
    entirely when any placeholder inside it is empty, so there are no dangling words."""
    missing = []

    def part(m):
        inner = m.group(1)
        names = PLACEHOLDER.findall(inner)
        if any(not attrs.get(n) for n in names):
            return ""
        return PLACEHOLDER.sub(lambda x: str(attrs[x.group(1)]), inner)

    text = re.sub(r"\[([^\]]*)\]", part, template)
    for n in PLACEHOLDER.findall(text):
        if not attrs.get(n):
            missing.append(n)
    text = PLACEHOLDER.sub(lambda x: str(attrs.get(x.group(1), "")), text)
    return re.sub(r"\s+", " ", text).strip(" ,.-"), missing


def pick(variants, seed):
    """Deterministic choice: the same product always gets the same variant, different products differ."""
    h = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16)
    return variants[h % len(variants)]


def build_card(attrs, lang_cfg, seed):
    title, miss_t = fill(lang_cfg["title"], attrs)
    sentences, missing = [], list(miss_t)
    for s in lang_cfg["sentences"]:
        variants = s if isinstance(s, list) else [s]
        text, miss = fill(pick(variants, seed + str(len(sentences))), attrs)
        if text and not miss:
            sentences.append(text[0].upper() + text[1:] + ("" if text.endswith((".", "!", "?")) else "."))
        else:
            missing += miss
    return title, " ".join(sentences), sorted(set(missing))


def check(title, desc, lim):
    issues = []
    if len(title) > lim["title_max"]:
        issues.append("title is %d chars (max %d)" % (len(title), lim["title_max"]))
    if len(title) < lim.get("title_min", 10):
        issues.append("title is too short")
    if len(desc) < lim["desc_min"]:
        issues.append("description is %d chars (min %d)" % (len(desc), lim["desc_min"]))
    if len(desc) > lim["desc_max"]:
        issues.append("description is %d chars (max %d)" % (len(desc), lim["desc_max"]))
    low = (title + " " + desc).lower()
    for w in RISKY:
        if w in low:
            issues.append("risky claim: %r" % w)
    return issues


def run(rows, cfg):
    """rows: list of attribute dicts. Returns (out_rows, summary)."""
    out, seen_titles = [], {}
    for i, attrs in enumerate(rows, start=2):
        key = attrs.get("sku") or attrs.get("name") or str(i)
        rec = {"sku": attrs.get("sku", ""), "issues": []}
        for lang, lc in cfg["languages"].items():
            title, desc, missing = build_card(attrs, lc, key)
            rec["title_" + lang], rec["desc_" + lang] = title, desc
            rec["issues"] += ["[%s] %s" % (lang, x) for x in check(title, desc, cfg["limits"])]
            rec["issues"] += ["[%s] missing: %s" % (lang, m) for m in missing if m in cfg.get("required", [])]
            seen = seen_titles.setdefault(lang, {})
            if title in seen:
                rec["issues"].append("[%s] same title as row %d" % (lang, seen[title]))
            else:
                seen[title] = i
        rec["issues"] = "; ".join(rec["issues"])
        out.append(rec)
    return out, {"rows": len(out), "with_issues": sum(1 for r in out if r["issues"])}
