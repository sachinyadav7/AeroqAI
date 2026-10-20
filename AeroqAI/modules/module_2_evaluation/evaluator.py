"""
Module 2: Automated Evaluation Engine.

Implements the Evaluation Triad:
  1. Faithfulness (Groundedness / Hallucination Detection)
  2. Answer Correctness (Factual & Semantic Alignment with Ground Truth)
  3. Context Relevance / Precision (Quality of Retrieved Chunks)

Supports both:
  - DeterministicEvaluator (heuristic, offline, instant for CI/CD)
  - LLMJudgeEvaluator (LLM-as-a-Judge via Groq or OpenAI for human-grade semantic evaluation)
"""
import json
import os
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple, Union

from AeroqAI.models.evaluation import (
    EvaluationSample,
    MetricScore,
    SampleEvaluationResult,
    BenchmarkReport
)


class BaseEvaluator(ABC):
    """Abstract base class for RAG quality evaluation engines."""

    def __init__(
        self,
        model_name: str,
        provider: str,
        pass_threshold: float = 0.70
    ) -> None:
        self.model_name = model_name
        self.provider = provider
        self.pass_threshold = pass_threshold

    @abstractmethod
    def evaluate_faithfulness(
        self,
        query: str,
        generated_answer: str,
        contexts: List[str]
    ) -> MetricScore:
        """Measure whether the generated answer is strictly grounded in the retrieved contexts."""
        pass

    @abstractmethod
    def evaluate_correctness(
        self,
        query: str,
        generated_answer: str,
        ground_truth: str
    ) -> MetricScore:
        """Measure whether the generated answer aligns factually with the ground truth answer."""
        pass

    @abstractmethod
    def evaluate_context_precision(
        self,
        query: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> MetricScore:
        """Measure whether the retrieved contexts are relevant and free from extraneous noise."""
        pass

    def evaluate_sample(
        self,
        sample: EvaluationSample,
        generated_answer: str,
        retrieved_contexts: List[str]
    ) -> SampleEvaluationResult:
        """Evaluate a single test case across all three Triad metrics."""
        start_time = time.perf_counter()

        faith = self.evaluate_faithfulness(sample.query, generated_answer, retrieved_contexts)
        corr = self.evaluate_correctness(sample.query, generated_answer, sample.ground_truth_answer)
        prec = self.evaluate_context_precision(sample.query, retrieved_contexts, sample.ground_truth_answer)

        # Composite score: 40% Faithfulness + 40% Correctness + 20% Context Precision
        overall = round(0.40 * faith.score + 0.40 * corr.score + 0.20 * prec.score, 4)
        passed = overall >= self.pass_threshold
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return SampleEvaluationResult(
            sample_id=sample.sample_id,
            query=sample.query,
            generated_answer=generated_answer,
            ground_truth_answer=sample.ground_truth_answer,
            retrieved_contexts=retrieved_contexts,
            faithfulness=faith,
            answer_correctness=corr,
            context_precision=prec,
            overall_score=overall,
            passed=passed,
            eval_latency_ms=round(latency_ms, 2)
        )

    def evaluate_dataset(
        self,
        dataset_name: str,
        samples: List[EvaluationSample],
        pipeline_fn: Callable[[str], Tuple[str, List[str]]]
    ) -> BenchmarkReport:
        """
        Execute benchmark evaluation over a list of EvaluationSamples.
        
        Args:
            dataset_name: Name of the benchmark dataset.
            samples: List of EvaluationSample test cases.
            pipeline_fn: Callable accepting a query string and returning (generated_answer, list_of_context_strings).
        """
        start_time = time.perf_counter()
        results: List[SampleEvaluationResult] = []

        for sample in samples:
            generated_answer, retrieved_contexts = pipeline_fn(sample.query)
            sample_res = self.evaluate_sample(
                sample=sample,
                generated_answer=generated_answer,
                retrieved_contexts=retrieved_contexts
            )
            results.append(sample_res)

        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        failed_count = total - passed_count
        pass_rate = round((passed_count / max(1, total)) * 100.0, 2)

        mean_faith = round(sum(r.faithfulness.score for r in results) / max(1, total), 4)
        mean_corr = round(sum(r.answer_correctness.score for r in results) / max(1, total), 4)
        mean_prec = round(sum(r.context_precision.score for r in results) / max(1, total), 4)
        mean_overall = round(sum(r.overall_score for r in results) / max(1, total), 4)
        total_latency = (time.perf_counter() - start_time) * 1000.0

        return BenchmarkReport(
            dataset_name=dataset_name,
            evaluator_model=f"{self.provider} ({self.model_name})",
            total_samples=total,
            passed_samples=passed_count,
            failed_samples=failed_count,
            pass_rate=pass_rate,
            mean_faithfulness=mean_faith,
            mean_correctness=mean_corr,
            mean_context_precision=mean_prec,
            mean_overall_score=mean_overall,
            total_eval_latency_ms=round(total_latency, 2),
            sample_results=results
        )


class DeterministicEvaluator(BaseEvaluator):
    """
    Offline heuristic evaluator for automated test suites and fast CI/CD runs.
    Uses token Jaccard overlap, stem matching, and containment heuristics.
    """

    def __init__(
        self,
        model_name: str = "deterministic-heuristic-v1",
        pass_threshold: float = 0.70
    ) -> None:
        super().__init__(
            model_name=model_name,
            provider="deterministic",
            pass_threshold=pass_threshold
        )

    def _tokenize(self, text: str) -> set:
        stopwords = {
            "what", "is", "the", "are", "of", "and", "in", "to", "a", "for", "do",
            "does", "how", "many", "when", "can", "it", "be", "on", "with", "as",
            "at", "by", "an", "this", "that", "which", "or", "from"
        }
        words = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower()))
        return words - stopwords

    def _stem(self, word: str) -> str:
        for suffix in ("ing", "tion", "tions", "ed", "es", "s", "ly"):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word

    def evaluate_faithfulness(
        self,
        query: str,
        generated_answer: str,
        contexts: List[str]
    ) -> MetricScore:
        # Check for correct refusal on out-of-domain queries
        refusal_phrases = ["cannot find", "not mentioned", "not provided", "no information"]
        is_refusal = any(p in generated_answer.lower() for p in refusal_phrases)

        if not contexts or all(not c.strip() for c in contexts):
            if is_refusal:
                return MetricScore(score=1.0, reasoning="Correctly refused to answer when no context was available.")
            return MetricScore(score=0.0, reasoning="Answer generated without supporting context (hallucination).")

        if is_refusal:
            return MetricScore(score=1.0, reasoning="Properly stated inability to find answer in context.")

        combined_context = " ".join(contexts).lower()
        ans_words = self._tokenize(generated_answer)
        if not ans_words:
            return MetricScore(score=1.0, reasoning="No substantive claims made.")

        context_stems = {self._stem(w) for w in self._tokenize(combined_context)}
        supported = sum(1 for w in ans_words if self._stem(w) in context_stems)
        ratio = supported / len(ans_words)
        score = round(min(1.0, max(0.0, ratio)), 4)
        return MetricScore(
            score=score,
            reasoning=f"{supported}/{len(ans_words)} answer words directly corroborated by context ({score * 100:.1f}%)."
        )

    def evaluate_correctness(
        self,
        query: str,
        generated_answer: str,
        ground_truth: str
    ) -> MetricScore:
        refusal_phrases = ["cannot find", "not mentioned", "not provided", "no information"]
        gt_is_refusal = any(p in ground_truth.lower() for p in refusal_phrases)
        ans_is_refusal = any(p in generated_answer.lower() for p in refusal_phrases)

        if gt_is_refusal and ans_is_refusal:
            return MetricScore(score=1.0, reasoning="Both generated answer and ground truth are clean refusals.")

        gt_words = {self._stem(w) for w in self._tokenize(ground_truth)}
        ans_words = {self._stem(w) for w in self._tokenize(generated_answer)}

        if not gt_words or not ans_words:
            return MetricScore(score=0.0, reasoning="Empty answer or ground truth.")

        intersection = gt_words.intersection(ans_words)
        union = gt_words.union(ans_words)
        jaccard = len(intersection) / len(union) if union else 0.0

        # Recall of ground truth key terms is given higher weight (60% recall + 40% jaccard)
        recall = len(intersection) / len(gt_words) if gt_words else 0.0
        score = round(min(1.0, max(0.0, 0.60 * recall + 0.40 * jaccard)), 4)

        return MetricScore(
            score=score,
            reasoning=f"Recall: {recall * 100:.1f}%, Jaccard: {jaccard * 100:.1f}%, Matched {len(intersection)}/{len(gt_words)} concepts."
        )

    def evaluate_context_precision(
        self,
        query: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> MetricScore:
        if not contexts:
            return MetricScore(score=0.0, reasoning="No context chunks retrieved.")

        query_stems = {self._stem(w) for w in self._tokenize(query)}
        if not query_stems:
            return MetricScore(score=1.0, reasoning="Query contains only stopwords.")

        relevant_chunks = 0
        for ctx in contexts:
            ctx_stems = {self._stem(w) for w in self._tokenize(ctx)}
            if query_stems.intersection(ctx_stems):
                relevant_chunks += 1

        precision = relevant_chunks / len(contexts)
        score = round(min(1.0, max(0.0, precision)), 4)
        return MetricScore(
            score=score,
            reasoning=f"{relevant_chunks}/{len(contexts)} retrieved chunks contain keywords relevant to the query."
        )


class LLMJudgeEvaluator(BaseEvaluator):
    """
    LLM-as-a-Judge semantic evaluator.
    Utilizes Groq (or OpenAI) to evaluate complex semantic alignment,
    groundedness nuance, and context relevance with rich structured reasoning.
    """

    def __init__(
        self,
        model_name: str = "openai/gpt-oss-120b",
        api_key: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1",
        provider: str = "groq",
        pass_threshold: float = 0.70
    ) -> None:
        super().__init__(
            model_name=model_name,
            provider=provider,
            pass_threshold=pass_threshold
        )
        resolved_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not resolved_key and Path(".env").exists():
            try:
                for line in Path(".env").read_text(encoding="utf-8").splitlines():
                    if line.startswith("GROQ_API_KEY="):
                        resolved_key = line.split("=", 1)[1].strip().strip("'\"")
                        break
            except Exception:
                pass

        self.api_key = resolved_key
        self.base_url = base_url
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except Exception as e:
            self.client = None
            self._init_error = str(e)

    def _call_llm_judge(self, prompt: str) -> Dict[str, Any]:
        """Send prompt to LLM and parse JSON response containing score and reasoning."""
        if not self.api_key or self.client is None:
            raise RuntimeError("LLMJudge requires a valid API key (GROQ_API_KEY or OPENAI_API_KEY).")

        system_msg = (
            "You are an impartial, highly rigorous AI evaluation judge for RAG systems.\n"
            "You evaluate quality across Faithfulness, Correctness, and Context Relevance.\n"
            "You must return ONLY a valid JSON object with exact keys 'score' (float between 0.0 and 1.0) "
            "and 'reasoning' (concise string explanation)."
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
            score = float(data.get("score", 0.0))
            score = min(1.0, max(0.0, score))
            reasoning = str(data.get("reasoning", "No reasoning provided."))
            return {"score": score, "reasoning": reasoning}
        except Exception:
            return {"score": 0.5, "reasoning": f"Failed to parse LLM judge response: {content[:100]}"}

    def evaluate_faithfulness(
        self,
        query: str,
        generated_answer: str,
        contexts: List[str]
    ) -> MetricScore:
        prompt = (
            f"Evaluate the FAITHFULNESS of the following generated answer against the reference context.\n\n"
            f"Question: {query}\n\n"
            f"Reference Context:\n" + ("\n---\n".join(contexts) if contexts else "[NO CONTEXT]") + "\n\n"
            f"Generated Answer:\n{generated_answer}\n\n"
            "Criteria:\n"
            "- Score 1.0: Every factual claim in the answer is completely supported by the context.\n"
            "- Score 0.0: The answer contains false, contradictory, or fabricated claims not present in the context.\n"
            "- If the context does not contain the answer and the answer accurately states that, score 1.0.\n"
            "Return JSON: {\"score\": float, \"reasoning\": string}"
        )
        res = self._call_llm_judge(prompt)
        return MetricScore(score=res["score"], reasoning=res["reasoning"])

    def evaluate_correctness(
        self,
        query: str,
        generated_answer: str,
        ground_truth: str
    ) -> MetricScore:
        prompt = (
            f"Evaluate the ANSWER CORRECTNESS of the generated answer compared to the ground truth answer.\n\n"
            f"Question: {query}\n\n"
            f"Ground Truth Answer:\n{ground_truth}\n\n"
            f"Generated Answer:\n{generated_answer}\n\n"
            "Criteria:\n"
            "- Score 1.0: The generated answer captures all critical facts and matches the ground truth in substance.\n"
            "- Score 0.5 - 0.9: Mostly correct but missing minor secondary details.\n"
            "- Score 0.0 - 0.4: Factual errors, omissions of core answers, or contradiction.\n"
            "- If both state the question cannot be answered from the docs, score 1.0.\n"
            "Return JSON: {\"score\": float, \"reasoning\": string}"
        )
        res = self._call_llm_judge(prompt)
        return MetricScore(score=res["score"], reasoning=res["reasoning"])

    def evaluate_context_precision(
        self,
        query: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> MetricScore:
        prompt = (
            f"Evaluate the CONTEXT PRECISION of the retrieved passages for answering the query.\n\n"
            f"Question: {query}\n\n"
            f"Ground Truth Answer:\n{ground_truth or '[NOT PROVIDED]'}\n\n"
            f"Retrieved Passages:\n" + ("\n---\n".join(contexts) if contexts else "[NO CONTEXT]") + "\n\n"
            "Criteria:\n"
            "- Score 1.0: The retrieved passages are directly relevant, highly targeted, and contain the information needed.\n"
            "- Score 0.5: Passages are partially relevant but contain substantial irrelevant filler.\n"
            "- Score 0.0: Passages are completely irrelevant or unrelated to the question.\n"
            "Return JSON: {\"score\": float, \"reasoning\": string}"
        )
        res = self._call_llm_judge(prompt)
        return MetricScore(score=res["score"], reasoning=res["reasoning"])


def get_evaluator(
    provider: str = "deterministic",
    model_name: Optional[str] = None,
    pass_threshold: float = 0.70,
    **kwargs: Any
) -> BaseEvaluator:
    """Factory helper to resolve evaluator engines."""
    prov_lower = provider.lower().strip()
    if prov_lower in ("deterministic", "mock", "heuristic", "offline"):
        return DeterministicEvaluator(
            model_name=model_name or "deterministic-heuristic-v1",
            pass_threshold=pass_threshold
        )
    elif prov_lower in ("groq", "lpu"):
        return LLMJudgeEvaluator(
            model_name=model_name or "openai/gpt-oss-120b",
            provider="groq",
            base_url="https://api.groq.com/openai/v1",
            pass_threshold=pass_threshold,
            **kwargs
        )
    elif prov_lower in ("openai", "gpt"):
        return LLMJudgeEvaluator(
            model_name=model_name or "gpt-4o-mini",
            provider="openai",
            base_url="https://api.openai.com/v1",
            pass_threshold=pass_threshold,
            **kwargs
        )
    else:
        raise ValueError(
            f"Unsupported evaluator provider '{provider}'. Expected 'deterministic', 'groq', or 'openai'."
        )
