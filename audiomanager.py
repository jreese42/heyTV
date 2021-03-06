import pyaudio
import time
import wave
from collections import deque
import audioop
import math
import logger
import os

class AudioManager:
    """
    A class for managing audio with Amazon's Alexa API
    Based heavily on jeysonmc's google speech script:
    https://github.com/jeysonmc/python-google-speech-scripts/blob/master/stt_google.py

    Initialize the class with audio settings, then listen to invoke the microphone clip manager
    """
    SAMPLE_HISTORY_SIZE = 300

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
        self.sample_history = deque(maxlen = self.SAMPLE_HISTORY_SIZE)
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

        #n = 0
        while (iterations == -1 or num > 0):
            curr_chunk = stream.read(self.audio_chunk_size)
            sample = math.sqrt(abs(audioop.avg(curr_chunk, 4)))
            audio_window.append(sample)
            self.update_threshold(sample)
            #self.logger.logDebug("Audio: " + str(audio_window[-1]) +"    " +str(n))
            #n = n+1

            if (sum( [x > self.threshold for x in audio_window]) > 0):
                if (not recording):
                    self.logger.logDebug("Starting recording window")
                    recording = True
                audio_data_out.append(curr_chunk)

            elif (recording):
                self.logger.logDebug("Finished recording window")
                filename = self.save_speech_window(list(prev_audio) + audio_data_out, pyaudio_handle)
                self.logger.logDebug("saved speech file: " + filename)

                #Perform STT operation here

                # Reset before going into the next recording window
                os.remove(filename)
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
        
    def update_threshold(self, new_sample):
        """
        Update the threshold value required to trigger a recording
        based on a weighted listed of recent audio samples
        """
        # Insert the new sample into the queue
        # This will push out values older than SAMPLE_HISTORY_SIZE
        self.sample_history.append(new_sample)

        # Calculate a threshold
        # Weight recent samples higher than older samples

        # first, calculate a weighted average, weight samples exponentially favoring newer samples
        count = len(self.sample_history)
        weighted_sum = sum([(x**2)*self.sample_history[x]/self.SAMPLE_HISTORY_SIZE for x in range(count)])
        weighted_denom = sum([x**2/self.SAMPLE_HISTORY_SIZE for x in range(count)])
        weighted_avg = weighted_sum / (weighted_denom + 1)

        # second, calculate the standard deviation using the weighted average
        dist_sum = sum([(self.sample_history[x] - weighted_avg)**2 for x in range(count)])
        std_dev = math.sqrt((1.0/count) * dist_sum)

        # finally, set the threshold to be the average plus a portion of the standard deviation
        self.threshold = weighted_avg + (0.4 * std_dev)
        self.logger.logDebug("New Threshold: " + str(self.threshold))
            



