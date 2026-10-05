import unittest

from core import EditOptions, build_ffmpeg_command


class BuildFFmpegCommandTests(unittest.TestCase):
    def test_builds_default_command(self) -> None:
        command = build_ffmpeg_command("input.mp4", "output.mp4", EditOptions())
        self.assertEqual(command[0:5], ["ffmpeg", "-y", "-i", "input.mp4", "-c:v"])
        self.assertIn("libx264", command)
        self.assertIn("output.mp4", command)

    def test_combines_scale_and_rotate_filters(self) -> None:
        options = EditOptions(width=1280, height=720, rotate=90)
        command = build_ffmpeg_command("in.mp4", "out.mp4", options)
        vf_index = command.index("-vf")
        self.assertEqual(command[vf_index + 1], "scale=1280:720,transpose=1")

    def test_disables_audio_when_requested(self) -> None:
        command = build_ffmpeg_command("in.mp4", "out.mp4", EditOptions(include_audio=False))
        self.assertIn("-an", command)
        self.assertNotIn("-c:a", command)

    def test_adds_trim_and_fps_options(self) -> None:
        options = EditOptions(start_time="00:00:10", end_time="00:00:30", fps=30)
        command = build_ffmpeg_command("in.mp4", "out.mp4", options)
        self.assertEqual(command[2:4], ["-ss", "00:00:10"])
        self.assertIn("-to", command)
        self.assertIn("00:00:30", command)
        self.assertIn("-r", command)

    def test_adds_extended_video_filter_chain(self) -> None:
        options = EditOptions(
            width=1920,
            height=1080,
            crop_width=1280,
            crop_height=720,
            crop_x=10,
            crop_y=20,
            flip_horizontal=True,
            flip_vertical=True,
            deinterlace=True,
            brightness=0.1,
            contrast=1.2,
            saturation=1.3,
            gamma=0.9,
            video_speed=1.25,
            custom_vf="unsharp=5:5:1.0:5:5:0.0",
        )
        command = build_ffmpeg_command("in.mp4", "out.mp4", options)
        vf = command[command.index("-vf") + 1]
        self.assertIn("yadif", vf)
        self.assertIn("scale=1920:1080", vf)
        self.assertIn("crop=1280:720:10:20", vf)
        self.assertIn("hflip", vf)
        self.assertIn("vflip", vf)
        self.assertIn("setpts=PTS/1.25", vf)
        self.assertIn("eq=brightness=0.1:contrast=1.2:saturation=1.3:gamma=0.9", vf)
        self.assertTrue(vf.endswith("unsharp=5:5:1.0:5:5:0.0"))

    def test_adds_extended_audio_filter_chain(self) -> None:
        options = EditOptions(
            audio_codec="libopus",
            audio_bitrate="256k",
            audio_channels=2,
            audio_sample_rate=48000,
            volume=1.5,
            audio_tempo=3.0,
            highpass_hz=120,
            lowpass_hz=15000,
            audio_normalize=True,
            audio_denoise=True,
            custom_af="acompressor=threshold=-12dB:ratio=3",
        )
        command = build_ffmpeg_command("in.mp4", "out.mp4", options)
        self.assertIn("-c:a", command)
        self.assertIn("libopus", command)
        self.assertIn("-ac", command)
        self.assertIn("2", command)
        self.assertIn("-ar", command)
        self.assertIn("48000", command)
        af = command[command.index("-af") + 1]
        self.assertIn("volume=1.5", af)
        self.assertIn("atempo=2.0", af)
        self.assertIn("atempo=1.5", af)
        self.assertIn("highpass=f=120", af)
        self.assertIn("lowpass=f=15000", af)
        self.assertIn("loudnorm", af)
        self.assertIn("afftdn", af)
        self.assertTrue(af.endswith("acompressor=threshold=-12dB:ratio=3"))

    def test_raises_for_invalid_dimension_pair(self) -> None:
        with self.assertRaises(ValueError):
            build_ffmpeg_command("in.mp4", "out.mp4", EditOptions(width=1280))

    def test_raises_for_invalid_crop_pair(self) -> None:
        with self.assertRaises(ValueError):
            build_ffmpeg_command("in.mp4", "out.mp4", EditOptions(crop_width=640))

    def test_raises_for_invalid_rotate(self) -> None:
        with self.assertRaises(ValueError):
            build_ffmpeg_command("in.mp4", "out.mp4", EditOptions(rotate=45))


if __name__ == "__main__":
    unittest.main()
