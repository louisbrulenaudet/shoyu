from enum import Enum

__all__ = [
    "Region",
    "SafeSearch",
    "TimeLimit",
    "Backend",
    "USER_AGENTS",
    "ACCEPT_LANGUAGES",
    "REFERERS",
]


class Region(str, Enum):
    """
    Enum representing supported search regions/locales.
    """
    WT_WT = "wt-wt"
    US_EN = "us-en"
    UK_EN = "uk-en"
    RU_RU = "ru-ru"
    FR_FR = "fr-fr"
    DE_DE = "de-de"
    ES_ES = "es-es"
    IT_IT = "it-it"
    NL_NL = "nl-nl"
    PL_PL = "pl-pl"
    TR_TR = "tr-tr"
    PT_PT = "pt-pt"
    AR_AR = "ar-ar"
    ZH_CN = "zh-cn"
    ZH_TW = "zh-tw"
    JA_JP = "ja-jp"
    KO_KR = "ko-kr"

class SafeSearch(str, Enum):
    """
    Enum representing safe search filtering levels.
    """
    ON = "on"
    MODERATE = "moderate"
    OFF = "off"

class TimeLimit(str, Enum):
    """
    Enum representing time range filters for search results.
    """
    DAY = "d"
    WEEK = "w"
    MONTH = "m"
    YEAR = "y"
    NONE = None

class Backend(str, Enum):
    """
    Enum representing backend modes for search.
    """
    AUTO = "auto"
    HTML = "html"
    LITE = "lite"

class ErrorCodes(str, Enum):
    TOR_NOT_FOUND = "TOR_NOT_FOUND"
    TOR_LAUNCH_FAILED = "TOR_LAUNCH_FAILED"
    TOR_BIND_FAILED = "TOR_BIND_FAILED"
    TOR_CONNECTION_FAILED = "TOR_CONNECTION_FAILED"
    TOR_AUTH_FAILED = "TOR_AUTH_FAILED"
    TOR_COMMAND_FAILED = "TOR_COMMAND_FAILED"
    SEARCH_CLIENT_NOT_INITIALIZED = "SEARCH_CLIENT_NOT_INITIALIZED"
    SEARCH_FAILED = "SEARCH_FAILED"
    IDENTITY_ROTATION_FAILED = "IDENTITY_ROTATION_FAILED"
    UNEXPECTED_RESULT_TYPE = "UNEXPECTED_RESULT_TYPE"
    GENERAL_RUNTIME_ERROR = "GENERAL_RUNTIME_ERROR"
    PORT_BIND_FAILED = "PORT_BIND_FAILED"
    PROCESS_TIMEOUT = "PROCESS_TIMEOUT"
    PROCESS_LOOKUP_FAILED = "PROCESS_LOOKUP_FAILED"

# List of common user agent strings for HTTP requests.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Android 10; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0",
    "Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows   NT 6.1; WOW64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 6.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 5.1; rv:68.0) Gecko/20100101 Firefox/68.0",
    "Mozilla/5.0 (Windows NT 5.0; rv:68.0) Gecko/20100101 Firefox/68.0",
    "Mozilla/5.0 (Windows NT 4.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 3.1; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 2.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 1.0; Win64; x64) AppleWebKit/537.36",
]

# List of common Accept-Language headers for HTTP requests.
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8",
    "es-ES,es;q=0.9,en;q=0.8",
    "it-IT,it;q=0.9,en;q=0.8",
    "ru-RU,ru;q=0.9,en;q=0.8",
]

# List of common referer URLs for HTTP requests.
REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://search.yahoo.com/",
    "https://www.ecosia.org/",
    "https://www.startpage.com/",
]
