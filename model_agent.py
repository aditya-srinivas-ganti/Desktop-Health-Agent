import json
import re
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_FILE = BASE_DIR / "models.json"
LOG_FILE = BASE_DIR / "computer_health.log"

LOOKBACK_YEARS = 3

HEADERS = {
    "User-Agent": (
        "DesktopHealthAgent/1.0 "
        "(AI Model Release Monitor)"
    )
}

REQUEST_TIMEOUT = 20


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | MODEL_AGENT | %(levelname)s | %(message)s"
)

logger = logging.getLogger("model_agent")


# ============================================================
# SOURCE CONFIGURATION
# ============================================================

SOURCES = [
    {
        "company": "OpenAI",
        "url": "https://openai.com/news/",
        "domain": "openai.com"
    },
    {
        "company": "Anthropic",
        "url": "https://www.anthropic.com/news",
        "domain": "anthropic.com"
    },
    {
        "company": "Google DeepMind",
        "url": "https://deepmind.google/blog/",
        "domain": "deepmind.google"
    }
]


# ============================================================
# HELPERS
# ============================================================

def load_models():
    """
    Load existing models.json.
    """

    if not MODEL_FILE.exists():
        return []

    try:
        with MODEL_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError) as error:
        logger.error("Unable to read models.json: %s", error)
        return []


def save_models(models):
    """
    Save model database.
    """

    try:
        models.sort(
            key=lambda item: item.get("date", ""),
            reverse=True
        )

        with MODEL_FILE.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                models,
                file,
                indent=4,
                ensure_ascii=False
            )

        logger.info(
            "Saved %d models to models.json",
            len(models)
        )

    except OSError as error:
        logger.error(
            "Unable to save models.json: %s",
            error
        )


def normalize_name(name):
    """
    Normalize model names for duplicate detection.
    """

    return re.sub(
        r"[^a-z0-9]",
        "",
        name.lower()
    )


def is_duplicate(model, existing_models):
    """
    Check whether a model already exists.
    """

    model_name = normalize_name(
        model.get("name", "")
    )

    company = model.get(
        "company",
        ""
    ).lower()

    for existing in existing_models:

        existing_name = normalize_name(
            existing.get("name", "")
        )

        existing_company = existing.get(
            "company",
            ""
        ).lower()

        if (
            model_name == existing_name
            and company == existing_company
        ):
            return True

    return False


def within_lookback(date_string):
    """
    Check whether a release is inside
    the configured three-year window.
    """

    try:
        release_date = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).replace(tzinfo=timezone.utc)

        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(days=365 * LOOKBACK_YEARS)
        )

        return release_date >= cutoff

    except ValueError:
        return False


def parse_date(text):
    """
    Extract a date from text.

    Supports formats such as:

    August 7, 2025
    Aug 7, 2025
    July 2026
    2025-08-07
    """

    patterns = [
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},\s+\d{4}\b",

        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
        r"\.?\s+\d{1,2},\s+\d{4}\b",

        r"\b\d{4}-\d{2}-\d{2}\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        value = match.group(0)

        for fmt in (
            "%B %d, %Y",
            "%b %d, %Y",
            "%b. %d, %Y",
            "%Y-%m-%d"
        ):
            try:
                return datetime.strptime(
                    value,
                    fmt
                ).strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None


def detect_model_name(title):
    """
    Try to determine whether a page title
    appears to announce a model.
    """

    title_lower = title.lower()

    keywords = [
        "gpt",
        "claude",
        "gemini",
        "llama",
        "mistral",
        "model",
        "sonnet",
        "opus",
        "haiku",
        "deepseek",
        "qwen",
        "nova",
        "command",
        "robotics",
        "genie",
        "lyria"
    ]

    if any(
        keyword in title_lower
        for keyword in keywords
    ):
        return title.strip()

    return None


def classify_model(title, description):
    """
    Basic automatic categorization.
    """

    text = (
        title + " " + description
    ).lower()

    if any(
        x in text
        for x in [
            "reasoning",
            "thinking",
            "think longer"
        ]
    ):
        model_type = "Reasoning"

    elif any(
        x in text
        for x in [
            "vision",
            "multimodal",
            "image",
            "video"
        ]
    ):
        model_type = "Multimodal"

    elif any(
        x in text
        for x in [
            "coding",
            "code",
            "developer"
        ]
    ):
        model_type = "Coding"

    elif any(
        x in text
        for x in [
            "robot",
            "robotics",
            "physical"
        ]
    ):
        model_type = "Robotics"

    elif any(
        x in text
        for x in [
            "audio",
            "speech",
            "voice"
        ]
    ):
        model_type = "Audio"

    else:
        model_type = "General"

    return model_type


# ============================================================
# SOURCE SCRAPER
# ============================================================

def fetch_source(source):
    """
    Download an official source page.
    """

    logger.info(
        "Checking %s: %s",
        source["company"],
        source["url"]
    )

    try:

        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as error:

        logger.error(
            "Failed to fetch %s: %s",
            source["company"],
            error
        )

        return None


def extract_articles(html, source):
    """
    Extract likely release articles.

    This intentionally uses broad extraction because
    publisher layouts change over time.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    results = []

    for link in soup.find_all("a", href=True):

        title = link.get_text(
            " ",
            strip=True
        )

        if not title:
            continue

        model_name = detect_model_name(title)

        if not model_name:
            continue

        href = link.get("href")

        if not href:
            continue

        article_url = urljoin(
            source["url"],
            href
        )

        # Collect nearby text as description.
        parent = link.parent

        description = ""

        if parent:
            description = parent.get_text(
                " ",
                strip=True
            )

        # Look around the link if necessary.
        if len(description) < 80:

            container = link.find_parent(
                ["article", "div", "section", "li"]
            )

            if container:
                description = container.get_text(
                    " ",
                    strip=True
                )

        release_date = parse_date(
            description
        )

        if not release_date:

            release_date = parse_date(
                title
            )

        if not release_date:
            continue

        if not within_lookback(
            release_date
        ):
            continue

        results.append({
            "name": model_name,
            "company": source["company"],
            "date": release_date,
            "type": classify_model(
                title,
                description
            ),
            "category": "AI Model",
            "description": description[:500],
            "url": article_url,
            "source": source["company"],
            "discovered_at": datetime.now(
                timezone.utc
            ).isoformat()
        })

    return results


# ============================================================
# CLEANUP
# ============================================================

def remove_old_models(models):
    """
    Keep only models from the last three years.
    """

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=365 * LOOKBACK_YEARS)
    )

    cleaned = []

    for model in models:

        try:

            release_date = datetime.strptime(
                model["date"],
                "%Y-%m-%d"
            ).replace(
                tzinfo=timezone.utc
            )

            if release_date >= cutoff:
                cleaned.append(model)

        except (
            KeyError,
            ValueError
        ):
            logger.warning(
                "Removing invalid model entry: %s",
                model
            )

    return cleaned


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent():

    logger.info(
        "================ MODEL AGENT STARTED ================"
    )

    existing_models = load_models()

    logger.info(
        "Existing model count: %d",
        len(existing_models)
    )

    discovered_models = []

    for source in SOURCES:

        html = fetch_source(source)

        if not html:
            continue

        articles = extract_articles(
            html,
            source
        )

        logger.info(
            "%s: discovered %d candidate models",
            source["company"],
            len(articles)
        )

        discovered_models.extend(
            articles
        )

    new_count = 0

    for model in discovered_models:

        if is_duplicate(
            model,
            existing_models
        ):
            continue

        existing_models.append(
            model
        )

        new_count += 1

        logger.info(
            "NEW MODEL: %s | %s | %s",
            model["name"],
            model["company"],
            model["date"]
        )

    existing_models = remove_old_models(
        existing_models
    )

    save_models(
        existing_models
    )

    logger.info(
        "New models added: %d",
        new_count
    )

    logger.info(
        "Final model count: %d",
        len(existing_models)
    )

    logger.info(
        "================ MODEL AGENT FINISHED ================"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_agent()