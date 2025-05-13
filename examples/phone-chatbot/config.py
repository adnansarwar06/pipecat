from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Twilio credentials for 
    twilio_account_sid: str
    twilio_auth_token: str

    # Edge TTS settings
    edge_tts_voice: str = "en-US-AriaNeural"

    # Silence detection parameters
    silence_timeout: int = 10        # seconds to wait for speech before prompting
    max_silent_prompts: int = 3      # number of re-prompts before hangup
    initial_silent_timeout: int = 2

    record_timeout: int = 5         
    record_max_length: int = 10     

    min_transcription_length: int = 25  # minimum characters to consider as valid speech

    # Directories for audio storage and logs
    audio_dir: str = "audio"
    log_file: str = "logs/call_summary.log"

    class Config:
        env_file = ".env"

    
