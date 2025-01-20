from pydantic import BaseModel
import numpy as np

class LocationData(BaseModel):
    stage: int
    x: float
    z: float
    direction: float

class AudioData(BaseModel):
    left_vol: float  # 左チャンネルのボリューム（0.0 - 1.0 など）
    right_vol: float  # 右チャンネルのボリューム（0.0 - 1.0 など）
    decay: float  # 各エコーの減衰率（0 < decay < 1）
    delay_ms: float # エコー間の遅延時間（ミリ秒）
    repeats: int # エコーの繰り返し回数
    left_delay: float 
    right_delay: float
    position: float

stage1 = np.zeros((21, 21))
for i in range(21):
    stage1[0][i] = 1
    stage1[20][i] = 1
    stage1[i][0] = 1
    stage1[i][20] = 1
for i in range(6, 21):
    stage1[i][6] = 1
for i in range(6, 14):
    stage1[6][i] = 1
for i in range(12, 21):
    stage1[13][i] = 1
for i in range(16, 20):
    stage1[20][i] = 0
print(stage1)

def find_wall_distances(x, z):
    # 前後左右に壁までの距離を初期化
    front_wall = None
    back_wall = None
    left_wall = None
    right_wall = None
    for i in range(z - 1, -1, -1):
        if stage1[x, i] == 1:
            left_wall = z - i
            break
    for i in range(z + 1, stage1.shape[1]):
        if stage1[x, i] == 1:
            right_wall = i - z
            break
    for i in range(x - 1, -1, -1):
        if stage1[i, z] == 1:
            front_wall = x - i
            break
    for i in range(x + 1, stage1.shape[0]):
        if stage1[i, z] == 1:
            back_wall = i - x
            break
    return front_wall, back_wall, left_wall, right_wall

def reflection_volume(distance:int) -> int:
    if distance == 0:
        return 10
    elif 1 <= distance <= 3:
        return 8
    elif 4 <= distance <= 6:
        return 4
    elif 7 <= distance <= 9:
        return 2
    else:
        return 0

def reflection(distance:int, direction:float) -> AudioData:
    sin = np.sin(np.radians(direction))
    cos = np.cos(np.radians(direction))
    vol = reflection_volume(distance)
    return AudioData(
        left_vol = -cos * vol,
        right_vol = cos * vol,
        decay = 0,
        delay_ms = 0,
        repeats = 0,
        left_delay = int(cos * 10) +  distance * 5,
        right_delay = distance * 5,
        # left_delay = cos * 10,
        # right_delay = 0,
        position = 10 * sin
    )

def location_to_audiodata(data: LocationData) -> AudioData:
    print("\n", data)
    x_int = int(data.x) + 10
    z_int = 21 - (int(data.z) + 10)
    print("x_int:", x_int, "z_int:", z_int)
    direction = data.direction
    print("direction:", direction)

    if data.stage == 1:
        # current_location = stage1[z_int][x_int]
        front_wall, back_wall, left_wall, right_wall = find_wall_distances(z_int, x_int)
        print("front_wall:", front_wall, "back_wall:", back_wall, "left_wall:", left_wall, "right_wall:", right_wall)
        audio_right = reflection(right_wall, direction)
        audio_front = reflection(left_wall, direction + 90)
        audio_left = reflection(left_wall, direction + 180)
        audio_back = reflection(back_wall, direction + 270)
        close_wall = min(left_wall, right_wall, front_wall, back_wall)
        if close_wall == left_wall:
            audio = audio_left
        elif close_wall == right_wall:
            audio = audio_right
        elif close_wall == front_wall:
            audio = audio_front
        else:
            audio = audio_back
    return audio