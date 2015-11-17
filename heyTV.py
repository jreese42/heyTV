import audiomanager
import pyaudio
import sys

audiomanager = audiomanager.AudioManager(format     = pyaudio.paInt16,
                                         channels   = 1,
                                         rate       = 16000,
                                         chunk_size = 1024,
                                         silence_limit = 1,
                                         prev_audio_time = 0.5,
                                         threshold = 2500,
                                         log_fd = sys.stdout)

audiomanager.listen(1)
