import numpy as np
import time
import threading
from fastapi import FastAPI, UploadFile, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
from pydub.playback import play
from pydantic import BaseModel
# import sounddevice as sd
import asyncio
import uvicorn

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.post("/hello")
def hello(request: Request):
    return {"message": "Hello World"}


# ITD（両耳間到達時間差）を加える関数
def apply_itd(audio_data: AudioSegment, left_delay_ms: int, right_delay_ms: int):
    # ステレオ音声を左右のモノラルチャンネルに分割
    left_channel, right_channel = audio_data.split_to_mono()

    # 左右のチャンネルに無音（遅延）を追加
    left_channel_with_delay = AudioSegment.silent(duration=left_delay_ms) + left_channel  # 左チャンネルに遅延
    right_channel_with_delay = AudioSegment.silent(duration=right_delay_ms) + right_channel  # 右チャンネルに遅延

    # 音声長を揃える（必要な場合）
    max_length = max(len(left_channel_with_delay), len(right_channel_with_delay))
    left_channel_with_delay = left_channel_with_delay + AudioSegment.silent(duration=max_length - len(left_channel_with_delay))
    right_channel_with_delay = right_channel_with_delay + AudioSegment.silent(duration=max_length - len(right_channel_with_delay))
    # 遅延を加えた左右チャンネルを再びステレオに統合
    return AudioSegment.from_mono_audiosegments(left_channel_with_delay, right_channel_with_delay)


@app.post("/play")
# async def play_audio(file: UploadFile = Form(...), left_vol: int = Form(0), right_vol: int = Form(0)):
async def play_audio(left_vol: int = Form(0), right_vol: int = Form(0)):
    # if file.content_type != "audio/wav":
    #     raise HTTPException(status_code=400, detail="WAV形式のファイルをアップロードしてください。")

    try:
        # ファイルを読み込み、モノラル音声として解析
        # audio_data = AudioSegment.from_file(file.file, format=file.content_type)
        audio_data = AudioSegment.from_file('test.wav', format="wav")
        if audio_data.channels != 1:
            raise HTTPException(status_code=400, detail="モノラルのmp3ファイルをアップロードしてください。")
        
        left_vol_edit = left_vol
        right_vol_edit = 1
        # 左右音量を調整してステレオ変換
        stereo_audio = AudioSegment.from_mono_audiosegments(
            audio_data.apply_gain(left_vol_edit),
            audio_data.apply_gain(right_vol_edit)
        )

        left_delay =  20
        right_delay = 0
        # ITD（両耳間到達時間差）を加える
        stereo_with_itd = apply_itd(stereo_audio, left_delay, right_delay)
        print("音声の再生を開始します。")

        # 非同期的に音声を再生するためにスレッドを使用
        def play_in_thread(audio):
            play(audio)

        threading.Thread(target=play_in_thread, args=(stereo_with_itd,)).start()

        return {"message": "音声の再生を開始しました。"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エラーが発生しました: {e}")

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)