"""Unit tests for Module 2: Automated Evaluation Engine."""
import json
from unittest.mock import MagicMock, patch
import pytest

from AeroqAI.models.evaluation import (
    EvaluationSample,
    MetricScore,
    SampleEvaluationResult,
    BenchmarkReport
)
from AeroqAI.modules.module_2_evaluation.evaluator import (
    BaseEvaluator,
    DeterministicEvaluator,
    LLMJudgeEvaluator,
    get_evaluator
)


def test_evaluation_sample_contract():
    """Verify EvaluationSample model validation and attributes."""
    sample = EvaluationSample(
        sample_id="test_01",
        query="What is the leave policy?",
        ground_truth_answer="Employees get 20 days paid leave.",
        reference_contexts=["20 days of paid annual leave are accrued annually."],
        metadata={"page": 3, "topic": "leave"}
    )
    assert sample.sample_id == "test_01"
    assert sample.metadata["page"] == 3
    assert len(sample.reference_contexts) == 1


def test_deterministic_evaluator_faithfulness():
    """Verify deterministic faithfulness scoring against context."""
    evaluator = DeterministicEvaluator()

    # Grounded answer
    grounded_ans = "Standard full-time employees receive 20 days of paid annual leave."
    context = ["Standard full-time employees receive 20 days of paid annual leave per calendar year."]
    res = evaluator.evaluate_faithfulness("leave policy", grounded_ans, context)
    assert res.score >= 0.8
    assert "directly corroborated" in res.reasoning

    # Clean refusal when no context is provided
    res_refusal = evaluator.evaluate_faithfulness("spaceship policy", "I cannot find the answer in the provided documents.", [])
    assert res_refusal.score == 1.0

    # Fabricated answer with empty context
    res_hallucination = evaluator.evaluate_faithfulness("warp drive", "Warp drives require dilithium crystals.", [])
    assert res_hallucination.score == 0.0


def test_deterministic_evaluator_correctness():
    """Verify semantic and factual correctness against ground truth."""
    evaluator = DeterministicEvaluator()

    gt = "Employees receive 20 days of annual paid leave."
    generated = "Employees receive 20 days of annual paid leave."
    score = evaluator.evaluate_correctness("leave days", generated, gt)
    assert score.score >= 0.9

    # Both are clean refusals
    gt_ref = "I cannot find the answer in the provided documents."
    ans_ref = "I cannot find the answer in the provided documents."
    ref_score = evaluator.evaluate_correctness("spaceships", ans_ref, gt_ref)
    assert ref_score.score == 1.0

    # Completely wrong answer
    wrong_ans = "Employees must work 80 hours a week with zero vacation."
    wrong_score = evaluator.evaluate_correctness("leave days", wrong_ans, gt)
    assert wrong_score.score < 0.3


def test_deterministic_evaluator_context_precision():
    """Verify context precision evaluates relevance of retrieved passages."""
    evaluator = DeterministicEvaluator()

    query = "What is the hybrid remote work policy?"
    relevant_ctx = ["Global Tech operates on a flexible hybrid work model with 3 days in office."]
    irrelevant_ctx = ["The corporate parking lot is closed on weekends."]

    # High precision when all chunks are relevant
    p_high = evaluator.evaluate_context_precision(query, relevant_ctx)
    assert p_high.score == 1.0

    # Half precision when 1 of 2 chunks is relevant
    p_med = evaluator.evaluate_context_precision(query, relevant_ctx + irrelevant_ctx)
    assert p_med.score == 0.5


def test_evaluate_sample_composite():
    """Verify evaluate_sample calculates weighted composite score and pass flag."""
    evaluator = DeterministicEvaluator(pass_threshold=0.70)
    sample = EvaluationSample(
        sample_id="sample_01",
        query="annual paid leave allowance",
        ground_truth_answer="Employees receive 20 days of paid leave per year.",
        reference_contexts=["Full-time employees receive 20 days of paid leave per calendar year."]
    )

    gen_answer = "Employees receive 20 days of paid leave per year."
    retrieved = ["Full-time employees receive 20 days of paid leave per calendar year."]

    result = evaluator.evaluate_sample(sample, gen_answer, retrieved)
    assert isinstance(result, SampleEvaluationResult)
    assert result.overall_score >= 0.70
    assert result.passed is True
    assert result.faithfulness.score > 0
    assert result.answer_correctness.score > 0
    assert result.context_precision.score > 0


def test_evaluate_dataset_benchmark_report():
    """Verify evaluate_dataset computes aggregate statistics and format table."""
    evaluator = DeterministicEvaluator(pass_threshold=0.70)
    samples = [
        EvaluationSample(
            sample_id="s1",
            query="leave allowance",
            ground_truth_answer="20 days annual leave",
            reference_contexts=["20 days annual leave per year."]
        ),
        EvaluationSample(
            sample_id="s2",
            query="core hours",
            ground_truth_answer="10:00 AM to 4:00 PM EST",
            reference_contexts=["Core operational hours are 10:00 AM to 4:00 PM EST."]
        )
    ]

    def mock_pipeline(query: str):
        if "leave" in query:
            return "20 days annual leave.", ["20 days annual leave per year."]
        return "10:00 AM to 4:00 PM EST.", ["Core operational hours are 10:00 AM to 4:00 PM EST."]

    report = evaluator.evaluate_dataset("HR Benchmark", samples, mock_pipeline)
    assert isinstance(report, BenchmarkReport)
    assert report.total_samples == 2
    assert report.passed_samples == 2
    assert report.pass_rate == 100.0
    assert report.mean_overall_score >= 0.70

    summary_table = report.format_summary_table()
    assert "AeroqAI Evaluation Benchmark Report" in summary_table
    assert "Faithfulness" in summary_table
    assert "✅ PASS" in summary_table


def test_evaluator_factory():
    """Verify get_evaluator resolves supported providers and validates bad ones."""
    det_eval = get_evaluator("deterministic")
    assert isinstance(det_eval, DeterministicEvaluator)
    assert det_eval.provider == "deterministic"

    groq_eval = get_evaluator("groq", api_key="test-key")
    assert isinstance(groq_eval, LLMJudgeEvaluator)
    assert groq_eval.provider == "groq"

    with pytest.raises(ValueError, match="Unsupported evaluator provider"):
        get_evaluator("invalid_provider")


def test_llm_judge_mocked_calls():
    """Verify LLMJudgeEvaluator parses JSON score and reasoning from LLM."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "score": 0.95,
        "reasoning": "Answer is strictly grounded in the context."
    })
    mock_resp.choices = [mock_choice]

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_openai.return_value = mock_client

        evaluator = LLMJudgeEvaluator(api_key="fake-groq-key")
        score = evaluator.evaluate_faithfulness(
            query="leave days",
            generated_answer="20 days",
            contexts=["Employees receive 20 days leave."]
        )
        assert score.score == 0.95
        assert "strictly grounded" in score.reasoning
