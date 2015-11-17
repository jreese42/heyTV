import pyaudio
import time
import wave
from collections import deque
import audioop
import math
import logger

class AudioManager:
    """
    A class for managing audio with Amazon's Alexa API
    Based heavily on jeysonmc's google speech script:
    https://github.com/jeysonmc/python-google-speech-scripts/blob/master/stt_google.py

    Initialize the class with audio settings, then listen to invoke the microphone clip manager
    """
    def __init__(self, format, channels, rate, chunk_size, silence_limit, prev_audio_time, threshold, log_fd):
        
        """
        Create an audio manager object
        Takes a pyaudio format, number of channels, rate, and chunk size
        """
        self.audio_format = format
        self.audio_channels = channels
        self.audio_rate = rate
        self.audio_chunk_size = chunk_size
        self.silence_limit = silence_limit
        self.prev_audio_time = prev_audio_time
        self.threshold = threshold
        self.logger = logger.Logger(log_fd)
        self.logger.logDebug("Created Audio Manager")

         
    def listen(self, iterations):
        """Listen for a keyword"""

        #Get a handle on pyaudio
        pyaudio_handle = pyaudio.PyAudio()
        stream = pyaudio_handle.open(format=self.audio_format,
                              channels=self.audio_channels, 
                              rate=self.audio_rate, 
                              input=True, 
                              frames_per_buffer=self.audio_chunk_size)
        audio_data_out = []
        curr_chunk = ''
        window_size = self.audio_rate / self.audio_chunk_size

        audio_window = deque(maxlen = self.silence_limit * window_size)
        prev_audio = deque(maxlen = self.prev_audio_time * window_size)
        num = iterations
        response = []

        recording = False

        while (num == -1 or num > 0):
            curr_chunk = stream.read(self.audio_chunk_size)
            audio_window.append(math.sqrt(abs(audioop.avg(curr_chunk, 4))))

            if (sum( [x > self.threshold for x in audio_window]) > 0):
                if (not recording):
                    self.logger.logDebug("Starting recording window")
                    recording = True
                audio_data_out.append(curr_chunk)

            elif (recording):
                self.logger.logDebug("Finished recording window")
                filename = self.save_speech_window(list(prev_audio) + audio_data_out, pyaudio_handle)
                self.logger.logDebug("saved speech file: " + filename)

                # Reset before going into the next recording window
                recording = False
                audio_window = deque(maxlen = self.silence_limit * window_size)
                prev_audio = deque(maxlen = self.prev_audio_time * window_size)
                audio_data_out = []

                num = num - 1
            else:
                prev_audio.append(curr_chunk)




    def save_speech_window(self, data, pyaudio_handle):
        """
        Save audio data to a temporary file
        Returns the filename of the created file
        """
        filename = "tmp_" + str(int(time.time()))
        # Write to a WAV file
        data = ''.join(data)

        wavfd = wave.open(filename + '.wav', 'wb')

        #Set WAV encoding info and write data
        wavfd.setnchannels(self.audio_channels)
        wavfd.setsampwidth(pyaudio_handle.get_sample_size(self.audio_format))
        wavfd.setframerate(self.audio_rate)
        wavfd.writeframes(data)
        wavfd.close()

        return filename + '.wav'
        

