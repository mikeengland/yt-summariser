from yt_summariser.summarise.chunking import plan_chunks
from yt_summariser.transcript.models import Segment


def segments(count, chars=40):
    return [Segment(start=i * 10.0, text="a" * chars) for i in range(count)]


def test_transcript_that_fits_is_one_chunk():
    transcript = segments(3)  # 120 chars, about 30 tokens

    chunks = plan_chunks(transcript, budget_tokens=100)

    assert chunks == [transcript]


def test_over_budget_transcript_is_split_in_order_without_losing_segments():
    transcript = segments(5)  # 10 tokens each

    chunks = plan_chunks(transcript, budget_tokens=25)

    assert [len(chunk) for chunk in chunks] == [2, 2, 1]
    assert [s for chunk in chunks for s in chunk] == transcript


def test_a_single_segment_larger_than_the_budget_still_gets_its_own_chunk():
    transcript = segments(1, chars=400) + segments(1)

    chunks = plan_chunks(transcript, budget_tokens=25)

    assert chunks == [[transcript[0]], [transcript[1]]]
