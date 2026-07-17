"""Deterministic, content-based classification for ChatGPT conversations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Classification:
    disposition: str
    categories: tuple[str, ...]
    engineering_evidence: tuple[str, ...]
    exclusion_evidence: tuple[str, ...]
    priority_flags: tuple[str, ...]
    system_design_concepts: tuple[str, ...]
    project_flags: tuple[str, ...]


CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "Go foundations": (
        r"\bgolang\b", r"```go\b", r"\bgo (?:program|code|function|package|module|developer|backend|interview)\b",
        r"\bdefer\s+\w+\s*\(", r"\bpanic\s*\(", r"\brecover\s*\(", r"\berrors\.(?:is|as)\b",
    ),
    "Go collections": (
        r"\bgo (?:slice|map)s?\b", r"\bmake\(\[\]", r"\bappend\(", r"\bmap\[[^\]]+\]",
        r"\bslice (?:header|capacity|length|alias)",
    ),
    "structs, methods and interfaces": (
        r"\bgo (?:struct|interface|method|receiver)s?\b", r"\btype \w+ struct\b",
        r"\bpointer receiver\b", r"\bvalue receiver\b", r"\bmethod set\b", r"\bstruct embedding\b",
    ),
    "Go concurrency": (
        r"\bgoroutine", r"\bgo channel", r"\bchan\b", r"\bwaitgroup\b", r"\bsync\.(?:mutex|rwmutex|once|pool)",
        r"\bworker pool\b", r"\bfan[- ](?:in|out)\b", r"\bcontext cancellation\b",
    ),
    "Go runtime and internals": (
        r"\bgo runtime\b", r"\bgmp scheduler\b", r"\bescape analysis\b", r"\bgarbage collector\b",
        r"\binterface internals\b", r"\bmap internals\b", r"\bslice internals\b", r"\bsync\.pool\b",
    ),
    "Go networking and testing": (
        r"\bgin(?:-gonic)?\b", r"\bnet/http\b", r"\bhttptest\b", r"\bgo test\b", r"\btable[- ]driven test",
        r"\bgo (?:http|networking|testing)\b",
    ),
    "DSA and NeetCode": (
        r"\b(?:dsa|leetcode|neet.?code|algomоnster|algomonster)\b", r"\bdata structures? and algorithms?\b",
        r"\b(?:two pointers?|sliding window|binary search|bfs|dfs|dynamic programming|kadane|heap|hash table|linked list)\b",
        r"\btime complexity\b", r"\bspace complexity\b",
    ),
    "system-design foundations": (
        r"\bsystem design\b", r"\bhigh[- ]level (?:design|architecture)\b", r"\bapi gateway\b",
        r"\bload balanc", r"\bscalab(?:le|ility)\b", r"\bcapacity estimation\b",
    ),
    "distributed-system patterns": (
        r"\bdistributed system", r"\bsaga\b", r"\btransactional outbox\b", r"\bchange data capture\b|\bcdc\b",
        r"\bcqrs\b", r"\bevent[- ]driven\b", r"\bdistributed lock", r"\bleader election\b",
        r"\bidempoten", r"\bbackpressure\b", r"\bcircuit breaker\b", r"\bbulkhead\b",
    ),
    "real system designs": (
        r"\buber system design\b", r"\byoutube system design\b", r"\bdesign (?:uber|youtube)\b",
        r"\breal[- ]time (?:location|messaging) (?:system|architecture|pipeline)\b",
    ),
    "databases": (
        r"\bpostgres(?:ql)?\b", r"\bmysql\b", r"\bmongodb\b", r"\bdatabase (?:index|transaction|replication|shard)",
        r"\btransaction isolation\b", r"\boptimistic lock", r"\bsql (?:query|database|index|transaction)\b",
    ),
    "Kafka and messaging": (
        r"\bkafka\b", r"\bconsumer group\b", r"\bmessage queue\b", r"\bpub/?sub\b", r"\bdead letter queue\b|\bdlq\b",
        r"\bmessage broker\b",
    ),
    "caching and Redis": (
        r"\bredis\b", r"\bcache[- ]aside\b", r"\bcache invalidation\b", r"\blru cache\b", r"\bdistributed cache\b",
    ),
    "Kubernetes and infrastructure": (
        r"\bkubernetes\b|\bk8s\b", r"\beks\b", r"\bdocker\b", r"\bterraform\b", r"\bhelm\b",
        r"\bcontainer orchestration\b", r"\becs\b",
    ),
    "Linux and networking": (
        r"\blinux\b", r"\bsubnet\b", r"\brouting table\b", r"\breverse proxy\b", r"\bforward proxy\b",
        r"\bdns\b", r"\btcp\b", r"\bwebsocket\b", r"\bipsec\b", r"\bnetwork (?:architecture|troubleshoot|issue)\b",
    ),
    "security": (
        r"\boauth\b", r"\boidc\b", r"\bjwt\b", r"\bmtls\b", r"\btls\b", r"\bauthentication\b",
        r"\bauthorization\b", r"\bbearer token\b", r"\bcertificate chain\b",
    ),
    "AWS": (
        r"\baws\b", r"\bamazon web services\b", r"\blambda\b", r"\bbedrock\b", r"\bcloudwatch\b",
        r"\bapi gateway\b", r"\becs\b", r"\beks\b",
    ),
    "reliability and observability": (
        r"\bobservability\b", r"\bprometheus\b", r"\bgrafana\b", r"\bkibana\b", r"\bkql\b",
        r"\bstructured logging\b", r"\bdistributed tracing\b", r"\bretr(?:y|ies)\b", r"\brate limit",
        r"\bcircuit breaker\b", r"\bbackpressure\b", r"\bslo\b|\bsla\b",
    ),
    "interview experiences": (
        r"\binterview (?:experience|round|feedback|rejection|assessment)\b", r"\bhackerearth test\b",
        r"\bcoding assessment\b", r"\btechnical interview\b",
    ),
    "interview mistakes": (
        r"\b(?:failed|failure|mistake|rejected|could not|couldn.t)\b.{0,100}\b(?:interview|code|implement|syntax)\b",
        r"\bweak (?:at|in|when)\b.{0,80}\b(?:implementation|coding|syntax|go|golang)\b",
    ),
    "behavioural and leadership preparation": (
        r"\bbehavio(?:u)?ral (?:interview|round|question)\b", r"\bleadership (?:interview|principle|question)\b",
        r"\bstar (?:answer|method|story)\b", r"\bstaff engineer interview\b",
    ),
    "production projects": (
        r"\bpermission version", r"\bcee-bff\b", r"\bnetflix conductor\b|\bconductor workflow\b",
        r"\bpulsecheck\b", r"\bcomarketer\b", r"\bncs (?:permission|throughput|panel)",
    ),
    "Google preparation roadmap": (
        r"\bgoogle (?:interview|preparation|prep|roadmap)\b", r"\bfaang (?:interview|preparation|prep|roadmap)\b",
        r"\b(?:senior|staff) (?:go|golang|backend|software) (?:interview|role|prep|preparation)\b",
    ),
}


EXCLUSION_PATTERNS: dict[str, tuple[str, ...]] = {
    "medical-health": (
        r"\b(?:diagnosis|symptom|treatment|remed(?:y|ies)|medicine|tablet|dosage|doctor|hospital|physiotherap|blood test|cbc|ecg|migraine|pain|rash|swelling|pregnan|workout|nutrition|calorie|protein supplement)\b",
    ),
    "shopping": (
        r"\b(?:shopping|purchase|retailer|product price|discount|coupon|flipkart|credit card benefit|voucher)\b",
    ),
    "personal-finance": (
        r"\b(?:investment|tax regime|loan|emi|credit card|debit card|insurance|mutual fund|elss|stock portfolio|gold price|xirr|interest certificate|debt repayment)\b",
    ),
    "travel": (
        r"\b(?:trip|itinerary|flight|train|lounge access|hotel|travel|irctc|passport renewal)\b",
    ),
    "household": (
        r"\b(?:washing machine|dishwasher|chimney|cabinet|air fryer|kettle|tv wi-fi|home appliance|laundry|household|cleaning guide|recipe)\b",
    ),
    "social-media-image": (
        r"\b(?:instagram|facebook|reels?|portrait request|image generation|caption|youtube metadata|social media growth|video editing|linkedin profile)\b",
    ),
    "unrelated-personal": (
        r"\b(?:marriage|maid|apology message|reply to compliment|leave reason|salary deduction|room confirmation|email attendance|pet|dog|rottweiler)\b",
    ),
}


PRIORITY_PATTERNS: dict[str, tuple[str, ...]] = {
    "slices": (r"\bgo slices?\b", r"\bslice syntax\b", r"\bappend\("),
    "maps": (r"\bgo maps?\b", r"\bmap syntax\b", r"\bmap\[[^\]]+\]"),
    "struct construction and constructors": (r"\bstruct (?:construction|creation|literal|constructor)", r"\bconstructor function\b"),
    "methods and receivers": (r"\b(?:method|pointer|value) receiver\b",),
    "interfaces": (r"\bgo interfaces?\b", r"\binterface implementation\b", r"\bmethod set\b"),
    "embedding and composition": (r"\bstruct embedding\b", r"\bembedding and composition\b"),
    "complete main invocation": (r"\binvok(?:e|ing|ation).{0,80}\bmain\b", r"\bmain invocation\b", r"\bcomplete executable go program\b"),
    "error handling": (r"\bgo error handling\b", r"\berrors\.(?:is|as)\b", r"\bfmt\.errorf\b"),
    "DSA implementation in Go": (r"\bdsa (?:in|with|using) go\b", r"\bgo (?:dsa|leetcode)\b"),
    "balanced four-part slice failure": (r"\b(?:partition|partions?).{0,100}\b(?:slice|array).{0,100}\b(?:four|4|even)", r"\b(?:four|4).{0,80}\b(?:balanced|even)\b.{0,80}\b(?:partitions?|groups?)"),
    "map and slice syntax failure": (r"\bmap syntax.{0,80}slice syntax\b", r"\b(?:map|slice) syntax.{0,120}\b(?:fail|weak|wrong)"),
    "theory stronger than implementation": (r"\btheor(?:y|ies|etical).{0,120}\b(?:weak|fail|implement)", r"\bimplementation fluency\b"),
    "Java DSA for Go interviews": (r"\b(?:neetcode|dsa).{0,120}\bjava.{0,160}\bgo(?:lang)?\b", r"\bjava.{0,120}\b(?:go|golang) interviews?\b"),
}


SYSTEM_CONCEPT_PATTERNS = {
    "Uber": r"\buber\b", "YouTube": r"\byoutube\b", "Saga": r"\bsaga\b",
    "transactional outbox": r"\btransactional outbox\b|\boutbox pattern\b", "CDC": r"\bchange data capture\b|\bcdc\b",
    "CQRS": r"\bcqrs\b", "event pipelines": r"\bevent (?:pipeline|stream|driven)\b", "caching": r"\bcach(?:e|ing)\b",
    "idempotency": r"\bidempoten", "retry": r"\bretr(?:y|ies)\b", "circuit breaker": r"\bcircuit breaker\b",
    "bulkhead": r"\bbulkhead\b", "backpressure": r"\bbackpressure\b", "rate limiting": r"\brate limit",
    "sharding": r"\bshard", "replication": r"\breplica(?:tion)?\b", "leader election": r"\bleader election\b",
    "distributed locking": r"\bdistributed lock", "Kafka": r"\bkafka\b", "PostgreSQL": r"\bpostgres(?:ql)?\b",
    "Redis": r"\bredis\b", "Kubernetes": r"\bkubernetes\b|\bk8s\b", "AWS": r"\baws\b|\bamazon web services\b",
    "networking": r"\bnetwork(?:ing)?\b|\btcp\b|\bdns\b|\bproxy\b", "OAuth": r"\boauth\b", "JWT": r"\bjwt\b",
    "OIDC": r"\boidc\b", "mTLS": r"\bmtls\b", "WebSockets": r"\bwebsockets?\b", "observability": r"\bobservability\b",
}


PROJECT_PATTERNS = {
    "NCS Permission Versioning": r"\b(?:ncs.{0,80}permission|permission version)",
    "CEE Conductor Migration": r"\b(?:cee-bff|cee.{0,80}conductor|conductor migration)\b",
    "CoMarketer WebSocket Architecture": r"\bcomarketer\b",
    "PulseCheck Monitoring System": r"\bpulsecheck\b",
}


def _matches(patterns: Iterable[str], text: str) -> list[str]:
    found = []
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            found.append(pattern)
    return found


def classify(title: str, body: str) -> Classification:
    """Classify using message content, with title used only as supplementary evidence."""
    categories: list[str] = []
    engineering_evidence: list[str] = []
    for category, patterns in CATEGORY_PATTERNS.items():
        body_hits = _matches(patterns, body)
        title_hits = _matches(patterns, title)
        if body_hits:
            categories.append(category)
            engineering_evidence.append(f"{category}:content:{body_hits[0]}")
        elif title_hits:
            # Title-only matches never qualify a record as definitively technical.
            engineering_evidence.append(f"{category}:title:{title_hits[0]}")

    exclusion_evidence: list[str] = []
    for domain, patterns in EXCLUSION_PATTERNS.items():
        hits = _matches(patterns, f"{title}\n{body}")
        if hits:
            exclusion_evidence.append(domain)

    content_category_count = len(categories)
    if content_category_count >= 2 and exclusion_evidence:
        disposition = "mixed-content"
    elif content_category_count >= 2:
        disposition = "engineering-relevant"
    elif content_category_count == 1 and not exclusion_evidence:
        disposition = "potentially engineering-relevant"
    elif content_category_count == 1 and exclusion_evidence:
        disposition = "mixed-content"
    elif exclusion_evidence:
        disposition = "excluded-non-engineering"
    else:
        disposition = "needs-manual-review"

    combined = f"{title}\n{body}"
    priority = tuple(name for name, patterns in PRIORITY_PATTERNS.items() if _matches(patterns, combined))
    concepts = tuple(name for name, pattern in SYSTEM_CONCEPT_PATTERNS.items() if re.search(pattern, combined, re.I | re.S))
    projects = tuple(name for name, pattern in PROJECT_PATTERNS.items() if re.search(pattern, combined, re.I | re.S))
    return Classification(
        disposition=disposition,
        categories=tuple(categories),
        engineering_evidence=tuple(engineering_evidence),
        exclusion_evidence=tuple(exclusion_evidence),
        priority_flags=priority,
        system_design_concepts=concepts,
        project_flags=projects,
    )
