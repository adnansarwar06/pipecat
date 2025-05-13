import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import edge_tts
from twilio.twiml.voice_response import VoiceResponse
import asyncio

from config import Settings

# Load configuration settings
settings = Settings()

# Ensure required directories
os.makedirs(settings.audio_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)

logging.basicConfig(
    filename=settings.log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# In-memory store for call sessions
sessions = {}
static_audio = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Generate static audio prompts on startup.
    """
    prompts = {
        "start": "Call started.",
        "retry": "I didn't hear anything. Could you please speak?",
        "terminate": "Ending the call. Goodbye.",
        "heard_something": "You said something. Ending the call now.",
    }

    for key, text in prompts.items():
        filename = f"{key}.mp3"
        filepath = os.path.join(settings.audio_dir, filename)
        if not os.path.exists(filepath):
            communicate = edge_tts.Communicate(text, voice=settings.edge_tts_voice)
            await communicate.save(filepath)
        static_audio[key] = filename

    yield


# Initialize FastAPI and mount static files
app = FastAPI(lifespan=lifespan)
app.mount("/audio", StaticFiles(directory=settings.audio_dir), name="audio")


@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    call_sid = form["CallSid"]

    # Initialize session
    session = sessions.setdefault(call_sid, {"silence_count": 0, "transcripts": []})
    resp = VoiceResponse()

    if session["silence_count"] == 0:
        filename = static_audio["start"]
        audio_url = str(request.url_for("audio", path=filename))
        resp.play(audio_url)
    else:
        logging.info(f"Call {call_sid}: retry #{session['silence_count']}")

    # Start recording and use transcription callback
    resp.record(
        action=str(request.url_for("handle_recording")),
        method="POST",
        timeout=settings.record_timeout,
        maxLength=settings.record_max_length,
        playBeep=True,
        transcribe=True,
        transcribeCallback=str(request.url_for("handle_transcription")),
    )

    return Response(content=str(resp), media_type="application/xml")


@app.post("/handle_transcription")
async def handle_transcription(request: Request):
    """
    Called asynchronously by Twilio with the transcription result.
    Stores the transcription text for use by /handle_recording.
    """
    try:
        form = await request.form()
        call_sid = form.get("CallSid")
        transcription = form.get("TranscriptionText")

        if call_sid not in sessions:
            sessions[call_sid] = {"silence_count": 0, "transcripts": []}

        if (
            transcription
            and transcription.strip()
            and len(transcription.strip()) >= settings.min_transcription_length
        ):
            sessions[call_sid]["transcripts"].append(transcription.strip())
            logging.info(f"Call {call_sid}: transcription received - {transcription}")
        else:
            logging.info(
                f"Call {call_sid}: transcription too short or empty: {transcription!r}"
            )

        return Response(content="", media_type="text/plain")

    except Exception as e:
        logging.error(f"Exception in /handle_transcription: {e}", exc_info=True)
        return Response(status_code=200)


@app.post("/handle_recording")
async def handle_recording(request: Request):
    """
    After recording ends, wait for Twilio transcription (via callback),
    then decide whether to retry or end the call.
    """
    try:
        form = await request.form()
        call_sid = form.get("CallSid")
        session = sessions.get(call_sid, {"silence_count": 0, "transcripts": []})
        resp = VoiceResponse()

        logging.info(f"Waiting for transcription for call {call_sid}...")
        recording_url = form.get("RecordingUrl")
        logging.info(f"Recording URL: {recording_url}.mp3")

        # Poll for transcription (wait up to 6 seconds)
        for i in range(12):
            if session["transcripts"]:
                break
            await asyncio.sleep(0.5)

        if session["transcripts"]:
            filename = static_audio["heard_something"]
            audio_url = str(request.url_for("audio", path=filename))
            resp.play(audio_url)
            resp.hangup()
            logging.info(f"Call {call_sid}: voice detected, call ended.")
        else:
            session["silence_count"] += 1
            logging.info(
                f"Call {call_sid}: no voice detected (silence count = {session['silence_count']})"
            )

            if session["silence_count"] < settings.max_silent_prompts:
                filename = static_audio["retry"]
                audio_url = str(request.url_for("audio", path=filename))
                resp.play(audio_url)
                resp.redirect("/voice")
            else:
                filename = static_audio["terminate"]
                audio_url = str(request.url_for("audio", path=filename))
                resp.play(audio_url)
                resp.hangup()
                logging.info(
                    f"Call {call_sid} ended after {session['silence_count']} silences."
                )

        sessions[call_sid] = session
        return Response(content=str(resp), media_type="application/xml")

    except Exception as e:
        logging.error(f"Exception in /handle_recording: {e}", exc_info=True)
        return Response(
            "<Response><Say>Internal server error. Goodbye.</Say><Hangup/></Response>",
            media_type="application/xml",
        )
