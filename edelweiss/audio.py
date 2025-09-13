import threading
import pyaudio
import wave

import pyaudio
import wave
import threading


class SoundManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls, *args, **kwargs)
            cls.pyaudio_instance = pyaudio.PyAudio()
            cls.run = True

        return cls._instance

    def load_sound(self, filename):
        try:
            wf = wave.open(filename, "rb")
            print(f"File {filename} loaded successfully.")
        except Exception as e:
            raise Exception(f"Failed to load sound from file: {filename}, error: {e}")
        return wf

    def play_sound(self, wf, loop=False, position=0):
        def play():
            p = pyaudio.PyAudio()

            self.stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            data = wf.readframes(1024)

            while data != "" and self.run:
                self.stream.write(data)
                data = wf.readframes(1024)

            self.stream.stop_stream()
            self.stream.close()

            p.terminate()

        thread = threading.Thread(target=play)
        thread.start()
        return thread

    def stop(self):
        self.run = False

    def close(self):
        self.pyaudio_instance.terminate()


if __name__ == "__main__":
    sound_manager = SoundManager()

    try:
        sound_buffer = sound_manager.load_sound("music.wav")
        sound_thread = sound_manager.play_sound(sound_buffer)

        sound_thread.join()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        sound_manager.close()
