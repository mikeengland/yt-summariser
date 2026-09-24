from yt_summariser.summarise.timestamps import link_timestamps


def test_valid_citation_becomes_a_youtube_link():
    result = link_timestamps("- Rust has no GC [02:05]", video_id="abc123", duration=600)

    assert result == "- Rust has no GC [02:05](https://youtu.be/abc123?t=125)"


def test_citation_beyond_video_duration_is_dropped():
    result = link_timestamps("- Made-up claim [15:00]", video_id="abc123", duration=600)

    assert result == "- Made-up claim"


def test_hour_citation_is_linked():
    result = link_timestamps("- Late point [1:02:03]", video_id="abc123", duration=7200)

    assert result == "- Late point [1:02:03](https://youtu.be/abc123?t=3723)"


def test_placeholder_citation_copied_from_the_prompt_is_dropped():
    result = link_timestamps("- Trunks are long [mm:ss]", video_id="abc123", duration=600)

    assert result == "- Trunks are long"
