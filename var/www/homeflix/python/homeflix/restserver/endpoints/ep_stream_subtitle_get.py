import logging
import os

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request
from flask import make_response
import subprocess
from flask import Response

class EPStreamSubtitleGet(EP):

    ID = 'stream_subtitle_get'
    URL = '/stream/subtitle/get'

    PATH_PAR_PAYLOAD = '/subtitle/get'
    PATH_PAR_URL = '/subtitle/get/card_id/<card_id>/subtitle_track/<subtitle_track>'

    METHOD = 'GET'

    ATTR_CARD_ID = 'card_id'
    ATTR_SUBTITLE_TRACK = 'subtitle_track'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, card_id, subtitle_track) -> dict:

        payload = {}
        payload[EPStreamSubtitleGet.ATTR_CARD_ID] = card_id
        payload[EPStreamSubtitleGet.ATTR_SUBTITLE_TRACK] = subtitle_track

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        card_id = payload[EPStreamSubtitleGet.ATTR_CARD_ID]
        subtitle_track = payload[EPStreamSubtitleGet.ATTR_SUBTITLE_TRACK]

        media_path = self.web_gadget.db._get_full_media_file_name_by_card_id(card_id)

        #import logging
        #logging.error(f"!!!!! Subtitle - absolute_media_path: {media_path}, card_id: {card_id} !!!")

        if not os.path.exists(media_path):
            return make_response("Media file not found", 404)

        # Stream with FFmpeg
        return self._stream_with_ffmpeg(media_path, subtitle_track)

    def _stream_with_ffmpeg(self, media_path, subtitle_track):
        """Stream subtitle track using FFmpeg"""

        # FFmpeg command to select specific audio track
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', media_path,
            '-map', f'0:s:{subtitle_track}',    # Map specific subtitle stream
            '-c:s', 'webvtt',
            '-f', 'webvtt',                     # Use MKV format (better subtitle support)
            'pipe:1'                            # Output to stdout
        ]


        def generate():
            process = None
            try:
                print("Starting FFmpeg subtitle process")
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"FFmpeg subtitle PID: {process.pid}")

                while True:
                    data = process.stdout.read(8192)
                    if not data:
                        print("No more subtitle data from FFmpeg")
                        break
                    yield data

            except Exception as e:
                print(f"Exception in subtitle generate: {e}")
            finally:
                print("Subtitle finally block executing")
                if process:
                    print(f"Subtitle process status: {process.poll()}")
                    try:
                        if process.poll() is None:
                            print("Terminating subtitle process")
                            process.terminate()
                            try:
                                process.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                print("Subtitle terminate timeout, force killing")
                                process.kill()
                                process.wait()

                        # Ensure process is reaped
                        import os
                        try:
                            os.waitpid(process.pid, 0)
                            print("Subtitle process properly reaped")
                        except:
                            pass

                        print(f"Subtitle process cleaned up, return code: {process.returncode}")
                    except Exception as e:
                        print(f"Subtitle cleanup error: {e}")


#        def generate():
#            process = None
#            try:
#                process = subprocess.Popen(
#                    ffmpeg_cmd,
#                    stdout=subprocess.PIPE,
#                    stderr=subprocess.PIPE
#                )
#
#                while True:
#                    data = process.stdout.read(8192)
#                    if not data:
#                        break
#                    yield data
#
#            except GeneratorExit:
#                # Client disconnected - kill FFmpeg process
#                if process and process.poll() is None:
#                    process.terminate()
#                    process.wait()
#                raise
#            except Exception as e:
#                print(f"FFmpeg error: {e}")
#                if process and process.poll() is None:
#                    process.terminate()
#            finally:
#                if process and process.poll() is None:
#                    process.terminate()

#            try:
#                process = subprocess.Popen(
#                    ffmpeg_cmd,
#                    stdout=subprocess.PIPE,
#                    stderr=subprocess.PIPE
#                )
#
#                while True:
#
#                    # Reads a chunk of video data from FFmpeg's stdout pipe
#                    # 8192 is the buffer size - how much data to read at once
#                    data = process.stdout.read(8192)
#                    if not data:
#                        break
#                    yield data
#
#                process.wait()
#            except Exception as e:
#                print(f"FFmpeg error: {e}")

        return Response(
            generate(),
            mimetype='text/vtt',
            headers={
                'Content-Type': 'text/vtt',
                'Accept-Ranges': 'bytes'
            }
        )
