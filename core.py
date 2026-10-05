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
    audio_codec: str = "aac"
    video_bitrate: str = ""
    audio_channels: int | None = None
    audio_sample_rate: int | None = None
    crop_width: int | None = None
    crop_height: int | None = None
    crop_x: int = 0
    crop_y: int = 0
    flip_horizontal: bool = False
    flip_vertical: bool = False
    deinterlace: bool = False
    brightness: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0
    gamma: float = 1.0
    video_speed: float = 1.0
    volume: float = 1.0
    audio_tempo: float = 1.0
    highpass_hz: int | None = None
    lowpass_hz: int | None = None
    audio_normalize: bool = False
    audio_denoise: bool = False
    custom_vf: str = ""
    custom_af: str = ""


def _build_atempo_chain(tempo: float) -> list[str]:
    if tempo <= 0:
        raise ValueError("audio_tempo must be > 0")

    filters: list[str] = []
    remaining = tempo
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.6f}".rstrip("0").rstrip("."))
    return filters


def _validate_options(options: EditOptions) -> None:
    if options.crf < 0 or options.crf > 51:
        raise ValueError("crf must be between 0 and 51")
    if options.width is not None and options.width <= 0:
        raise ValueError("width must be > 0")
    if options.height is not None and options.height <= 0:
        raise ValueError("height must be > 0")
    if (options.width is None) != (options.height is None):
        raise ValueError("width and height must be provided together")
    if options.fps is not None and options.fps <= 0:
        raise ValueError("fps must be > 0")
    if options.crop_width is not None and options.crop_width <= 0:
        raise ValueError("crop_width must be > 0")
    if options.crop_height is not None and options.crop_height <= 0:
        raise ValueError("crop_height must be > 0")
    if (options.crop_width is None) != (options.crop_height is None):
        raise ValueError("crop_width and crop_height must be provided together")
    if options.crop_x < 0 or options.crop_y < 0:
        raise ValueError("crop_x and crop_y must be >= 0")
    if options.rotate not in (0, 90, 180, 270):
        raise ValueError("rotate must be one of 0, 90, 180, 270")
    if options.contrast <= 0:
        raise ValueError("contrast must be > 0")
    if options.saturation <= 0:
        raise ValueError("saturation must be > 0")
    if options.gamma <= 0:
        raise ValueError("gamma must be > 0")
    if options.video_speed <= 0:
        raise ValueError("video_speed must be > 0")
    if options.volume <= 0:
        raise ValueError("volume must be > 0")
    if options.audio_tempo <= 0:
        raise ValueError("audio_tempo must be > 0")
    if options.audio_channels is not None and options.audio_channels <= 0:
        raise ValueError("audio_channels must be > 0")
    if options.audio_sample_rate is not None and options.audio_sample_rate <= 0:
        raise ValueError("audio_sample_rate must be > 0")
    if options.highpass_hz is not None and options.highpass_hz <= 0:
        raise ValueError("highpass_hz must be > 0")
    if options.lowpass_hz is not None and options.lowpass_hz <= 0:
        raise ValueError("lowpass_hz must be > 0")


def _build_video_filters(options: EditOptions) -> list[str]:
    video_filters: list[str] = []
    if options.deinterlace:
        video_filters.append("yadif")
    if options.width and options.height:
        video_filters.append(f"scale={options.width}:{options.height}")
    if options.crop_width and options.crop_height:
        video_filters.append(f"crop={options.crop_width}:{options.crop_height}:{options.crop_x}:{options.crop_y}")

    rotate_map = {
        90: "transpose=1",
        180: "transpose=1,transpose=1",
        270: "transpose=2",
    }
    if options.rotate in rotate_map:
        video_filters.append(rotate_map[options.rotate])
    if options.flip_horizontal:
        video_filters.append("hflip")
    if options.flip_vertical:
        video_filters.append("vflip")
    if options.video_speed != 1.0:
        video_filters.append(f"setpts=PTS/{options.video_speed}")
    if (
        options.brightness != 0.0
        or options.contrast != 1.0
        or options.saturation != 1.0
        or options.gamma != 1.0
    ):
        video_filters.append(
            f"eq=brightness={options.brightness}:contrast={options.contrast}:"
            f"saturation={options.saturation}:gamma={options.gamma}"
        )
    if options.custom_vf.strip():
        video_filters.append(options.custom_vf.strip())

    return video_filters


def _build_audio_filters(options: EditOptions) -> list[str]:
    audio_filters: list[str] = []
    if options.volume != 1.0:
        audio_filters.append(f"volume={options.volume}")
    if options.audio_tempo != 1.0:
        audio_filters.extend(_build_atempo_chain(options.audio_tempo))
    if options.highpass_hz:
        audio_filters.append(f"highpass=f={options.highpass_hz}")
    if options.lowpass_hz:
        audio_filters.append(f"lowpass=f={options.lowpass_hz}")
    if options.audio_normalize:
        audio_filters.append("loudnorm")
    if options.audio_denoise:
        audio_filters.append("afftdn")
    if options.custom_af.strip():
        audio_filters.append(options.custom_af.strip())
    return audio_filters


def build_ffmpeg_command(input_path: str, output_path: str, options: EditOptions) -> list[str]:
    if not input_path or not output_path:
        raise ValueError("input_path and output_path are required")
    _validate_options(options)

    command: list[str] = ["ffmpeg", "-y"]

    if options.start_time:
        command.extend(["-ss", options.start_time])

    command.extend(["-i", input_path])

    if options.end_time:
        command.extend(["-to", options.end_time])

    video_filters = _build_video_filters(options)
    if video_filters:
        command.extend(["-vf", ",".join(video_filters)])

    if options.fps:
        command.extend(["-r", str(options.fps)])

    command.extend(["-c:v", options.video_codec, "-preset", options.preset, "-crf", str(options.crf)])
    if options.video_bitrate.strip():
        command.extend(["-b:v", options.video_bitrate.strip()])

    if options.include_audio:
        command.extend(["-c:a", options.audio_codec, "-b:a", options.audio_bitrate])
        if options.audio_channels:
            command.extend(["-ac", str(options.audio_channels)])
        if options.audio_sample_rate:
            command.extend(["-ar", str(options.audio_sample_rate)])
        audio_filters = _build_audio_filters(options)
        if audio_filters:
            command.extend(["-af", ",".join(audio_filters)])
    else:
        command.append("-an")

    command.extend(["-threads", str(os.cpu_count() or 1), output_path])
    return command
