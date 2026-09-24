import json

from yt_summariser.transcript.models import VideoInfo


def render_note(info: VideoInfo, source: str, provider: str, model: str, body: str) -> str:
    frontmatter = [
        "---",
        f"title: {json.dumps(info.title)}",
        f"url: {info.url}",
        f"video_id: {info.video_id}",
        f"channel: {json.dumps(info.channel)}",
        f"published: {info.published}",
        f"duration: {info.duration}",
        "tags: [youtube]",
        f"transcript_source: {source}",
        f"provider: {provider}",
        f"model: {model}",
        "---",
    ]
    return "\n".join(frontmatter) + f"\n\n# {info.title}\n\n[Watch on YouTube]({info.url})\n\n{body.strip()}\n"
