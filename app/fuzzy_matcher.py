"""
Fuzzy Matching Utilities for NL-to-SQL.
Uses RapidFuzz for string similarity, FlashText for keyword extraction,
and spaCy for NLP preprocessing.
"""
import logging
import re
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from rapidfuzz import fuzz, process

from app.config import settings

logger = logging.getLogger(__name__)

# Try to load spaCy model
try:
    import spacy
    _nlp = spacy.load(settings.spacy_model)
    _spacy_available = True
except Exception as e:
    logger.warning(f"spaCy model '{settings.spacy_model}' not available: {e}. "
                   f"Run: python -m spacy download {settings.spacy_model}")
    _spacy_available = False


class FuzzyMatcher:
    """
    Matches user natural language terms to database schema objects (tables, columns)
    using multiple strategies: edit distance, token similarity, and keyword extraction.
    """

    def __init__(self):
        self._keyword_processor = None
        self._keyword_dict: Dict[str, str] = {}
        self._table_names: List[str] = []
        self._column_names: List[str] = []
        self._column_to_table: Dict[str, str] = {}

    def load_schema(self, tables: List, columns: List[Tuple[str, str, str]] = None):
        """
        Load schema objects for matching.
        
        Args:
            tables: List of table names
            columns: List of (table_name, column_name, data_type) tuples
        """
        self._table_names = [t.name if hasattr(t, 'name') else str(t) for t in tables]
        
        if columns:
            for table_name, col_name, data_type in columns:
                qualified = f"{table_name}.{col_name}"
                self._column_names.append(col_name)
                self._column_names.append(qualified)
                self._column_to_table[col_name] = table_name
                self._column_to_table[qualified] = table_name

        # Build FlashText keyword processor
        try:
            from flashtext import KeywordProcessor
            self._keyword_processor = KeywordProcessor(case_sensitive=False)
            for name in self._table_names:
                self._keyword_processor.add_keyword(name, ("table", name))
                # Add common variations
                self._keyword_processor.add_keyword(name.replace("_", " "), ("table", name))
                self._keyword_processor.add_keyword(name.replace("_", ""), ("table", name))
            for col in self._column_names:
                self._keyword_processor.add_keyword(col, ("column", col))
                self._keyword_processor.add_keyword(col.replace("_", " "), ("column", col))
        except ImportError:
            self._keyword_processor = None
            logger.debug("FlashText not available, using regex-based extraction")

    def extract_keywords(self, text: str) -> List[str]:
        """Extract potential database-related keywords from natural language text."""
        keywords = set()

        # FlashText extraction
        if self._keyword_processor:
            found = self._keyword_processor.extract_keywords(text)
            for match_type, match_value in found:
                keywords.add(match_value)

        # Regex-based extraction for snake_case and CamelCase terms
        snake_case_terms = re.findall(r'\b[a-z]+_[a-z_0-9]+\b', text.lower())
        keywords.update(snake_case_terms)

        # Extract capitalized phrases (likely table/column names in queries)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        keywords.update(c.lower() for c in capitalized)

        # spaCy-based extraction
        if _spacy_available:
            doc = _nlp(text)
            for chunk in doc.noun_chunks:
                keywords.add(chunk.text.lower().strip())
            for ent in doc.ents:
                if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART", "EVENT"):
                    keywords.add(ent.text.lower().strip())

        return list(keywords)

    def find_best_table_match(self, term: str, threshold: float = 0.6) -> Optional[Tuple[str, float]]:
        """
        Find the best matching table for a given term using fuzzy string matching.
        
        Args:
            term: User's natural language term
            threshold: Minimum similarity score (0-1)
            
        Returns:
            Tuple of (best_table_name, score) or None if no match found
        """
        if not self._table_names:
            return None

        # Try exact match first
        term_lower = term.lower().strip()
        for table in self._table_names:
            if table.lower() == term_lower or table.lower() == term_lower.replace(" ", "_"):
                return (table, 1.0)

        # Fuzzy match using token sort ratio (handles word reordering)
        match_result = process.extractOne(
            term_lower,
            self._table_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=int(threshold * 100),
        )

        if match_result:
            return (match_result[0], match_result[1] / 100.0)

        # Try partial match (for compound terms)
        best_score = 0.0
        best_table = None
        for table in self._table_names:
            partial = fuzz.partial_ratio(term_lower, table) / 100.0
            if partial > best_score:
                best_score = partial
                best_table = table

        if best_score >= threshold:
            return (best_table, best_score)

        return None

    def find_best_column_match(self, term: str, threshold: float = 0.5) -> Optional[Tuple[str, str, float]]:
        """
        Find the best matching column for a given term.
        
        Returns:
            Tuple of (table_name, column_name, score) or None
        """
        if not self._column_names:
            return None

        term_lower = term.lower().strip()

        # Exact match
        for col in self._column_names:
            if col.lower() == term_lower:
                table = self._column_to_table.get(col, "")
                return (table, col, 1.0)

        # Fuzzy match
        match_result = process.extractOne(
            term_lower,
            self._column_names,
            scorer=fuzz.WRatio,
            score_cutoff=int(threshold * 100),
        )

        if match_result:
            col_name = match_result[0]
            table = self._column_to_table.get(col_name, "")
            return (table, col_name, match_result[1] / 100.0)

        return None

    def extract_tables_from_question(self, question: str) -> List[Tuple[str, float]]:
        """
        Extract and score all candidate tables from a natural language question.
        
        Returns:
            List of (table_name, confidence_score) sorted by score descending
        """
        keywords = self.extract_keywords(question)
        results = []

        for kw in keywords:
            match = self.find_best_table_match(kw)
            if match:
                results.append(match)

        # Also check individual words
        words = [w.lower() for w in question.split() if len(w) > 2]
        for word in words:
            if word not in keywords:
                match = self.find_best_table_match(word)
                if match:
                    results.append(match)

        # Deduplicate and average scores
        score_map: Dict[str, List[float]] = {}
        for table, score in results:
            if table not in score_map:
                score_map[table] = []
            score_map[table].append(score)

        averaged = [(t, np.mean(s).item()) for t, s in score_map.items()]
        averaged.sort(key=lambda x: x[1], reverse=True)
        return averaged

    def extract_columns_from_question(self, question: str) -> List[Tuple[str, str, float]]:
        """
        Extract candidate columns from a question.
        
        Returns:
            List of (table_name, column_name, confidence_score)
        """
        keywords = self.extract_keywords(question)
        results = []

        for kw in keywords:
            match = self.find_best_column_match(kw)
            if match:
                table, col, score = match
                results.append((table, col, score))

        # Search for possessive patterns: "customer's name" -> customer.name
        poss_pattern = re.findall(r"(\w+)'[s]?\s+(\w+)", question.lower())
        for obj, attr in poss_pattern:
            table_match = self.find_best_table_match(obj, threshold=0.4)
            col_match = self.find_best_column_match(attr, threshold=0.4)
            if table_match and col_match:
                results.append((table_match[0], col_match[1], min(table_match[1], col_match[1])))

        results.sort(key=lambda x: x[2], reverse=True)
        return results

    def get_common_phrases(self) -> Dict[str, str]:
        """Return a map of common business phrases to schema objects."""
        phrases = {
            "list": "SELECT",
            "show": "SELECT",
            "find": "SELECT",
            "count": "COUNT",
            "total": "SUM",
            "average": "AVG",
            "avg": "AVG",
            "minimum": "MIN",
            "minimum": "MIN",
            "maximum": "MAX",
            "max": "MAX",
            "group by": "GROUP BY",
            "sorted by": "ORDER BY",
            "ordered by": "ORDER BY",
            "top": "LIMIT",
            "first": "LIMIT",
            "limit": "LIMIT",
        }
        return phrases


# Singleton
fuzzy_matcher = FuzzyMatcher()