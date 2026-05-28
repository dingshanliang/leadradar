from __future__ import annotations

import hashlib

from bs4 import BeautifulSoup

from leadradar.crawlers.base import DocumentParser, RawPage


class HtmlDocumentParser(DocumentParser):
    def extract_text(self, page: RawPage) -> str:
        soup = BeautifulSoup(page.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
