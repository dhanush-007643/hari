"""
DataVista+ NLP Engine
Natural Language Processing pipeline for query intent extraction and schema detection
Uses spaCy for NLP processing with fallback regex-based approach
"""
import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try loading spaCy model
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
    logger.info("spaCy model loaded successfully")
except Exception:
    nlp = None
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available, using regex fallback NLP")


# ─── Intent Patterns ───────────────────────────────────────────────────────────

INTENT_PATTERNS = {
    "SELECT": [
        r"\b(show|list|display|get|fetch|find|retrieve|what|which|give|tell)\b"
    ],
    "AGGREGATE_COUNT": [
        r"\b(count|how many|number of|total count)\b"
    ],
    "AGGREGATE_SUM": [
        r"\b(sum|total|aggregate|overall|combined)\b"
    ],
    "AGGREGATE_AVG": [
        r"\b(average|avg|mean|typical)\b"
    ],
    "AGGREGATE_MAX": [
        r"\b(maximum|max|highest|greatest|top|best|most)\b"
    ],
    "AGGREGATE_MIN": [
        r"\b(minimum|min|lowest|least|worst|bottom)\b"
    ],
    "FILTER": [
        r"\b(where|filter|with|having|only|except|excluding)\b"
    ],
    "GROUP": [
        r"\b(group by|grouped|per|by|each|every|categorize|breakdown)\b"
    ],
    "ORDER": [
        r"\b(sort|order|rank|arrange|top \d+|first \d+|last \d+)\b"
    ],
    "JOIN": [
        r"\b(join|combine|merge|with|related|associated|linked)\b"
    ],
    "TREND": [
        r"\b(trend|over time|monthly|weekly|daily|yearly|growth|decline)\b"
    ],
}

# Time expressions
TIME_PATTERNS = {
    "today": "DATE('now')",
    "yesterday": "DATE('now', '-1 day')",
    "last week": "DATE('now', '-7 days')",
    "last month": "DATE('now', '-1 month')",
    "last year": "DATE('now', '-1 year')",
    "this month": "strftime('%Y-%m', date_column) = strftime('%Y-%m', 'now')",
    "this year": "strftime('%Y', date_column) = strftime('%Y', 'now')",
    r"last (\d+) days": "DATE('now', '-{0} days')",
}

# Comparison operators
COMPARISON_MAP = {
    r"greater than|more than|above|over|>": ">",
    r"less than|fewer than|below|under|<": "<",
    r"equal to|equals|=|is": "=",
    r"at least|minimum of|>=": ">=",
    r"at most|maximum of|<=": "<=",
    r"not equal|!=|different from": "!=",
}

# Column name synonyms (common business terms)
COLUMN_SYNONYMS = {
    "revenue": ["total_amount", "sales", "revenue", "amount", "income", "total_revenue"],
    "orders": ["order_id", "orders", "transactions", "purchases"],
    "customers": ["customer_id", "customers", "clients", "buyers"],
    "products": ["product_id", "products", "items", "goods"],
    "date": ["order_date", "created_at", "date", "timestamp", "transaction_date"],
    "region": ["region", "area", "location", "territory", "zone"],
    "quantity": ["quantity", "qty", "units", "volume", "count"],
    "price": ["unit_price", "price", "cost", "rate"],
    "status": ["status", "state", "condition"],
    "employee": ["employee_id", "emp_id", "employees", "staff"],
    "salary": ["salary", "compensation", "pay", "wage"],
    "department": ["department", "dept", "division", "team"],
}


@dataclass
class NLPResult:
    """Result of NLP processing on a natural language query."""
    original_query: str
    normalized_query: str
    intent: str
    sub_intents: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    columns: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    filters: List[Dict] = field(default_factory=list)
    groupby: List[str] = field(default_factory=list)
    orderby: Optional[str] = None
    limit: Optional[int] = None
    time_filter: Optional[str] = None
    aggregation: Optional[str] = None
    confidence: float = 0.0
    keywords: List[str] = field(default_factory=list)


class NLPEngine:
    """
    Natural Language Processing engine for query intent extraction.
    Uses spaCy when available, falls back to regex-based processing.
    """

    def __init__(self, schema: Optional[Dict] = None):
        """
        Initialize NLP engine.
        schema: dict of {table_name: [column_names]} for schema-aware processing
        """
        self.schema = schema or {}
        self.all_tables = list(self.schema.keys())
        self.all_columns = [col for cols in self.schema.values() for col in cols]

    def process(self, query: str) -> NLPResult:
        """Main entry point: process a natural language query."""
        normalized = self._normalize(query)
        result = NLPResult(
            original_query=query,
            normalized_query=normalized,
            intent="SELECT",
        )

        # Extract components
        result.intent, result.sub_intents = self._detect_intent(normalized)
        result.keywords = self._extract_keywords(normalized)
        result.entities = self._extract_entities(normalized)
        result.tables = self._detect_tables(normalized)
        result.columns = self._detect_columns(normalized)
        result.filters = self._extract_filters(normalized)
        result.groupby = self._extract_groupby(normalized)
        result.orderby, result.limit = self._extract_order_limit(normalized)
        result.time_filter = self._extract_time_filter(normalized)
        result.aggregation = self._detect_aggregation(normalized)
        result.confidence = self._compute_confidence(result)

        return result

    def _normalize(self, query: str) -> str:
        """Lowercase, strip extra whitespace, fix common typos."""
        q = query.lower().strip()
        q = re.sub(r'\s+', ' ', q)
        q = q.replace("'", "'").replace(""", '"').replace(""", '"')
        return q

    def _detect_intent(self, query: str) -> Tuple[str, List[str]]:
        """Classify primary and secondary query intents."""
        matched_intents = []
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    matched_intents.append(intent)
                    break

        if not matched_intents:
            return "SELECT", []

        # Primary intent priority
        priority_order = [
            "AGGREGATE_COUNT", "AGGREGATE_SUM", "AGGREGATE_AVG",
            "AGGREGATE_MAX", "AGGREGATE_MIN", "TREND", "JOIN",
            "GROUP", "FILTER", "ORDER", "SELECT"
        ]
        for p in priority_order:
            if p in matched_intents:
                return p, [i for i in matched_intents if i != p]

        return matched_intents[0], matched_intents[1:]

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords using spaCy or regex."""
        if SPACY_AVAILABLE and nlp:
            doc = nlp(query)
            return [
                token.lemma_ for token in doc
                if not token.is_stop and not token.is_punct and token.is_alpha
            ]
        # Fallback: remove common stopwords
        stopwords = {
            "show", "me", "the", "a", "an", "of", "in", "is", "are",
            "what", "which", "how", "give", "list", "get", "find"
        }
        words = query.split()
        return [w for w in words if w not in stopwords and len(w) > 2]

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy NER."""
        entities = {"numbers": [], "dates": [], "names": [], "orgs": []}
        if SPACY_AVAILABLE and nlp:
            doc = nlp(query)
            for ent in doc.ents:
                if ent.label_ in ("CARDINAL", "QUANTITY", "PERCENT", "MONEY"):
                    entities["numbers"].append(ent.text)
                elif ent.label_ in ("DATE", "TIME"):
                    entities["dates"].append(ent.text)
                elif ent.label_ == "PERSON":
                    entities["names"].append(ent.text)
                elif ent.label_ == "ORG":
                    entities["orgs"].append(ent.text)
        # Regex fallback for numbers
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', query)
        entities["numbers"].extend(numbers)
        return entities

    def _detect_tables(self, query: str) -> List[str]:
        """Detect which database tables are referenced in the query."""
        detected = []
        for table in self.all_tables:
            # Direct match or partial match
            if table.replace("_", " ") in query or table in query:
                detected.append(table)

        # Keyword-based table detection from common synonyms
        table_keywords = {
            "sales_orders": ["order", "orders", "sale", "sales", "purchase"],
            "products": ["product", "products", "item", "items"],
            "customers": ["customer", "customers", "client", "clients", "buyer"],
            "employees": ["employee", "employees", "staff", "worker"],
            "departments": ["department", "departments", "dept", "division"],
            "transactions": ["transaction", "transactions", "payment"],
        }
        for table, keywords in table_keywords.items():
            for kw in keywords:
                if kw in query and table not in detected:
                    if table in self.all_tables:
                        detected.append(table)
                    break

        return detected or (self.all_tables[:1] if self.all_tables else [])

    def _detect_columns(self, query: str) -> List[str]:
        """Detect which columns are needed based on query context."""
        detected = []
        # Direct column name match
        for col in self.all_columns:
            if col.replace("_", " ") in query or col in query:
                detected.append(col)

        # Synonym-based detection
        for business_term, synonyms in COLUMN_SYNONYMS.items():
            for synonym in synonyms:
                if synonym in query:
                    detected.extend([s for s in synonyms if s in self.all_columns])
                    break
        return list(set(detected))

    def _extract_filters(self, query: str) -> List[Dict]:
        """Extract WHERE clause conditions from the query."""
        filters = []

        # Region/category filters
        region_match = re.search(
            r'\b(from|in|for|region|area)\s+["\']?([A-Za-z\s]+)["\']?', query
        )
        if region_match:
            filters.append({
                "column": "region",
                "operator": "=",
                "value": region_match.group(2).strip()
            })

        # Numeric comparisons
        for pattern, operator in COMPARISON_MAP.items():
            match = re.search(rf'{pattern}\s+(\d+(?:\.\d+)?)', query, re.IGNORECASE)
            if match:
                value = match.group(1) if len(match.groups()) == 1 else match.group(len(match.groups()))
                filters.append({"column": "value", "operator": operator, "value": float(value)})

        # Status filters
        status_match = re.search(r'\b(status|state)\s+(is\s+)?["\']?(\w+)["\']?', query)
        if status_match:
            filters.append({"column": "status", "operator": "=", "value": status_match.group(3)})

        return filters

    def _extract_groupby(self, query: str) -> List[str]:
        """Extract GROUP BY columns from the query."""
        groupby_patterns = [
            r'\bby\s+(region|area|category|department|status|month|year|product|customer)',
            r'\bper\s+(region|area|category|department|status|product|customer)',
            r'\beach\s+(region|area|category|department|status|product)',
            r'\bgroup(?:ed)?\s+by\s+(\w+)',
        ]
        groups = []
        for pattern in groupby_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                groups.append(match.group(1).lower())

        # Map to actual column names
        mapped = []
        for grp in groups:
            for col in self.all_columns:
                if grp in col:
                    mapped.append(col)
                    break
            else:
                mapped.append(grp)  # use as-is

        return list(set(mapped))

    def _extract_order_limit(self, query: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract ORDER BY direction and LIMIT from the query."""
        orderby = None
        limit = None

        # Limit patterns: "top 10", "first 5", "last 20"
        limit_match = re.search(r'\b(top|first|last)\s+(\d+)\b', query)
        if limit_match:
            limit = int(limit_match.group(2))
            orderby = "DESC" if limit_match.group(1) in ("top", "last") else "ASC"

        # Sort direction
        if re.search(r'\b(highest|maximum|max|most|best|desc)\b', query):
            orderby = "DESC"
        elif re.search(r'\b(lowest|minimum|min|least|worst|asc)\b', query):
            orderby = "ASC"

        return orderby, limit

    def _extract_time_filter(self, query: str) -> Optional[str]:
        """Extract time period filter from the query."""
        for pattern, sql_expr in TIME_PATTERNS.items():
            if isinstance(pattern, str) and pattern in query:
                return sql_expr
            elif hasattr(pattern, 'match'):
                match = re.search(pattern, query)
                if match:
                    return sql_expr.format(*match.groups())
        return None

    def _detect_aggregation(self, query: str) -> Optional[str]:
        """Detect aggregation function needed."""
        agg_map = {
            r'\b(count|how many)\b': "COUNT",
            r'\b(sum|total|aggregate)\b': "SUM",
            r'\b(average|avg|mean)\b': "AVG",
            r'\b(maximum|max|highest)\b': "MAX",
            r'\b(minimum|min|lowest)\b': "MIN",
        }
        for pattern, func in agg_map.items():
            if re.search(pattern, query, re.IGNORECASE):
                return func
        return None

    def _compute_confidence(self, result: NLPResult) -> float:
        """Compute confidence score based on how much was understood."""
        score = 0.5  # base
        if result.tables:
            score += 0.2
        if result.columns:
            score += 0.1
        if result.filters:
            score += 0.1
        if result.aggregation:
            score += 0.05
        if result.groupby:
            score += 0.05
        return min(round(score, 2), 1.0)
