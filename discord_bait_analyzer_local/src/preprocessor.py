import re
from typing import Iterable, List, Set

IGNORED_USERS = {
    'MEE6',
    'Deleted User'
}

BAIT_PATTERNS = [
    r'shiny\s+flash(?:y)?(?:\s+thing)?',
    r'fishing\s+fly',
    r'salmon\s+egg(?:s)?',
    r'shr(?:i|1)?m+p?s?\s+lure',
    r'wiggl?y\s+worm',
    r'mega[-\s]*pellet(?:\s+bait)?',
    r'uranium\s+glowing\s+lure',
]

GENERAL_SELLER_PATTERNS = [
    r'sell(?:ing)?\s+bait(?:s)?\s+at',
    r'cheap\s+bait(?:s)?\s+at',
    r'selling\s+bait(?:s)?\s+in',
    r'bait\s+at',
    r'restock(?:ed)?\s+bait(?:s)?\s+at',
    r'come\s+\w+\s+for\s+bait',
    r'bait\s+shop',
    r'looking\s+for\s+bait\?',
]

BUY_PATTERNS = [
    r'\bbuy(?:ing)?\b',
    r'\bneed\b',
    r'\blf\b',
    r'\bwtb\b',
    r'dm\s+me\s+if\s+u\s+sell',
]

SELL_PATTERNS = [
    r'\bsell(?:ing)?\b',
    r'\bcheap\b',
    r'\brestock(?:ed)?\b',
    r'\bshop\b',
    r'\bvend\b',
    r'\bclearing\b',
]

STOP_WORDS = {
    'SELL', 'SELLING', 'BUY', 'BUYING', 'BAIT', 'BAITS', 'CHEAP', 'GO', 'AT', 'IN',
    'WORLD', 'WORLDS', 'RESTOCK', 'RESTOCKED', 'SHOP', 'STORE', 'VEND', 'VENDING',
    'WIGGLY', 'WORM', 'SHINY', 'FLASHY', 'THING', 'FISHING', 'FLY', 'SALMON', 'EGG',
    'EGGS', 'SHRIMP', 'LURE', 'MEGA', 'PELLET', 'URANIUM', 'GLOWING', 'DL', 'WL',
    'BGL', 'DM', 'ME', 'RATE', 'STOCK', 'SOLD', 'NOT', 'LINK', 'ONLY', 'ALL',
    'HAVE', 'TONS', 'NEED', 'DAILY', 'ARROW', 'VERIFIED', 'CORRECT', 'REMEMBER',
    'COME', 'FOR', 'AND', 'THE', 'OUT', 'OF', 'IF', 'YOU', 'MSG', 'VISIT',
}

MESSAGE_BLOCK_RE = re.compile(r'(\[.*?\]\s+.*?)(?=\n\[.*?\]\s+|\Z)', re.DOTALL)
HEADER_RE = re.compile(r'^\[(.*?)\]\s+(.+?)\n', re.DOTALL)
WORLD_TOKEN_RE = re.compile(r'\b[A-Za-z0-9]{3,24}\b')

EXPLICIT_WORLD_PATTERNS = [
    re.compile(
        r'(?:sell(?:ing)?\s+bait(?:s)?\s+at|cheap\s+bait(?:s)?\s+at|selling\s+bait(?:s)?\s+in|restock(?:ed)?\s+bait(?:s)?\s+at|bait\s+at|sell\s+at|sell\s+cheap\s+bait\s+at|cheap\s+baits?\s+at)\s+([^\n]+)',
        re.IGNORECASE,
    ),
    re.compile(r'(?:go|come|visit|in|at)\s+([^\n]+)', re.IGNORECASE),
    re.compile(r'world\s+name\s*[:\-]?\s*([^\n]+)', re.IGNORECASE),
]


def _normalize_text(text: str) -> str:
    text = text.replace('**', ' ').replace('__', ' ').replace('`', ' ').replace('*', ' ')
    text = re.sub(r'<a?:[^>]+>', ' ', text)
    text = re.sub(r':[A-Za-z0-9_]+:', ' ', text)
    text = re.sub(r'[\u2190-\u21ff]', ' ', text)
    return text



def _has_bait_context(text_lower: str) -> bool:
    return any(re.search(pattern, text_lower) for pattern in BAIT_PATTERNS)



def _looks_like_buyer_only(text_lower: str) -> bool:
    has_buy = any(re.search(pattern, text_lower) for pattern in BUY_PATTERNS)
    has_sell = any(re.search(pattern, text_lower) for pattern in SELL_PATTERNS) or any(
        re.search(pattern, text_lower) for pattern in GENERAL_SELLER_PATTERNS
    )
    return has_buy and not has_sell



def _split_candidate_segment(segment: str) -> Iterable[str]:
    segment = _normalize_text(segment)
    segment = re.sub(r'\([^\)]*\)', ' ', segment)
    parts = re.split(r'[/|,&]|\band\b|\bor\b', segment, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]



def _extract_world_tokens(segment: str) -> List[str]:
    candidates = []
    for token in WORLD_TOKEN_RE.findall(segment):
        token_up = token.upper()
        if token_up in STOP_WORDS:
            continue
        if token_up.isdigit():
            continue
        if len(token_up) < 3 or len(token_up) > 24:
            continue
        candidates.append(token_up)
    return candidates



def _extract_worlds_from_text(text: str) -> Set[str]:
    worlds: Set[str] = set()
    clean_text = _normalize_text(text)

    for pattern in EXPLICIT_WORLD_PATTERNS:
        for match in pattern.findall(clean_text):
            for piece in _split_candidate_segment(match):
                for token in _extract_world_tokens(piece):
                    worlds.add(token)

    for line in clean_text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if re.search(r'^(go|at|in)\b', line_stripped, re.IGNORECASE):
            for token in _extract_world_tokens(line_stripped):
                worlds.add(token)

    return worlds



def analyze_and_extract_from_content(content: str) -> List[str]:
    """Ekstrak nama world penjual bait dari satu file log Discord."""
    extracted_worlds: Set[str] = set()
    blocks = MESSAGE_BLOCK_RE.findall(content)

    for block in blocks:
        header_match = HEADER_RE.match(block)
        if not header_match:
            continue

        username = header_match.group(2).strip().splitlines()[0].strip()
        if username in IGNORED_USERS:
            continue

        message_body = block[header_match.end():].strip()
        if not message_body:
            continue

        text_lower = message_body.lower()

        if not _has_bait_context(text_lower):
            continue
        if _looks_like_buyer_only(text_lower):
            continue

        seller_signal = any(re.search(pattern, text_lower) for pattern in SELL_PATTERNS) or any(
            re.search(pattern, text_lower) for pattern in GENERAL_SELLER_PATTERNS
        )
        if not seller_signal:
            continue

        extracted_worlds.update(_extract_worlds_from_text(message_body))

    return sorted(extracted_worlds)
