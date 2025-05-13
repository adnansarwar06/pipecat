<!-- @format -->

<div align="center">
 <img alt="pipecat" width="300px" height="auto" src="image.png">
</div>

# Pipecat Voice Bot (Modified)

This is a modified version of the original Pipecat voice bot example.

The required libraries are listed in the `requirements.txt` file.

> **Note:** `daily-python` is currently unavailable on PyPI and also cannot be installed via its GitHub link. As a result, this version uses the `twilio` library instead. I couldn't find any recent information explaining the issue.

---

## Setup Instructions

This project avoids API keys and paid services where possible. Because of that, a bit of manual setup is required — especially around ngrok and webhook configuration.

### 1. Start ngrok

Make sure you have [ngrok](https://ngrok.com/) installed and registered. Then run:

```bash
ngrok http 8000
```

If successful, you’ll see a forwarding address like:

```
https://random-subdomain.ngrok-free.app
```

Save this URL — you’ll need it to update your Twilio webhook.

---

### 2. Update the Twilio Webhook

Run the following command to point your Twilio number to your local server:

```bash
python ./update_webhook.py -p [your_twilio_phone_number] -w [your_ngrok_link]
```

Make sure the following environment variables are set in your `.env` file:

```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
```

---

### 3. Start the Server

Start the FastAPI app using Uvicorn:

```bash
uvicorn main:app --host [your_ip] --port [your_port] --reload
```

---

## Limitations

- Twilio's transcription can be slow for long audio, which might cause the app to incorrectly treat valid speech as silence.
- Transcription quality can be low for short or unclear speech.
- Retry logic is in place for when valid input is not detected.

---

## Logging

Call activity and transcriptions are saved in `./logs/`.

### Sample Log Output:

```
2025-05-13 10:59:11,747 - INFO - Waiting for transcription for call CA96e9070e...
2025-05-13 10:59:11,747 - INFO - Recording URL: https://api.twilio.com/2010-04-01/...
2025-05-13 10:59:17,859 - INFO - Call CA96e9070e...: no voice detected (silence count = 1)
2025-05-13 10:59:24,878 - INFO - Call CA96e9070e...: transcription too short or empty: 'A.'
2025-05-13 10:59:27,324 - INFO - Call CA96e9070e...: retry #1
2025-05-13 10:59:38,625 - INFO - Waiting for transcription for call CA96e9070e...
2025-05-13 10:59:38,625 - INFO - Recording URL: https://api.twilio.com/2010-04-01/...
2025-05-13 10:59:44,677 - INFO - Call CA96e9070e...: no voice detected (silence count = 2)
2025-05-13 10:59:52,437 - INFO - Call CA96e9070e...: transcription too short or empty: 'Of the.'
2025-05-13 10:59:54,190 - INFO - Call CA96e9070e...: retry #2
2025-05-13 11:00:05,346 - INFO - Waiting for transcription for call CA96e9070e...
2025-05-13 11:00:05,347 - INFO - Recording URL: https://api.twilio.com/2010-04-01/...
2025-05-13 11:00:11,411 - INFO - Call CA96e9070e...: no voice detected (silence count = 3)
2025-05-13 11:00:11,412 - INFO - Call CA96e9070e... ended after 3 silences.
2025-05-13 11:00:17,155 - INFO - Call CA96e9070e...: transcription too short or empty: 'A.'
```

---

## Notes

- If you speak too softly or too briefly, Twilio might return inaccurate or empty transcriptions like `'A.'` or `'Of the.'`
- These are filtered using a minimum word count or character length to minimize false positives.
- You can modify filtering rules and behavior thresholds in `config.py`.
