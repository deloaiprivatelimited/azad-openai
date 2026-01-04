from openai import OpenAI

client = OpenAI()

video = client.videos.create(
    model="sora-2",
    seconds=15,  # 15 seconds
    prompt="""
Create a 15-second cinematic promotional video.

Scene description:
An Indian girl in her early 20s, well-groomed and confident, standing in a calm indoor setting with soft lighting. She is holding a book clearly facing the camera. The book cover text reads “ಭಾರತೀಯ ಇತಿಹಾಸ ಮತ್ತು ಪರಂಪರೆ”.

The girl speaks in clear Kannada with a professional, friendly tone. Her expressions are confident and motivating.

Dialogue (Kannada):
“ಭಾರತೀಯ ಇತಿಹಾಸ ಮತ್ತು ಪರಂಪರೆ — ಲೇಖಕರು ಶ್ರೀನಿವಾಸ್.
IAS, KAS ಹಾಗೂ ಇತರೆ ಸ್ಪರ್ಧಾತ್ಮಕ ಪರೀಕ್ಷೆಗಳಿಗೆ ಅತ್ಯಂತ ಉಪಯುಕ್ತವಾದ ಪುಸ್ತಕ.
ವಿಶೇಷವಾಗಿ KAS ಮತ್ತು ಸಹಾಯಕ ಪ್ರಾಧ್ಯಾಪಕ ಪರೀಕ್ಷೆ ಬರೆಯುವ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಪಠ್ಯಕ್ರಮಕ್ಕೆ ಅನುಗುಣವಾಗಿ ಸಿದ್ಧಪಡಿಸಲಾಗಿದೆ.
ಇಂದೇ ಪಡೆಯಿರಿ.
AZAD PUBLICATION.”

End frame (text overlay, Kannada):
📞 9739728990 / 8861216868  
💰 ಬೆಲೆ: ₹430 + ₹50 ಅಂಚೆ ವೆಚ್ಚ  
“ಸ್ಪರ್ಧಾತ್ಮಕ ಯಶಸ್ಸಿನತ್ತ ನಿಮ್ಮ ಮೊದಲ ಹೆಜ್ಜೆ.”

Style:
Professional, clean, realistic video.
Natural Indian facial features.
Smooth camera movement.
Subtle background music.
High clarity, social-media-ready.

""",
    input_image=open("book_cover.png", "rb"),  # ✅ correct way to pass image
    size="1280x720"  # optional but recommended)
)
print("Video generation started:", video.id)

