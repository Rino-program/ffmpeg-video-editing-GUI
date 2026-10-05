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
        self.root.geometry("760x480")

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

        self.status_var = tk.StringVar(value="Ready")
        self.run_button: ttk.Button | None = None

        self._build_layout()

    def _build_layout(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        frame.columnconfigure(1, weight=1)

        self._add_file_picker_row(frame, 0, "Input file", self.input_path_var, self.pick_input_file)
        self._add_file_picker_row(frame, 1, "Output file", self.output_path_var, self.pick_output_file)

        self._add_entry_row(frame, 2, "Start time (hh:mm:ss)", self.start_time_var)
        self._add_entry_row(frame, 3, "End time (hh:mm:ss)", self.end_time_var)

        self._add_entry_row(frame, 4, "Width", self.width_var)
        self._add_entry_row(frame, 5, "Height", self.height_var)
        self._add_entry_row(frame, 6, "FPS", self.fps_var)

        ttk.Label(frame, text="CRF (0-51)").grid(row=7, column=0, sticky=tk.W, pady=4)
        ttk.Spinbox(frame, from_=0, to=51, textvariable=self.crf_var, width=10).grid(row=7, column=1, sticky=tk.W, pady=4)

        self._add_combo_row(frame, 8, "Preset", self.preset_var, ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"])
        self._add_combo_row(frame, 9, "Rotate", self.rotate_var, ["0", "90", "180", "270"])
        self._add_combo_row(frame, 10, "Video codec", self.video_codec_var, ["libx264", "libx265", "libvpx-vp9"])

        audio_frame = ttk.Frame(frame)
        audio_frame.grid(row=11, column=0, columnspan=3, sticky=tk.W, pady=8)
        ttk.Checkbutton(audio_frame, text="Include audio", variable=self.include_audio_var).pack(side=tk.LEFT)
        ttk.Label(audio_frame, text="Audio bitrate").pack(side=tk.LEFT, padx=(16, 8))
        ttk.Entry(audio_frame, textvariable=self.audio_bitrate_var, width=10).pack(side=tk.LEFT)

        self.run_button = ttk.Button(frame, text="Run FFmpeg", command=self.run_ffmpeg_async)
        self.run_button.grid(row=12, column=0, columnspan=3, sticky=tk.EW, pady=(16, 6))

        ttk.Label(frame, textvariable=self.status_var, foreground="#0b5").grid(row=13, column=0, columnspan=3, sticky=tk.W)

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

    def run_ffmpeg_async(self) -> None:
        if shutil.which("ffmpeg") is None:
            messagebox.showerror("FFmpeg not found", "ffmpeg command was not found in PATH.")
            return

        input_path = self.input_path_var.get().strip()
        output_path = self.output_path_var.get().strip()
        if not input_path or not output_path:
            messagebox.showerror("Validation error", "Input file and output file are required.")
            return
        if not Path(input_path).is_file():
            messagebox.showerror("Validation error", "Input file does not exist.")
            return

        try:
            options = EditOptions(
                start_time=self.start_time_var.get().strip(),
                end_time=self.end_time_var.get().strip(),
                width=int(self.width_var.get()) if self.width_var.get().strip() else None,
                height=int(self.height_var.get()) if self.height_var.get().strip() else None,
                fps=int(self.fps_var.get()) if self.fps_var.get().strip() else None,
                crf=int(self.crf_var.get()),
                preset=self.preset_var.get(),
                rotate=int(self.rotate_var.get()),
                include_audio=self.include_audio_var.get(),
                audio_bitrate=self.audio_bitrate_var.get().strip() or "192k",
                video_codec=self.video_codec_var.get(),
            )
            command = build_ffmpeg_command(input_path, output_path, options)
        except ValueError as exc:
            messagebox.showerror("Validation error", str(exc))
            return

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
