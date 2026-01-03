import logging
import os

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request
from flask import make_response
import subprocess
from flask import Response

class EPStreamMediaGet(EP):

    ID = 'stream_media_get'
    URL = '/stream/media/get'

    PATH_PAR_PAYLOAD = '/media/get'
    PATH_PAR_URL = '/media/get/card_id/<card_id>/audio_track/<audio_track>'

    METHOD = 'GET'

    ATTR_CARD_ID = 'card_id'
    ATTR_AUDIO_TRACK = 'audio_track'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, card_id, audio_track) -> dict:

        payload = {}
        payload[EPStreamMediaGet.ATTR_CARD_ID] = card_id
        payload[EPStreamMediaGet.ATTR_AUDIO_TRACK] = audio_track

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        card_id = payload[EPStreamMediaGet.ATTR_CARD_ID]
        audio_track = payload[EPStreamMediaGet.ATTR_AUDIO_TRACK]

        media_path = self.web_gadget.db._get_full_media_file_name_by_card_id(card_id)

        #import logging
        #logging.error(f"!!!!! Media - absolute_media_path: {media_path}, card_id: {card_id} !!!")

        if not os.path.exists(media_path):
            return make_response("Media file not found", 404)

        # Stream with FFmpeg
        return self._stream_with_ffmpeg(media_path, audio_track)


    def _stream_with_ffmpeg(self, media_path, audio_track):
        """Stream media with specific audio track using FFmpeg"""

        # FFmpeg command to select specific audio track
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', media_path,
            '-map', '0:v:0',
            '-map', f'0:a:{audio_track}',
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-f', 'mp4',
            '-movflags', 'frag_keyframe+empty_moov+default_base_moof',
            '-frag_duration', '20000000',    # 10 second fragments (less aggressive)
            '-bufsize', '2M',                # Larger buffer
            '-maxrate', '20M',               # Higher max rate
            'pipe:1'
        ]

#        # FFmpeg command to select specific audio track
#        ffmpeg_cmd = [
#            'ffmpeg',
#            '-i', media_path,
#            '-map', f'0:a:{audio_track}',  # Only map audio for MP3
#            '-c:a', 'copy',   # Copy audio without re-encoding
#            '-f', 'mp3',      # Output format MP3
#            'pipe:1'          # Output to stdout
#        ]


        def generate():
            process = None
            try:
                #print("Starting FFmpeg process")
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                #print(f"FFmpeg PID: {process.pid}")

                while True:
                    # Reads a chunk of video data from FFmpeg's stdout pipe
                    # 8192 (8KB) is the buffer size - how much data to read at once
                    data = process.stdout.read(8192)
                    if not data:
                        #print("No more data from FFmpeg")
                        break
                    yield data

            except Exception as e:
                #print(f"Exception in generate: {e}")
                pass
            finally:
                #print("Finally block executing")
                if process:
                    #print(f"Process status: {process.poll()}")
                    try:
                        if process.poll() is None:
                            #print("Terminating process")
                            process.terminate()
                            try:
                                process.wait(timeout=2)  # Shorter timeout
                            except subprocess.TimeoutExpired:
                                #print("Terminate timeout, force killing")
                                process.kill()
                                process.wait()  # Wait without timeout after kill

                        # Ensure process is reaped
                        import os
                        try:
                            os.waitpid(process.pid, 0)
                            print("Process properly reaped")
                        except:
                            pass  # Already reaped

                        #print(f"Process cleaned up, return code: {process.returncode}")
                    except Exception as e:
                        #print(f"Cleanup error: {e}")
                        pass

        return Response(
#            generate(),
#            mimetype='video/x-matroska',
#            headers={
#                'Content-Type': 'video/x-matroska',
#                'Accept-Ranges': 'bytes'
#            }
            generate(),
            mimetype='video/mp4',
            headers={
                'Content-Type': 'video/mp4',
                'Accept-Ranges': 'bytes'
            }
        )
