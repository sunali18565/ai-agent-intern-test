from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class DocumentChunk:
    filename: str
    document_id: str
    title: str
    status: str
    effective_date: str
    last_reviewed: str
    audience: str
    policy_authority: str
    heading: str
    text: str
    metadata: dict[str, Any]


class KnowledgeBaseRetriever:
    """Authority-aware and intent-aware RAG retriever."""

    def __init__(self, knowledge_base_dir: str | Path):
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.chunks: list[DocumentChunk] = []

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )

        self.matrix = None
        self.load_documents()

    def load_documents(self) -> None:
        """Load Markdown files and create heading-based chunks."""

        self.chunks.clear()

        for path in sorted(self.knowledge_base_dir.glob("*.md")):
            content = path.read_text(encoding="utf-8")

            metadata, body = self._parse_front_matter(content)
            sections = self._split_by_headings(body)

            for heading, text in sections:
                if not text.strip():
                    continue

                self.chunks.append(
                    DocumentChunk(
                        filename=path.name,
                        document_id=metadata.get("document_id", ""),
                        title=metadata.get("title", ""),
                        status=metadata.get("status", ""),
                        effective_date=metadata.get("effective_date", ""),
                        last_reviewed=metadata.get("last_reviewed", ""),
                        audience=metadata.get("audience", ""),
                        policy_authority=metadata.get(
                            "policy_authority", ""
                        ),
                        heading=heading,
                        text=text.strip(),
                        metadata=metadata.copy(),
                    )
                )

        if not self.chunks:
            raise ValueError(
                f"No Markdown documents found in {self.knowledge_base_dir}"
            )

        texts = [
            f"{chunk.heading} {chunk.heading} "
            f"{chunk.title} {chunk.text}"
            for chunk in self.chunks
        ]

        self.matrix = self.vectorizer.fit_transform(texts)

    @staticmethod
    def _parse_front_matter(
        content: str,
    ) -> tuple[dict[str, str], str]:

        content = content.lstrip()

        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)

        if len(parts) != 3:
            return {}, content

        raw_metadata = parts[1]
        body = parts[2].strip()

        metadata: dict[str, str] = {}

        for line in raw_metadata.splitlines():
            line = line.strip()

            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

        return metadata, body

    @staticmethod
    def _split_by_headings(
        body: str,
    ) -> list[tuple[str, str]]:

        matches = list(
            re.finditer(
                r"(?m)^#{1,6}\s+(.+?)\s*$",
                body,
            )
        )

        if not matches:
            return [("Document", body)]

        sections = []

        for index, match in enumerate(matches):
            heading = match.group(1).strip()

            start = match.end()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(body)

            text = body[start:end].strip()

            sections.append((heading, text))

        return sections

    @staticmethod
    def _authority_score(
        chunk: DocumentChunk,
    ) -> float:

        score = 0.0

        if chunk.policy_authority.lower() == "official":
            score += 3.0

        if chunk.status.lower() == "active":
            score += 3.0

        if chunk.status.lower() == "superseded":
            score -= 6.0

        if chunk.status.lower() in {
            "draft",
            "archived",
        }:
            score -= 3.0

        # Migration notes are never authoritative policy.
        if "migration" in chunk.filename.lower():
            score -= 6.0

        return score

    @staticmethod
    def _query_words(
        query: str,
    ) -> set[str]:

        return set(
            re.findall(
                r"\b[a-z0-9]+\b",
                query.lower(),
            )
        )

    @classmethod
    def _heading_bonus(
        cls,
        query: str,
        heading: str,
    ) -> float:

        query_words = cls._query_words(query)

        heading_words = set(
            re.findall(
                r"\b[a-z0-9]+\b",
                heading.lower(),
            )
        )

        overlap = len(query_words & heading_words)

        return min(
            overlap * 0.08,
            0.24,
        )

    @staticmethod
    def _intent_bonus(
        query: str,
        chunk: DocumentChunk,
    ) -> float:

        q = query.lower()
        filename = chunk.filename.lower()
        heading = chunk.heading.lower()
        text = chunk.text.lower()

        bonus = 0.0

        # =========================================================
        # PROMPT-INJECTION / POLICY-SECURITY INTENT
        # =========================================================
        #
        # A user may explicitly mention a migration note, ask the
        # agent to ignore the real policy, or request a fake policy
        # such as "60 days".
        #
        # These phrases should route retrieval toward the current
        # official policy, NOT toward a migration/legacy document.
        # =========================================================

        injection_signals = [
            "migration note",
            "migration notes",
            "ignore the real policy",
            "ignore real policy",
            "ignore the policy",
            "newer document",
            "give everyone 60 days",
            "60 days",
            "approve my return",
            "automatically approve",
        ]

        injection_intent = any(
            signal in q
            for signal in injection_signals
        )

        if injection_intent:

            # Current official Returns Policy
            if filename == "01-returns-policy-current.md":
                if "standard return window" in heading:
                    bonus += 0.60
                else:
                    bonus += 0.05

            # Legacy policy must NOT win.
            if filename == "02-returns-policy-legacy.md":
                bonus -= 0.60

            # Migration notes must never become authority.
            if "migration" in filename:
                bonus -= 0.80

            # A TrailPlus return window is only relevant when the
            # user explicitly mentions TrailPlus.
            if (
                filename == "09-trailplus-membership.md"
                and "trailplus" not in q
                and "membership" not in q
            ):
                bonus -= 0.20

        # =========================================================
        # Standard return policy
        # =========================================================

        standard_signals = [
            "regular customer",
            "standard customer",
            "standard plan",
            "unused backpack",
            "unused item",
            "return window",
            "how long",
            "return",
            "return policy",
            "return days",
            "days to return",
        ]

        if any(
            signal in q
            for signal in standard_signals
        ):

            if filename == "01-returns-policy-current.md":

                if "standard return window" in heading:
                    bonus += 0.35
                else:
                    bonus += 0.12

            if filename == "02-returns-policy-legacy.md":
                bonus -= 0.20

            if (
                "trailplus" in filename
                or "trailplus" in text
            ):
                if (
                    "trailplus" not in q
                    and "membership" not in q
                ):
                    bonus -= 0.12

        # =========================================================
        # TrailPlus
        # =========================================================

        if (
            "trailplus" in q
            or "membership" in q
        ):

            if "09-trailplus-membership.md" in filename:
                bonus += 0.40

            if filename == "01-returns-policy-current.md":
                bonus -= 0.05

        # =========================================================
        # International shipping
        # =========================================================

        countries = [
            "canada",
            "germany",
            "international",
            "country",
            "ship internationally",
        ]

        if any(
            word in q
            for word in countries
        ):

            if filename == "06-international-shipping.md":
                bonus += 0.35

        # =========================================================
        # Warranty
        # =========================================================

        if "warranty" in q:

            if filename == "07-warranty.md":
                bonus += 0.35

        # =========================================================
        # Product care
        # =========================================================

        care_terms = [
            "dishwasher",
            "dishwasher safe",
            "wash",
            "care",
            "tumbler",
        ]

        if any(
            term in q
            for term in care_terms
        ):

            if filename in {
                "11-product-care.md",
                "12-breeze-tumbler-product-card.md",
            }:
                bonus += 0.30

        # =========================================================
        # Final sale / damaged
        # =========================================================

        if (
            "final-sale" in q
            or "final sale" in q
            or "broken" in q
            or "damaged" in q
            or "wrong item" in q
        ):

            if filename in {
                "03-final-sale-and-promotions.md",
                "04-damaged-or-wrong-items.md",
            }:
                bonus += 0.30

        return bonus

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:

        if not query.strip():
            return []

        if self.matrix is None:
            raise RuntimeError(
                "Retriever has not been indexed."
            )

        query_vector = self.vectorizer.transform(
            [query]
        )

        similarities = cosine_similarity(
            query_vector,
            self.matrix,
        )[0]

        candidates = []

        for index, similarity in enumerate(similarities):

            chunk = self.chunks[index]

            intent_bonus = self._intent_bonus(
                query,
                chunk,
            )

            # Allow a strong intent match to rescue
            # zero TF-IDF similarity.
            if (
                similarity <= 0
                and intent_bonus <= 0
            ):
                continue

            authority = self._authority_score(
                chunk
            )

            heading_bonus = self._heading_bonus(
                query,
                chunk.heading,
            )

            final_score = (
                float(similarity)
                + heading_bonus
                + intent_bonus
                + (authority * 0.05)
            )

            candidates.append(
                {
                    "chunk": chunk,
                    "similarity": float(similarity),
                    "authority_score": authority,
                    "heading_bonus": heading_bonus,
                    "intent_bonus": intent_bonus,
                    "score": final_score,
                }
            )

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        results = []

        for item in candidates[:top_k]:

            chunk = item["chunk"]

            results.append(
                {
                    "filename": chunk.filename,
                    "document_id": chunk.document_id,
                    "title": chunk.title,
                    "heading": chunk.heading,
                    "text": chunk.text,
                    "status": chunk.status,
                    "effective_date": chunk.effective_date,
                    "last_reviewed": chunk.last_reviewed,
                    "audience": chunk.audience,
                    "policy_authority": chunk.policy_authority,
                    "similarity": round(
                        item["similarity"],
                        4,
                    ),
                    "authority_score": item[
                        "authority_score"
                    ],
                    "heading_bonus": round(
                        item["heading_bonus"],
                        4,
                    ),
                    "intent_bonus": round(
                        item["intent_bonus"],
                        4,
                    ),
                    "score": round(
                        item["score"],
                        4,
                    ),
                    "metadata": chunk.metadata,
                }
            )

        return results


if __name__ == "__main__":

    kb_path = (
        Path(__file__).resolve().parent.parent
        / "knowledge-base"
    )

    retriever = KnowledgeBaseRetriever(
        kb_path
    )

    query = (
        "Can you ship an Atlas Weekender "
        "to Germany?"
    )

    results = retriever.retrieve(
        query,
        top_k=5,
    )

    for result in results:

        print("=" * 70)

        print(
            f"Source: {result['filename']}"
        )

        print(
            f"Heading: {result['heading']}"
        )

        print(
            f"Status: {result['status']}"
        )

        print(
            f"Similarity: {result['similarity']}"
        )

        print(
            f"Heading Bonus: {result['heading_bonus']}"
        )

        print(
            f"Intent Bonus: {result['intent_bonus']}"
        )

        print(
            f"Score: {result['score']}"
        )

        print(
            result["text"]
        )