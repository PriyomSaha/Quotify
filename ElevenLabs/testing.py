from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key="sk_3da8f78e2b57ddf466f154a07c329992feb1ae591aea99c8")

voices = client.voices.search()

for voice in voices.voices:
    print(voice.name)
    print(voice.voice_id)
    print("-" * 40)