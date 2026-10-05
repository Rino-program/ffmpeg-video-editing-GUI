# ffmpeg-video-editing-GUI

FFmpeg を使った、使いやすさと拡張性を重視した動画編集 GUI です。  
タブ構成で基本編集から `vf` / `af` 系の詳細調整までまとめて実行できます。

## 主な機能

### 基本編集
- 入力/出力ファイル選択
- トリミング（開始/終了時刻）
- 解像度変更（scale）
- FPS 変更
- 映像コーデック選択（H.264 / H.265 / VP9 / AV1）
- CRF / Preset / 映像ビットレート調整

### Video Filters (`-vf`)
- 回転（0 / 90 / 180 / 270）
- クロップ（width/height/x/y）
- 反転（`hflip`, `vflip`）
- インターレース解除（`yadif`）
- 色調整（`eq`: brightness / contrast / saturation / gamma）
- 再生速度（`setpts`）
- カスタム `vf` 文字列追記（任意の FFmpeg フィルタ式）

### Audio Filters (`-af`)
- 音声有効/無効切替
- オーディオコーデック / ビットレート / チャンネル数 / サンプルレート
- 音量調整（`volume`）
- 音声テンポ調整（`atempo`。範囲外は複数段に自動分割）
- ハイパス / ローパス（`highpass`, `lowpass`）
- ラウドネス正規化（`loudnorm`）
- ノイズ低減（`afftdn`）
- カスタム `af` 文字列追記（任意の FFmpeg フィルタ式）

### 操作補助
- FFmpeg 実行前のコマンドプレビュー
- 入力値バリデーション（不正値・不足値を実行前に検知）
- 非同期実行による GUI 応答性維持

## 必要要件

- Python 3.10+
- `ffmpeg` コマンドが PATH 上で実行できること

## 起動方法

```bash
python app.py
```

## 使い方のポイント

1. `Input file` と `Output file` を指定
2. `Basic` / `Video Filters (vf)` / `Audio Filters (af)` の各タブで必要項目を設定
3. `Preview FFmpeg Command` で最終コマンドを確認
4. `Run FFmpeg` で変換・編集を実行

## テスト

```bash
python -m unittest discover -s tests -p "test_*.py"
```