from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class EditOptions:
    start_time: str = ""
    end_time: str = ""
    width: int | None = None
    height: int | None = None
    fps: int | None = None
    crf: int = 23
    preset: str = "medium"
    rotate: int = 0
    include_audio: bool = True
    audio_bitrate: str = "192k"
    video_codec: str = "libx264"


def build_ffmpeg_command(input_path: str, output_path: str, options: EditOptions) -> list[str]:
    if not input_path or not output_path:
        raise ValueError("input_path and output_path are required")

    command: list[str] = ["ffmpeg", "-y"]

    if options.start_time:
        command.extend(["-ss", options.start_time])

    command.extend(["-i", input_path])

    if options.end_time:
        command.extend(["-to", options.end_time])

    video_filters: list[str] = []
    if options.width and options.height:
        video_filters.append(f"scale={options.width}:{options.height}")

    rotate_map = {
        90: "transpose=1",
        180: "transpose=1,transpose=1",
        270: "transpose=2",
    }
    if options.rotate in rotate_map:
        video_filters.append(rotate_map[options.rotate])

    if video_filters:
        command.extend(["-vf", ",".join(video_filters)])

    if options.fps:
        command.extend(["-r", str(options.fps)])

    command.extend(["-c:v", options.video_codec, "-preset", options.preset, "-crf", str(options.crf)])

    if options.include_audio:
        command.extend(["-c:a", "aac", "-b:a", options.audio_bitrate])
    else:
        command.append("-an")

    command.extend(["-threads", str(os.cpu_count() or 1), output_path])
    return command
