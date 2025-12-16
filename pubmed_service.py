"""
PubMed Service for Medical Reviewer Agent
Provides search and article retrieval from NCBI PubMed database.
"""

import requests
import xml.etree.ElementTree as ET
from functools import lru_cache
from typing import List, Dict, Any, Optional
from datetime import datetime

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedService:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize PubMed service.
        
        Args:
            api_key: Optional NCBI API key for higher rate limits.
        """
        self.api_key = api_key
    
    async def search(self, query: str, max_results: int = 5, years: int = 10) -> List[Dict[str, Any]]:
        """
        Search PubMed for relevant articles.
        
        Args:
            query: Search query string.
            max_results: Maximum number of results to return.
            years: Number of years to search back.
            
        Returns:
            List of article dictionaries.
        """
        return self._search_sync(query, max_results, years)
    
    @lru_cache(maxsize=1000)
    def _search_sync(self, query: str, max_results: int = 5, years: int = 10) -> tuple:
        """Cached synchronous search implementation."""
        
        # Build search query with date filter
        search_url = f"{PUBMED_BASE}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "datetype": "pdat",
            "reldate": years * 365  # Days
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            search_results = response.json()
        except Exception as e:
            print(f"PubMed search error: {e}")
            return tuple()
        
        pmids = search_results.get("esearchresult", {}).get("idlist", [])
        
        if not pmids:
            return tuple()
        
        # Fetch article details
        articles = self._fetch_articles(pmids)
        return tuple(articles)
    
    def _fetch_articles(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch article details for given PMIDs."""
        
        fetch_url = f"{PUBMED_BASE}/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        if self.api_key:
            fetch_params["api_key"] = self.api_key
        
        try:
            fetch_response = requests.get(fetch_url, params=fetch_params, timeout=15)
            fetch_response.raise_for_status()
            articles = self._parse_pubmed_xml(fetch_response.text)
            return articles
        except Exception as e:
            print(f"PubMed fetch error: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """Parse PubMed XML response into article dictionaries."""
        
        articles = []
        try:
            root = ET.fromstring(xml_text)
            
            for article_elem in root.findall(".//PubmedArticle"):
                article = {}
                
                # PMID
                pmid_elem = article_elem.find(".//PMID")
                article["pmid"] = pmid_elem.text if pmid_elem is not None else ""
                
                # Title
                title_elem = article_elem.find(".//ArticleTitle")
                article["title"] = title_elem.text if title_elem is not None else ""
                
                # Authors
                authors = []
                for author in article_elem.findall(".//Author"):
                    last_name = author.find("LastName")
                    first_name = author.find("ForeName")
                    if last_name is not None:
                        name = last_name.text
                        if first_name is not None:
                            name = f"{first_name.text} {name}"
                        authors.append(name)
                article["authors"] = authors[:5]  # First 5 authors
                
                # Journal
                journal_elem = article_elem.find(".//Journal/Title")
                article["journal"] = journal_elem.text if journal_elem is not None else ""
                
                # Year
                year_elem = article_elem.find(".//PubDate/Year")
                if year_elem is None:
                    year_elem = article_elem.find(".//PubDate/MedlineDate")
                article["year"] = year_elem.text[:4] if year_elem is not None and year_elem.text else str(datetime.now().year)
                
                # Abstract
                abstract_parts = []
                for abstract_text in article_elem.findall(".//AbstractText"):
                    if abstract_text.text:
                        abstract_parts.append(abstract_text.text)
                article["abstract"] = " ".join(abstract_parts)
                
                articles.append(article)
                
        except ET.ParseError as e:
            print(f"XML parse error: {e}")
        
        return articles
    
    def calculate_relevance_score(self, query: str, article: Dict[str, Any]) -> float:
        """Calculate how well article matches the claim query."""
        
        query_terms = set(query.lower().split())
        title_terms = set(article.get("title", "").lower().split())
        abstract_terms = set(article.get("abstract", "").lower().split())
        
        title_overlap = len(query_terms & title_terms) / max(len(query_terms), 1)
        abstract_overlap = len(query_terms & abstract_terms) / max(len(query_terms), 1)
        
        # Weight title matches higher
        score = (title_overlap * 0.6) + (abstract_overlap * 0.4)
        
        # Boost for recent publications
        current_year = datetime.now().year
        try:
            pub_year = int(article.get("year", current_year))
        except ValueError:
            pub_year = current_year
        recency_boost = max(0, (5 - (current_year - pub_year)) * 0.02)
        
        return min(1.0, score + recency_boost)
