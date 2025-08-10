from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SearchResult:
    """
    Immutable container for a single search result.

    Attributes:
        title (str): Title of the search result.
        url (str): URL of the result.
        snippet (str): Text snippet or description of the result.
        source (str): Identifier for the search engine source (e.g., "duckduckgo").

    Usage:
        Used as the standard result object for all search backends.
    """

    title: str
    url: str
    snippet: str
    source: str

    @classmethod
    def from_ddgs(cls, raw: dict) -> "SearchResult":
        """
        Create a SearchResult instance from a DuckDuckGo search response dictionary.

        Args:
            raw (dict): Raw response dictionary from DDGS. Expected keys are:
                - "title": Title of the result.
                - "href": URL of the result.
                - "body": Snippet or description.
                - "source": Source identifier (optional, defaults to "duckduckgo").

        Returns:
            SearchResult: Parsed and validated search result object.

        Notes:
            Handles missing fields gracefully by substituting empty strings or default values.
        """
        return cls(
            title=raw.get("title", ""),
            url=raw.get("href", ""),
            snippet=raw.get("body", ""),
            source=raw.get("source", "duckduckgo"),
        )
