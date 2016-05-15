from pysoundcard import Stream, continue_flag
from autopy import mouse, screen
import numpy as np
import time

RATE = 44100
CHUNK = 2048

screen_size = screen.get_size()

MOUSE_SPEED = 15  # px
MOUSE_TARGET = [0, 0]

DB_MUL = 5
SCREEN_LEFT_DB = -16
SCREEN_RIGHT_DB = 2

SCREEN_TOP_HZ = 100
SCREEN_BOT_HZ = 1500

def determine_pitch(chunk):
    w = np.fft.fft(chunk)
    freqs = np.fft.fftfreq(len(w))
    idx = np.argmax(np.abs(w))
    freq = freqs[idx]
    return abs(freq * RATE)

def new_mouse_position(current, target, speed):
    if current == target:
        return current
    d = target - current
    if abs(d) > speed:
        return current + (np.sign(d) * speed)
    else:
        return current + d

def process_chunk(chunk, out_chunk, time_info, status):
    left_signal = chunk[:, 0]
    left_signal[left_signal == 0] = 0.00000001

    max_db = np.max(np.abs(left_signal))
    max_db = DB_MUL * np.log10(max_db)
    x_pct = np.interp(max_db, [SCREEN_LEFT_DB, SCREEN_RIGHT_DB], [0, 0.999999])

    hz = determine_pitch(left_signal)
    y_pct = np.interp(hz, [SCREEN_TOP_HZ, SCREEN_BOT_HZ], [0, 0.999999])

    MOUSE_TARGET[0] = int(screen_size[0] * x_pct)
    MOUSE_TARGET[1] = int(screen_size[1] * y_pct)

    c_x, c_y = mouse.get_pos()
    t_x, t_y = MOUSE_TARGET

    new_pos = np.array([
        new_mouse_position(c_x, t_x, MOUSE_SPEED),
        new_mouse_position(c_y, t_y, MOUSE_SPEED)
    ])
    mouse.move(
        max(0, min(new_pos[0], screen_size[0] - 1)),
        max(0, min(new_pos[1], screen_size[1] - 1))
    )

    out_chunk[:] = np.zeros_like(chunk)
    return continue_flag

def stream_audio():
    s = Stream(samplerate=RATE, blocksize=CHUNK, callback=process_chunk)
    s.start()
    try:
        print("Controlling cursor for 100 seconds, Ctrl-C to stop")
        time.sleep(100)
    except KeyboardInterrupt:
        pass
    print("Stopping...")
    s.stop()

if __name__ == "__main__":
    stream_audio()
