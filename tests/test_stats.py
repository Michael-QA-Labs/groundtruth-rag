"""Tests for the bootstrap.

Two of these matter more than the rest, because they catch the errors that
produce a confident, plausible, wrong interval:

`test_paired_difference_of_a_variant_against_itself_is_exactly_zero` catches
resampling the two variants independently. That version runs, returns a
sensible-looking interval, and answers a question nobody asked: whether two
independent samples of 24 questions differ, rather than whether the variants
differ on the same questions. It is the whole reason to pair.

`test_one_cluster_containing_everything_collapses_the_interval` catches a
cluster bootstrap that resamples inside clusters instead of resampling
clusters, which would silently restore the independence it exists to remove.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import stats                                                      # noqa: E402


# ------------------------------------------------------------- the interval --

def test_interval_of_a_constant_sample_is_that_constant():
    """Every resample of [0.4]*10 is [0.4]*10, whatever the seed."""
    lo, hi = stats.bootstrap_mean_ci([0.4] * 10, seed=1)
    assert lo == pytest.approx(0.4)
    assert hi == pytest.approx(0.4)


def test_interval_brackets_the_sample_mean():
    values = [0.0] * 12 + [1.0] * 12
    lo, hi = stats.bootstrap_mean_ci(values, seed=1)
    assert lo < 0.5 < hi


def test_interval_is_reproducible_for_a_given_seed():
    values = [0.0, 0.33, 1.0, 0.5, 0.0, 0.67, 1.0, 0.2]
    assert stats.bootstrap_mean_ci(values, seed=7) == stats.bootstrap_mean_ci(values, seed=7)


def test_a_different_seed_gives_a_different_interval():
    """Not a property worth wanting, a fact worth knowing. The interval is a
    random quantity, and reporting one to three decimals implies a precision
    that 2,000 resamples do not have."""
    values = [0.0, 0.33, 1.0, 0.5, 0.0, 0.67, 1.0, 0.2]
    assert stats.bootstrap_mean_ci(values, seed=7) != stats.bootstrap_mean_ci(values, seed=8)


def test_more_data_narrows_the_interval():
    """The property the whole day rests on: 24 questions buy a wide interval
    and there is no way around that except more questions."""
    small = [0.0, 1.0] * 6
    large = [0.0, 1.0] * 60
    lo_s, hi_s = stats.bootstrap_mean_ci(small, seed=3)
    lo_l, hi_l = stats.bootstrap_mean_ci(large, seed=3)
    assert (hi_l - lo_l) < (hi_s - lo_s)


def test_interval_respects_the_requested_confidence_level():
    values = [0.0] * 12 + [1.0] * 12
    wide = stats.bootstrap_mean_ci(values, alpha=0.01, seed=5)
    narrow = stats.bootstrap_mean_ci(values, alpha=0.20, seed=5)
    assert (wide[1] - wide[0]) > (narrow[1] - narrow[0])


def test_empty_sample_raises():
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci([], seed=1)


# --------------------------------------------------------- paired difference --

def test_paired_difference_of_a_variant_against_itself_is_exactly_zero():
    """The test that catches unpaired resampling.

    If the two variants are resampled independently, this returns a non-zero
    interval that looks entirely reasonable, and every comparison in
    results/confidence.md would be answering the wrong question.
    """
    values = [0.0, 0.33, 1.0, 0.5, 0.0, 0.67, 1.0, 0.2]
    lo, hi = stats.paired_diff_ci(values, values, seed=2)
    assert (lo, hi) == (0.0, 0.0)


def test_paired_difference_of_a_constant_shift_is_that_shift():
    values = [0.0, 0.33, 1.0, 0.5]
    shifted = [v + 0.1 for v in values]
    lo, hi = stats.paired_diff_ci(shifted, values, seed=2)
    assert lo == pytest.approx(0.1)
    assert hi == pytest.approx(0.1)


def test_paired_difference_is_first_argument_minus_second():
    lo, hi = stats.paired_diff_ci([1.0, 1.0], [0.0, 0.0], seed=2)
    assert lo > 0


def test_a_difference_carried_by_one_question_of_many_can_include_zero():
    """The situation this project is actually in. 23 questions unchanged and
    one improved by 1.0 is a mean difference of +0.042, and a bootstrap that
    frequently omits that one question cannot exclude zero."""
    variant = [0.0] * 23 + [1.0]
    baseline = [0.0] * 24
    lo, hi = stats.paired_diff_ci(variant, baseline, seed=4)
    assert lo == 0.0 < hi


def test_mismatched_lengths_raise():
    """Two variants scored on different question sets are not paired data, and
    the failure is otherwise silent: zip() would truncate to the shorter."""
    with pytest.raises(ValueError):
        stats.paired_diff_ci([0.1, 0.2, 0.3], [0.1, 0.2], seed=1)


# ------------------------------------------------------------ cluster option --

def test_one_cluster_containing_everything_collapses_the_interval():
    """Resampling clusters, not items inside them. With a single cluster there
    is exactly one possible resample, so the interval is a point."""
    values = [0.0, 0.5, 1.0, 0.25]
    lo, hi = stats.bootstrap_mean_ci(values, clusters=[[0, 1, 2, 3]], seed=1)
    assert lo == hi == pytest.approx(0.4375)


def test_singleton_clusters_reproduce_the_plain_bootstrap():
    values = [0.0, 0.33, 1.0, 0.5, 0.0, 0.67]
    plain = stats.bootstrap_mean_ci(values, seed=11)
    clustered = stats.bootstrap_mean_ci(values, clusters=[[i] for i in range(6)], seed=11)
    assert plain == clustered


def test_clustering_two_correlated_questions_widens_the_interval():
    """Q06 and Q30 both cite doc-05:c032, flagged since Day 4. Treating them as
    one unit means both enter a resample together or neither does, which is
    more honest and slightly less powerful."""
    values = [1.0, 1.0] + [0.0] * 10
    plain = stats.bootstrap_mean_ci(values, seed=6)
    clustered = stats.bootstrap_mean_ci(
        values, clusters=[[0, 1]] + [[i] for i in range(2, 12)], seed=6)
    assert (clustered[1] - clustered[0]) > (plain[1] - plain[0])


def test_clusters_must_cover_every_observation_exactly_once():
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci([0.1, 0.2, 0.3], clusters=[[0, 1]], seed=1)
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci([0.1, 0.2], clusters=[[0, 1], [1]], seed=1)


# ---------------------------------------------------------------- rendering --

def _rows():
    return [
        {"metric": "recall@10", "variant": "hybrid", "mean": 0.433, "ci": (0.271, 0.607)},
        {"metric": "recall@10", "variant": "dense", "mean": 0.362, "ci": (0.203, 0.536)},
    ]


def _diffs():
    return [{"metric": "recall@10", "comparison": "hybrid - dense",
             "diff": 0.071, "ci": (-0.075, 0.217), "excludes_zero": False}]


def test_rendered_report_records_the_seed_and_the_sample_size():
    """Every interval in the file is a function of both. An interval reported
    without its seed cannot be reproduced, and one reported without n invites
    the reader to assume it was computed on more than 24 questions."""
    text = stats.render(_rows(), _diffs(), n=24, seed=20260806, n_resamples=2000)
    assert "20260806" in text
    assert "24" in text
    assert "2000" in text or "2,000" in text


def test_rendered_report_does_not_call_a_touching_interval_significant():
    """The precision@3 comparison has a lower bound of exactly 0.000. A report
    that rounds it into a claim would be the single most misleading line in
    the project."""
    diffs = [{"metric": "precision@3", "comparison": "hybrid - dense",
              "diff": 0.056, "ci": (0.0, 0.125), "excludes_zero": False}]
    text = stats.render(_rows(), diffs, n=24, seed=1, n_resamples=2000).lower()
    assert "significant" not in text


def test_rendered_report_carries_the_sensitivity_checks_when_given_them():
    """The interval alone is not the finding. Whether it moves under a
    different seed, under clustering the one correlated pair, and how many
    questions would settle the comparison are what turn "no" into something
    actionable."""
    sensitivity = {
        "seeds": [(1, (0.0, 0.125)), (2, (0.0, 0.125))],
        "clustered": [("recall@10", (-0.075, 0.217), (-0.069, 0.217))],
        "n_needed": 106,
    }
    text = stats.render(_rows(), _diffs(), n=24, seed=1, n_resamples=2000,
                        sensitivity=sensitivity)
    assert "106" in text
    assert "seed" in text.lower()


def test_sensitivity_section_is_omitted_when_not_supplied():
    text = stats.render(_rows(), _diffs(), n=24, seed=1, n_resamples=2000)
    assert "## Sensitivity" not in text
