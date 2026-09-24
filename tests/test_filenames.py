from yt_summariser.output.filenames import Combination, plan_output_path

COMBO = Combination(video_id="abc123", source="manual", provider="claude", model="sonnet")


def test_free_name_uses_plain_title(tmp_path):
    plan = plan_output_path(tmp_path, "How Rust Works", COMBO)

    assert plan.path == tmp_path / "How Rust Works.md"
    assert not plan.skipped


def test_illegal_characters_are_replaced(tmp_path):
    plan = plan_output_path(tmp_path, 'Rust: is it *fast*? A/B "test"', COMBO)

    assert plan.path == tmp_path / "Rust - is it fast A-B test.md"


def write_note(path, combo):
    path.write_text(
        "---\n"
        f"video_id: {combo.video_id}\n"
        f"transcript_source: {combo.source}\n"
        f"provider: {combo.provider}\n"
        f"model: {combo.model}\n"
        "---\n# note\n"
    )


def test_existing_plain_name_for_other_combination_gets_long_name(tmp_path):
    write_note(tmp_path / "How Rust Works.md", Combination("abc123", "auto", "openai", "gpt"))

    plan = plan_output_path(tmp_path, "How Rust Works", COMBO)

    assert plan.path == tmp_path / "How Rust Works [manual · claude-sonnet].md"
    assert not plan.skipped


def test_same_combination_already_written_is_skipped(tmp_path):
    existing = tmp_path / "How Rust Works.md"
    write_note(existing, COMBO)

    plan = plan_output_path(tmp_path, "How Rust Works", COMBO)

    assert plan.skipped
    assert plan.path == existing


def test_duplicate_is_found_under_the_long_name_too(tmp_path):
    write_note(tmp_path / "How Rust Works.md", Combination("abc123", "auto", "openai", "gpt"))
    existing = tmp_path / "How Rust Works [manual · claude-sonnet].md"
    write_note(existing, COMBO)

    plan = plan_output_path(tmp_path, "How Rust Works", COMBO)

    assert plan.skipped
    assert plan.path == existing


def test_force_overwrites_the_duplicate_instead_of_skipping(tmp_path):
    existing = tmp_path / "How Rust Works.md"
    write_note(existing, COMBO)

    plan = plan_output_path(tmp_path, "How Rust Works", COMBO, force=True)

    assert plan.path == existing
    assert not plan.skipped


def test_long_name_taken_by_another_video_gets_video_id(tmp_path):
    other = Combination("zzz999", "manual", "claude", "sonnet")
    write_note(tmp_path / "How Rust Works.md", other)
    write_note(tmp_path / "How Rust Works [manual · claude-sonnet].md", other)

    plan = plan_output_path(tmp_path, "How Rust Works", COMBO)

    assert plan.path == tmp_path / "How Rust Works [manual · claude-sonnet] (abc123).md"


def test_unrelated_title_sharing_a_prefix_is_not_a_collision(tmp_path):
    write_note(tmp_path / "Rust Tutorial.md", Combination("zzz999", "manual", "claude", "sonnet"))

    plan = plan_output_path(tmp_path, "Rust", COMBO)

    assert plan.path == tmp_path / "Rust.md"


def test_long_titles_are_trimmed_to_120_characters(tmp_path):
    plan = plan_output_path(tmp_path, "x" * 300, COMBO)

    assert plan.path == tmp_path / ("x" * 120 + ".md")


def test_transcript_files_use_their_own_suffix_and_do_not_clash_with_summaries(tmp_path):
    write_note(tmp_path / "How Rust Works.md", COMBO)

    plan = plan_output_path(tmp_path, "How Rust Works", COMBO, kind="transcript")

    assert plan.path == tmp_path / "How Rust Works.transcript.md"
    assert not plan.skipped
