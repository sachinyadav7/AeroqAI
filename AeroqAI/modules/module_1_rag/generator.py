"""Module 1 — Stage 7: Context Assembly & LLM Generator.

Constructs context-augmented prompts with explicit citations and interfaces
with LLM providers (Mock for fast offline testing/CI, OpenAI for live production generation).
"""
import os
import re
import time
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict, Any, Tuple

from AeroqAI.models.retrieval import SearchResult, RetrievalResult, RerankedSearchResult, RerankResult
from AeroqAI.models.generation import SourceCitation, GenerationResult


DEFAULT_SYSTEM_PROMPT = (
    "You are AeroqAI Assistant, an enterprise knowledge specialist.\n"
    "Answer the user's question accurately, concisely, and strictly based on the provided reference context.\n"
    "If the context does not contain enough information to answer the question, clearly state:\n"
    "\"I cannot find the answer in the provided documents.\"\n"
    "Do not speculate or extrapolate beyond the provided text.\n"
    "Always maintain a professional, objective tone."
)

DEFAULT_USER_TEMPLATE = (
    "Context information is below:\n"
    "---------------------\n"
    "{context}\n"
    "---------------------\n"
    "Given the context information and no other information, answer the question: {query}"
)


class BaseLLMGenerator(ABC):
    """Abstract base class for LLM prompt assembly and text generation."""

    def __init__(
        self,
        model_name: str,
        provider: str,
        system_prompt: Optional[str] = None,
        user_template: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> None:
        self.model_name = model_name
        self.provider = provider
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.user_template = user_template or DEFAULT_USER_TEMPLATE
        self.temperature = temperature
        self.max_tokens = max_tokens

    def assemble_context(
        self,
        context: Union[RetrievalResult, RerankResult, List[SearchResult], List[RerankedSearchResult], List[str], str]
    ) -> Tuple[str, List[SourceCitation]]:
        """Extract and format raw context items into an assembled text block with citations.
        
        Returns:
            Tuple of (assembled_context_string, list_of_source_citations)
        """
        citations: List[SourceCitation] = []
        snippets: List[str] = []

        if isinstance(context, str):
            clean_str = context.strip()
            return clean_str, []

        items = []
        if isinstance(context, (RetrievalResult, RerankResult)):
            items = context.results
        elif isinstance(context, list):
            items = context

        for i, item in enumerate(items, start=1):
            if isinstance(item, (SearchResult, RerankedSearchResult)):
                score = getattr(item, "rerank_score", None)
                if score is None:
                    score = getattr(item, "similarity_score", getattr(item, "original_score", getattr(item, "score", None)))
                
                doc_id_val = getattr(item.chunk, "doc_id", None) or getattr(item.chunk.metadata, "doc_id", "unknown")
                citation = SourceCitation(
                    doc_id=doc_id_val,
                    source_file=item.chunk.metadata.source_file,
                    page_number=item.chunk.metadata.page_number,
                    chunk_id=item.chunk.chunk_id,
                    relevance_score=score,
                    excerpt=item.chunk.content[:150] + ("..." if len(item.chunk.content) > 150 else "")
                )
                citations.append(citation)
                
                header = (
                    f"[Source {i}: {citation.source_file} | Page {citation.page_number} | "
                    f"Chunk: {citation.chunk_id}]"
                )
                snippets.append(f"{header}\n{item.chunk.content.strip()}")

            elif isinstance(item, str):
                snippets.append(f"[Snippet {i}]\n{item.strip()}")

        assembled_text = "\n\n".join(snippets)
        return assembled_text, citations

    def format_prompt(self, query: str, context_text: str) -> str:
        """Format the user prompt template with assembled context and query."""
        return self.user_template.format(context=context_text, query=query.strip())

    @abstractmethod
    def generate(
        self,
        query: str,
        context: Union[RetrievalResult, RerankResult, List[SearchResult], List[RerankedSearchResult], List[str], str],
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        """Generate a grounded response for the query using the provided context."""
        pass


class DeterministicMockGenerator(BaseLLMGenerator):
    """Deterministic offline generator for fast unit testing and CI/CD without API keys."""

    def __init__(
        self,
        model_name: str = "mock-aeroq-v1",
        system_prompt: Optional[str] = None,
        user_template: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> None:
        super().__init__(
            model_name=model_name,
            provider="mock",
            system_prompt=system_prompt,
            user_template=user_template,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def generate(
        self,
        query: str,
        context: Union[RetrievalResult, RerankResult, List[SearchResult], List[RerankedSearchResult], List[str], str],
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        start_time = time.perf_counter()
        assembled_context, citations = self.assemble_context(context)
        formatted_prompt = self.format_prompt(query, assembled_context)

        # Stop words to ignore when matching query terms
        stopwords = {
            "what", "is", "the", "are", "of", "and", "in", "to", "a", "for", "do",
            "does", "how", "many", "when", "can", "it", "be", "on", "with", "as",
            "at", "by", "an", "this", "that", "which", "or", "from", "company",
            "policy", "about", "tell", "me", "give", "explain", "rules"
        }
        def _stem(word: str) -> str:
            for suffix in ("ing", "tion", "tions", "ed", "es", "s", "ly"):
                if word.endswith(suffix) and len(word) > len(suffix) + 2:
                    return word[:-len(suffix)]
            return word

        query_words = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", query.lower())) - stopwords
        query_stems = {_stem(w) for w in query_words}

        # Check if neural reranker decisively rejected candidates (e.g. cross-encoder logit < -2.0)
        has_negative_cross_scores = bool(citations and all(
            c.relevance_score is not None and c.relevance_score < -2.0 for c in citations
        ))

        if not assembled_context.strip() or not query_words or has_negative_cross_scores:
            answer = "I cannot find the answer in the provided documents."
            grounded = False
        else:
            # Clean header tags before extracting sentences
            clean_context = re.sub(r"\[(Source|Snippet)\s+\d+:[^\]]+\]", "", assembled_context)
            sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", clean_context) if s.strip()]
            scored_sentences: List[Tuple[int, str]] = []

            for sentence in sentences:
                s_words = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", sentence.lower()))
                s_stems = {_stem(w) for w in s_words}
                matches = query_stems.intersection(s_stems)
                if matches:
                    scored_sentences.append((len(matches), sentence))

            if scored_sentences:
                scored_sentences.sort(key=lambda x: x[0], reverse=True)
                top_sentences = [sent for _, sent in scored_sentences[:4]]
                
                # Compose synthesis
                source_note = ""
                if citations:
                    first_src = citations[0]
                    source_note = f" (Referencing {first_src.source_file}, Page {first_src.page_number})"
                
                synthesis = "\n- ".join(top_sentences)
                answer = (
                    f"Based on the provided documents{source_note}:\n- {synthesis}"
                )
                grounded = True
            else:
                answer = "I cannot find the answer in the provided documents."
                grounded = False

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Token count estimations
        prompt_tokens = len(formatted_prompt.split())
        completion_tokens = len(answer.split())
        total_tokens = prompt_tokens + completion_tokens

        return GenerationResult(
            query=query,
            answer=answer,
            sources=citations,
            model_name=self.model_name,
            provider=self.provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            prompt_template=self.user_template,
            raw_context=assembled_context,
            grounded=grounded
        )


class OpenAIGenerator(BaseLLMGenerator):
    """Production LLM generator using OpenAI or OpenAI-compatible endpoints."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        user_template: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> None:
        super().__init__(
            model_name=model_name,
            provider="openai",
            system_prompt=system_prompt,
            user_template=user_template,
            temperature=temperature,
            max_tokens=max_tokens
        )
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except Exception as e:
            self.client = None
            self._init_error = str(e)

    def generate(
        self,
        query: str,
        context: Union[RetrievalResult, RerankResult, List[SearchResult], List[RerankedSearchResult], List[str], str],
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is missing. Pass api_key to OpenAIGenerator or set the OPENAI_API_KEY environment variable."
            )
        if self.client is None:
            raise RuntimeError(f"OpenAI client failed to initialize: {getattr(self, '_init_error', 'unknown error')}")

        start_time = time.perf_counter()
        assembled_context, citations = self.assemble_context(context)
        formatted_prompt = self.format_prompt(query, assembled_context)
        active_sys_prompt = system_prompt or self.system_prompt

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": active_sys_prompt},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        choice = response.choices[0]
        answer = choice.message.content or ""
        
        prompt_tokens = response.usage.prompt_tokens if response.usage else None
        completion_tokens = response.usage.completion_tokens if response.usage else None
        total_tokens = response.usage.total_tokens if response.usage else None

        # Check for standard out-of-context refusal phrasing
        refusal_patterns = [
            "cannot find", "not provided in the", "not mentioned in",
            "does not contain", "no information", "cannot be answered"
        ]
        grounded = not any(pat in answer.lower() for pat in refusal_patterns)

        return GenerationResult(
            query=query,
            answer=answer,
            sources=citations,
            model_name=self.model_name,
            provider=self.provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            prompt_template=self.user_template,
            raw_context=assembled_context,
            grounded=grounded
        )


class GroqGenerator(OpenAIGenerator):
    """Ultra-fast production LLM generator powered by Groq LPU inference."""

    def __init__(
        self,
        model_name: str = "openai/gpt-oss-120b",
        api_key: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1",
        system_prompt: Optional[str] = None,
        user_template: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> None:
        # Check explicit key or GROQ_API_KEY / OPENAI_API_KEY
        resolved_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not resolved_key and Path(".env").exists():
            try:
                for line in Path(".env").read_text(encoding="utf-8").splitlines():
                    if line.startswith("GROQ_API_KEY="):
                        resolved_key = line.split("=", 1)[1].strip().strip("'\"")
                        break
            except Exception:
                pass

        super().__init__(
            model_name=model_name,
            api_key=resolved_key,
            base_url=base_url,
            system_prompt=system_prompt,
            user_template=user_template,
            temperature=temperature,
            max_tokens=max_tokens
        )
        self.provider = "groq"


def get_llm_generator(
    provider: str = "mock",
    model_name: Optional[str] = None,
    **kwargs: Any
) -> BaseLLMGenerator:
    """Factory helper to resolve LLM generator instance by provider name."""
    provider_lower = provider.lower()
    if provider_lower in ("mock", "offline", "test"):
        return DeterministicMockGenerator(
            model_name=model_name or "mock-aeroq-v1",
            **kwargs
        )
    elif provider_lower in ("openai", "gpt"):
        return OpenAIGenerator(
            model_name=model_name or "gpt-4o-mini",
            **kwargs
        )
    elif provider_lower in ("groq", "lpu"):
        return GroqGenerator(
            model_name=model_name or "openai/gpt-oss-120b",
            **kwargs
        )
    else:
        raise ValueError(
            f"Unsupported LLM generator provider '{provider}'. Supported providers: 'mock', 'openai', 'groq'."
        )
