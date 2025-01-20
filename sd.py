import numpy as np
import time
import threading
from fastapi import FastAPI, UploadFile, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
from pydub.playback import play
# from pydantic import BaseModel
import sounddevice as sd
import asyncio
import uvicorn
from tqdm import tqdm
from pydantic import BaseModel

class AudioData(BaseModel):
    left_vol: float  # 左チャンネルのボリューム（0.0 - 1.0 など）
    right_vol: float  # 右チャンネルのボリューム（0.0 - 1.0 など）
    decay: float  # 各エコーの減衰率（0 < decay < 1）
    delay_ms: int # エコー間の遅延時間（ミリ秒）
    repeats: int # エコーの繰り返し回数
    left_delay: int 
    right_delay: int
    position: float

# リクエストの例
# post http://localhost:8000/play
# {
#     "left_vol" : 0,
#     "right_vol" : 0,
#     "decay" : 100,
#     "delay_ms" : 20,
#     "repeats" : 100,
#     "left_delay" : 20,
#     "right_delay" : 0,
#     "position" : 5
# }

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
    left_channel, right_channel = audio_data.split_to_mono()

    left_channel_with_delay = AudioSegment.silent(duration=left_delay_ms) + left_channel  # 左チャンネルに遅延
    right_channel_with_delay = AudioSegment.silent(duration=right_delay_ms) + right_channel  # 右チャンネルに遅延

    max_length = max(len(left_channel_with_delay), len(right_channel_with_delay))
    left_channel_with_delay = left_channel_with_delay + AudioSegment.silent(duration=max_length - len(left_channel_with_delay))
    right_channel_with_delay = right_channel_with_delay + AudioSegment.silent(duration=max_length - len(right_channel_with_delay))
    print("ITDを適用しました。")
    return AudioSegment.from_mono_audiosegments(left_channel_with_delay, right_channel_with_delay)


def apply_reverb(audio_data: AudioSegment, decay: float = 4, delay_ms: int = 50, repeats: int = 30):
    try:
        output = audio_data  # オリジナル音声
        for i in tqdm(range(1, repeats + 1)):
            # エコーの生成: 遅延 + 減衰
            echo = AudioSegment.silent(duration=delay_ms * i) + audio_data - (10 + i * decay)
            output = output.overlay(echo)
        print("リバーブ効果を適用しました。")
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"リバーブ効果の適用中にエラーが発生しました: {e}")

# def apply_front_back_filter(audio_data: AudioSegment, position: int):
#     """
#     音源が前か後かに基づいてフィルタを適用。
#     position: "front" or "back"
#     """
#     if position == 1:
#         # 前の場合、高周波を少し強調
#         filtered_audio = audio_data.low_pass_filter(12000)  # 12kHz以上を強調
#     elif position == 0:
#         # 後の場合、高周波を弱める
#         filtered_audio = audio_data.low_pass_filter(3000)  # 3kHz以上を削減
#     else:
#         # その他の場合、何もしない
#         filtered_audio = audio_data
#     print("前後のフィルタを適用しました。")
#     return filtered_audio

def apply_front_back_filter(audio_data: AudioSegment, position: float):
    """
    音源の前後情報を基にフィルタを適用。
    position: -10 (完全に後ろ) ~ 10 (完全に前)
    """
    if not (-10 <= position <= 10):
        raise ValueError("position must be between -10 and 10")

    # positionに基づいてカットオフ周波数を計算
    min_cutoff = 3000   # 完全に後ろの場合のカットオフ周波数 (3kHz)
    max_cutoff = 12000  # 完全に前の場合のカットオフ周波数 (12kHz)
    # cutoff_freq = min_cutoff + (position / 10) * (max_cutoff - min_cutoff)
    cutoff_freq = (min_cutoff + max_cutoff) / 2 + (max_cutoff - min_cutoff) / 2 * position / 10

    # フィルタを適用
    filtered_audio = audio_data.low_pass_filter(cutoff_freq)
    print(f"前後のフィルタを適用しました: position={position}, カットオフ周波数={cutoff_freq:.2f} Hz")
    return filtered_audio

@app.post("/play")
async def play_audio(data: AudioData):
    start = time.time()
    # if file.content_type != "audio/wav":
    #     raise HTTPException(status_code=400, detail="WAV形式のファイルをアップロードしてください。")

    left_vol = data.left_vol
    right_vol = data.right_vol
    decay = data.decay
    delay_ms = data.delay_ms
    repeats = data.repeats
    left_delay = data.left_delay
    right_delay = data.right_delay
    position = data.position

    try:
        # audio_data = AudioSegment.from_file(file.file, format=file.content_type)
        # audio_data = AudioSegment.from_file('test.wav', format="wav")
        audio_data = AudioSegment.from_file('shitauchi.wav', format="wav")
        if audio_data.channels != 1:
            raise HTTPException(status_code=400, detail="モノラルのmp3ファイルをアップロードしてください。")
        
        # 左右音量を調整してステレオ変換
        stereo_audio = AudioSegment.from_mono_audiosegments(
            audio_data.apply_gain(left_vol),
            audio_data.apply_gain(right_vol)
        )
        print("左右音量を調整しました。")

        # リバーブ効果の適用（必要に応じて）
        # if reverb:
        #     stereo_audio = apply_reverb(stereo_audio)
        stereo_audio = apply_reverb(stereo_audio, decay, delay_ms, repeats)
        
        # left_delay =  40
        # right_delay = 0
        # ITD（両耳間到達時間差）を加える
        stereo_with_itd = apply_itd(stereo_audio, left_delay, right_delay)

        # 音源が前か後ろかに基づいてフィルタを適用
        stereo_with_hrtf = apply_front_back_filter(stereo_with_itd, position)

        print("音声の再生を開始します。")
        def play_in_thread(audio):
            play(audio)

        print(f"処理時間: {time.time() - start:.2f}秒")
        threading.Thread(target=play_in_thread, args=(stereo_with_hrtf,)).start()

        return {"message": "音声の再生を開始しました。"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エラーが発生しました: {e}")



# def apply_itd_numpy(data, left_delay_samples, right_delay_samples):
#     # ディレイを追加
#     left_channel = np.pad(data[:, 0], (left_delay_samples, 0), mode='constant')[:len(data)]
#     right_channel = np.pad(data[:, 0], (right_delay_samples, 0), mode='constant')[:len(data)]

#     # ステレオデータを再構築
#     return np.stack([left_channel, right_channel], axis=-1)


sample_rate = 44100
channels = 1

def callback(indata, outdata, frames, time, status):
    if status:
        print(status)
    print(type(indata))
    print(indata.shape)
    outdata[:] = indata

async def play_audio():
    # 非同期で実行するためにストリームを別スレッドで開始
    with sd.Stream(samplerate=sample_rate, channels=channels, callback=callback):
        print("Playing environment audio")
        await asyncio.sleep(10)


@app.post("/play/environment") 
async def play_environment():
    # 非同期タスクとしてplay_audioを実行
    await play_audio()
    return {"message": "Environment audio is playing"}

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)