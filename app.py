from __future__ import annotations

import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core import EditOptions, build_ffmpeg_command


class FFmpegVideoEditorGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FFmpeg Video Editing GUI")
        self.root.geometry("980x760")

        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.start_time_var = tk.StringVar()
        self.end_time_var = tk.StringVar()
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.fps_var = tk.StringVar()
        self.crf_var = tk.IntVar(value=23)
        self.preset_var = tk.StringVar(value="medium")
        self.rotate_var = tk.StringVar(value="0")
        self.include_audio_var = tk.BooleanVar(value=True)
        self.audio_bitrate_var = tk.StringVar(value="192k")
        self.video_codec_var = tk.StringVar(value="libx264")
        self.audio_codec_var = tk.StringVar(value="aac")
        self.video_bitrate_var = tk.StringVar()
        self.audio_channels_var = tk.StringVar()
        self.audio_sample_rate_var = tk.StringVar()
        self.crop_width_var = tk.StringVar()
        self.crop_height_var = tk.StringVar()
        self.crop_x_var = tk.StringVar(value="0")
        self.crop_y_var = tk.StringVar(value="0")
        self.flip_horizontal_var = tk.BooleanVar(value=False)
        self.flip_vertical_var = tk.BooleanVar(value=False)
        self.deinterlace_var = tk.BooleanVar(value=False)
        self.brightness_var = tk.StringVar(value="0.0")
        self.contrast_var = tk.StringVar(value="1.0")
        self.saturation_var = tk.StringVar(value="1.0")
        self.gamma_var = tk.StringVar(value="1.0")
        self.video_speed_var = tk.StringVar(value="1.0")
        self.volume_var = tk.StringVar(value="1.0")
        self.audio_tempo_var = tk.StringVar(value="1.0")
        self.highpass_hz_var = tk.StringVar()
        self.lowpass_hz_var = tk.StringVar()
        self.audio_normalize_var = tk.BooleanVar(value=False)
        self.audio_denoise_var = tk.BooleanVar(value=False)
        self.custom_vf_var = tk.StringVar()
        self.custom_af_var = tk.StringVar()

        self.status_var = tk.StringVar(value="Ready")
        self.run_button: ttk.Button | None = None
        self.command_preview: tk.Text | None = None

        self._build_layout()

    def _build_layout(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        self._build_file_section(frame)

        notebook = ttk.Notebook(frame)
        notebook.grid(row=1, column=0, sticky=tk.NSEW, pady=(10, 0))

        basic_tab = ttk.Frame(notebook, padding=10)
        video_tab = ttk.Frame(notebook, padding=10)
        audio_tab = ttk.Frame(notebook, padding=10)
        notebook.add(basic_tab, text="Basic")
        notebook.add(video_tab, text="Video Filters (vf)")
        notebook.add(audio_tab, text="Audio Filters (af)")

        self._build_basic_tab(basic_tab)
        self._build_video_tab(video_tab)
        self._build_audio_tab(audio_tab)

        action_row = ttk.Frame(frame)
        action_row.grid(row=2, column=0, sticky=tk.EW, pady=(10, 0))
        action_row.columnconfigure(0, weight=1)
        ttk.Button(action_row, text="Preview FFmpeg Command", command=self.preview_command).grid(
            row=0, column=0, sticky=tk.EW, padx=(0, 8)
        )
        self.run_button = ttk.Button(action_row, text="Run FFmpeg", command=self.run_ffmpeg_async)
        self.run_button.grid(row=0, column=1, sticky=tk.EW)

        preview_container = ttk.LabelFrame(frame, text="Command Preview", padding=8)
        preview_container.grid(row=3, column=0, sticky=tk.NSEW, pady=(10, 0))
        preview_container.columnconfigure(0, weight=1)
        preview_container.rowconfigure(0, weight=1)
        self.command_preview = tk.Text(preview_container, height=7, wrap=tk.WORD)
        self.command_preview.grid(row=0, column=0, sticky=tk.NSEW)
        ttk.Label(frame, textvariable=self.status_var, foreground="#0b5").grid(row=4, column=0, sticky=tk.W, pady=(8, 0))

    def _build_file_section(self, parent: ttk.Frame) -> None:
        files = ttk.LabelFrame(parent, text="Input / Output", padding=10)
        files.grid(row=0, column=0, sticky=tk.EW)
        files.columnconfigure(1, weight=1)
        self._add_file_picker_row(files, 0, "Input file", self.input_path_var, self.pick_input_file)
        self._add_file_picker_row(files, 1, "Output file", self.output_path_var, self.pick_output_file)

    def _build_basic_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(1, weight=1)
        self._add_entry_row(tab, 0, "Start time (hh:mm:ss)", self.start_time_var)
        self._add_entry_row(tab, 1, "End time (hh:mm:ss)", self.end_time_var)
        self._add_entry_row(tab, 2, "FPS", self.fps_var)
        self._add_entry_row(tab, 3, "Video bitrate (ex: 4M)", self.video_bitrate_var)

        ttk.Label(tab, text="CRF (0-51)").grid(row=4, column=0, sticky=tk.W, pady=4)
        ttk.Spinbox(tab, from_=0, to=51, textvariable=self.crf_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=4)

        self._add_combo_row(
            tab,
            5,
            "Preset",
            self.preset_var,
            ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"],
        )
        self._add_combo_row(tab, 6, "Video codec", self.video_codec_var, ["libx264", "libx265", "libvpx-vp9", "libaom-av1"])

    def _build_video_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(1, weight=1)
        self._add_entry_row(tab, 0, "Scale width", self.width_var)
        self._add_entry_row(tab, 1, "Scale height", self.height_var)
        self._add_combo_row(tab, 2, "Rotate", self.rotate_var, ["0", "90", "180", "270"])

        crop = ttk.LabelFrame(tab, text="Crop", padding=8)
        crop.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(8, 4))
        for idx in range(4):
            crop.columnconfigure(idx, weight=1)
        ttk.Label(crop, text="Width").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(crop, textvariable=self.crop_width_var).grid(row=1, column=0, sticky=tk.EW, padx=(0, 4))
        ttk.Label(crop, text="Height").grid(row=0, column=1, sticky=tk.W)
        ttk.Entry(crop, textvariable=self.crop_height_var).grid(row=1, column=1, sticky=tk.EW, padx=4)
        ttk.Label(crop, text="X").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(crop, textvariable=self.crop_x_var).grid(row=1, column=2, sticky=tk.EW, padx=4)
        ttk.Label(crop, text="Y").grid(row=0, column=3, sticky=tk.W)
        ttk.Entry(crop, textvariable=self.crop_y_var).grid(row=1, column=3, sticky=tk.EW, padx=(4, 0))

        checks = ttk.Frame(tab)
        checks.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=8)
        ttk.Checkbutton(checks, text="Flip horizontal (hflip)", variable=self.flip_horizontal_var).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(checks, text="Flip vertical (vflip)", variable=self.flip_vertical_var).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(checks, text="Deinterlace (yadif)", variable=self.deinterlace_var).pack(side=tk.LEFT)

        tune = ttk.LabelFrame(tab, text="Color / Speed", padding=8)
        tune.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=4)
        for idx in range(5):
            tune.columnconfigure(idx, weight=1)
        self._add_inline_entry(tune, 0, "Brightness", self.brightness_var)
        self._add_inline_entry(tune, 1, "Contrast", self.contrast_var)
        self._add_inline_entry(tune, 2, "Saturation", self.saturation_var)
        self._add_inline_entry(tune, 3, "Gamma", self.gamma_var)
        self._add_inline_entry(tune, 4, "Video speed", self.video_speed_var)

        self._add_entry_row(tab, 6, "Custom vf (appended)", self.custom_vf_var)

    def _build_audio_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(1, weight=1)
        ttk.Checkbutton(tab, text="Include audio", variable=self.include_audio_var).grid(row=0, column=0, sticky=tk.W, pady=(0, 6))
        self._add_combo_row(tab, 1, "Audio codec", self.audio_codec_var, ["aac", "libopus", "libmp3lame"])
        self._add_entry_row(tab, 2, "Audio bitrate (ex: 192k)", self.audio_bitrate_var)
        self._add_entry_row(tab, 3, "Audio channels (ex: 2)", self.audio_channels_var)
        self._add_entry_row(tab, 4, "Audio sample rate (ex: 48000)", self.audio_sample_rate_var)
        self._add_entry_row(tab, 5, "Volume (1.0=default)", self.volume_var)
        self._add_entry_row(tab, 6, "Audio tempo (0.5-2.0 each stage, auto-chain)", self.audio_tempo_var)
        self._add_entry_row(tab, 7, "Highpass Hz", self.highpass_hz_var)
        self._add_entry_row(tab, 8, "Lowpass Hz", self.lowpass_hz_var)
        ttk.Checkbutton(tab, text="Normalize audio (loudnorm)", variable=self.audio_normalize_var).grid(row=9, column=0, sticky=tk.W, pady=3)
        ttk.Checkbutton(tab, text="Denoise audio (afftdn)", variable=self.audio_denoise_var).grid(row=10, column=0, sticky=tk.W, pady=3)
        self._add_entry_row(tab, 11, "Custom af (appended)", self.custom_af_var)

    @staticmethod
    def _add_entry_row(frame: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=variable).grid(row=row, column=1, columnspan=2, sticky=tk.EW, pady=4)

    @staticmethod
    def _add_combo_row(frame: ttk.Frame, row: int, label: str, variable: tk.StringVar, values: list[str]) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        ttk.Combobox(frame, textvariable=variable, values=values, state="readonly").grid(row=row, column=1, sticky=tk.W, pady=4)

    @staticmethod
    def _add_file_picker_row(frame: ttk.Frame, row: int, label: str, variable: tk.StringVar, command) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=variable).grid(row=row, column=1, sticky=tk.EW, pady=4)
        ttk.Button(frame, text="Browse", command=command).grid(row=row, column=2, sticky=tk.E, padx=(8, 0), pady=4)

    @staticmethod
    def _add_inline_entry(frame: ttk.Frame, column: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(frame, text=label).grid(row=0, column=column, sticky=tk.W)
        ttk.Entry(frame, textvariable=variable).grid(row=1, column=column, sticky=tk.EW, padx=4)

    @staticmethod
    def _parse_optional_int(value: str, field_name: str) -> int | None:
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(stripped)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an integer") from exc

    @staticmethod
    def _parse_float(value: str, field_name: str) -> float:
        try:
            return float(value.strip())
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a number") from exc

    def _collect_options(self) -> EditOptions:
        return EditOptions(
            start_time=self.start_time_var.get().strip(),
            end_time=self.end_time_var.get().strip(),
            width=self._parse_optional_int(self.width_var.get(), "width"),
            height=self._parse_optional_int(self.height_var.get(), "height"),
            fps=self._parse_optional_int(self.fps_var.get(), "fps"),
            crf=int(self.crf_var.get()),
            preset=self.preset_var.get().strip(),
            rotate=int(self.rotate_var.get().strip() or "0"),
            include_audio=self.include_audio_var.get(),
            audio_bitrate=self.audio_bitrate_var.get().strip() or "192k",
            video_codec=self.video_codec_var.get().strip(),
            audio_codec=self.audio_codec_var.get().strip(),
            video_bitrate=self.video_bitrate_var.get().strip(),
            audio_channels=self._parse_optional_int(self.audio_channels_var.get(), "audio_channels"),
            audio_sample_rate=self._parse_optional_int(self.audio_sample_rate_var.get(), "audio_sample_rate"),
            crop_width=self._parse_optional_int(self.crop_width_var.get(), "crop_width"),
            crop_height=self._parse_optional_int(self.crop_height_var.get(), "crop_height"),
            crop_x=int(self.crop_x_var.get().strip() or "0"),
            crop_y=int(self.crop_y_var.get().strip() or "0"),
            flip_horizontal=self.flip_horizontal_var.get(),
            flip_vertical=self.flip_vertical_var.get(),
            deinterlace=self.deinterlace_var.get(),
            brightness=self._parse_float(self.brightness_var.get(), "brightness"),
            contrast=self._parse_float(self.contrast_var.get(), "contrast"),
            saturation=self._parse_float(self.saturation_var.get(), "saturation"),
            gamma=self._parse_float(self.gamma_var.get(), "gamma"),
            video_speed=self._parse_float(self.video_speed_var.get(), "video_speed"),
            volume=self._parse_float(self.volume_var.get(), "volume"),
            audio_tempo=self._parse_float(self.audio_tempo_var.get(), "audio_tempo"),
            highpass_hz=self._parse_optional_int(self.highpass_hz_var.get(), "highpass_hz"),
            lowpass_hz=self._parse_optional_int(self.lowpass_hz_var.get(), "lowpass_hz"),
            audio_normalize=self.audio_normalize_var.get(),
            audio_denoise=self.audio_denoise_var.get(),
            custom_vf=self.custom_vf_var.get(),
            custom_af=self.custom_af_var.get(),
        )

    def _build_command_from_form(self) -> list[str]:
        input_path = self.input_path_var.get().strip()
        output_path = self.output_path_var.get().strip()
        if not input_path or not output_path:
            raise ValueError("Input file and output file are required.")
        if not Path(input_path).is_file():
            raise ValueError("Input file does not exist.")

        options = self._collect_options()
        return build_ffmpeg_command(input_path, output_path, options)

    def pick_input_file(self) -> None:
        path = filedialog.askopenfilename(title="Select input video")
        if path:
            self.input_path_var.set(path)
            if not self.output_path_var.get():
                source = Path(path)
                self.output_path_var.set(str(source.with_name(f"{source.stem}_edited.mp4")))

    def pick_output_file(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Select output video",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
        )
        if path:
            self.output_path_var.set(path)

    def preview_command(self) -> None:
        try:
            command = self._build_command_from_form()
        except ValueError as exc:
            messagebox.showerror("Validation error", str(exc))
            return

        if self.command_preview:
            self.command_preview.delete("1.0", tk.END)
            self.command_preview.insert(tk.END, " ".join(command))
        self.status_var.set("Preview updated")

    def run_ffmpeg_async(self) -> None:
        if shutil.which("ffmpeg") is None:
            messagebox.showerror("FFmpeg not found", "ffmpeg command was not found in PATH.")
            return

        try:
            command = self._build_command_from_form()
        except ValueError as exc:
            messagebox.showerror("Validation error", str(exc))
            return

        if self.command_preview:
            self.command_preview.delete("1.0", tk.END)
            self.command_preview.insert(tk.END, " ".join(command))

        if self.run_button:
            self.run_button.config(state=tk.DISABLED)
        self.status_var.set("Processing...")

        thread = threading.Thread(target=self._run_ffmpeg, args=(command,), daemon=True)
        thread.start()

    def _run_ffmpeg(self, command: list[str]) -> None:
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        self.root.after(0, self._on_process_done, process.returncode, process.stderr)

    def _on_process_done(self, return_code: int, stderr: str) -> None:
        if self.run_button:
            self.run_button.config(state=tk.NORMAL)
        if return_code == 0:
            self.status_var.set("Done")
            messagebox.showinfo("Success", "Video processing completed.")
            return

        self.status_var.set("Failed")
        error_tail = "\n".join(stderr.strip().splitlines()[-20:])
        messagebox.showerror("FFmpeg failed", error_tail or "Unknown FFmpeg error.")


def main() -> None:
    root = tk.Tk()
    FFmpegVideoEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
