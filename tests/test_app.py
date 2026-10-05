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


if __name__ == "__main__":
    unittest.main()
