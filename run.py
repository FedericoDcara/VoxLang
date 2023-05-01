
import winsound
import sys
import time
import pyaudio
import keyboard
import wave
from utils.translate import *
from utils.TTS import *
from utils.subtitle import *
from faster_whisper import WhisperModel

# to help the CLI write unicode characters to the terminal
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

mode = 0
total_characters = 0
is_Speaking = False

# function to get the user's input audio
def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    print("Recording...")
    while keyboard.is_pressed('RIGHT_SHIFT'):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Stopped recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    transcribe_audio_faster_whisper("input.wav")

def play_wav_through_microphone(filename):
    # Set parameters for audio stream
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 2
    fs = 44100

    # Open the .wav file
    wf = wave.open(filename, 'rb')

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open audio stream
    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    # Read data from .wav file and send to audio stream
    data = wf.readframes(chunk)

    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(chunk)

    # Close audio stream and PyAudio instance
    stream.stop_stream()
    stream.close()
    p.terminate()

#transcribe audio from faster whisper WIP
def transcribe_audio_faster_whisper(file):
    global chat_now

    model_size = "medium"
    # Run on GPU with FP16
    model = WhisperModel(model_size, device="cuda", compute_type="float16")
    # or run on GPU with INT8
    # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
    # or run on CPU with INT8
    # model = WhisperModel(model_size, device="cpu", compute_type="int8")   
    segments, info = model.transcribe(file, beam_size=5 , vad_filter=True)   
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))   
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
        translate_text(segment.text)

def translate_text(text):
    global is_Speaking
    # subtitle will act as subtitle for the viewer
    #subtitle = translate_google(text, "ID")

    # tts will be the string to be converted to audio
    detect = detect_google(text)
    tts = translate_google(text, f"{detect}", "JA")
    # tts = translate_deeplx(text, f"{detect}", "JA")
    tts_en = translate_google(text, f"{detect}", "EN")
    try:
        # print("ID Answer: " + subtitle)
        print("JP Answer: " + tts)
        print("EN Answer: " + tts_en)

    except:
        print("Error translating text")
        return

    # Choose between the available TTS engines
    # Japanese TTS
    voicevox_tts(tts)

    # Generate Subtitle
    generate_subtitle(text,tts_en,tts)
    time.sleep(1)

    # is_Speaking is used to prevent the assistant speaking more than one audio at a time
    is_Speaking = True
    winsound.PlaySound("test.wav", winsound.SND_FILENAME)
    is_Speaking = False

    # Clear the text files after the assistant has finished speaking
    time.sleep(1)
    truncate_files()
    
def truncate_files():
    files = ["output.txt", "eng.txt", "jap.txt"]
    for file in files:
        with open(file, "w") as f:
            f.truncate(0)

if __name__ == "__main__":
    try:
        print("Press and Hold Right Shift to record audio")
        while True:
            if keyboard.is_pressed('RIGHT_SHIFT'):
                record_audio()
    except KeyboardInterrupt:
        print("Stopped")

