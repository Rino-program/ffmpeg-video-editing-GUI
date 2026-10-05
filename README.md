# ffmpeg-video-editing-GUI

FFmpeg を使った、シンプルで使いやすい動画編集 GUI です。  
以下の編集を 1 画面でまとめて実行できます。

- 入力/出力ファイル選択
- トリミング（開始/終了時刻）
- 解像度変更（Width/Height）
- FPS 変更
- 回転（0 / 90 / 180 / 270）
- 映像コーデック選択（H.264 / H.265 / VP9）
- CRF / Preset 調整
- 音声あり/なし切替、音声ビットレート設定

## 必要要件

- Python 3.10+
- `ffmpeg` コマンドが PATH 上で実行できること

## 起動方法

```bash
python app.py
```

## テスト

```bash
python -m unittest discover -s tests -p "test_*.py"
```