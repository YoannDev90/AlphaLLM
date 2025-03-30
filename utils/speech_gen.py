import requests
import urllib.parse

text = "Generating audio using the GET method is simple for short texts."
voice = "echo" # alloy, echo, fable, onyx, nova, shimmer
output_filename = "generated_audio_get.mp3"

encoded_text = urllib.parse.quote(text)
url = f"https://text.pollinations.ai/{encoded_text}"
params = {
    "model": "openai-audio",
    "voice": voice
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()

    if 'audio/mpeg' in response.headers.get('Content-Type', ''):
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        print(f"Audio saved successfully as {output_filename}")
    else:
        print("Error: Expected audio response, but received:")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"Error making TTS GET request: {e}")