from pathlib import Path
from openai import OpenAI

client = OpenAI()
speech_file_path = Path(__file__).parent / "1.mp3"
input_text = """Aptitude and DSA.
Most people think it's just coding.
But actually — it's the first door you must pass.

Companies don’t test DSA to find coding robots.
They test whether you can think — when the clock is real.

In just 45 minutes, they read you.
Can you break a hard problem into simple shapes?
Can you pick the right tool instead of guessing?
Can you defend your logic like an engineer?
And can you stay calm… and finish?

This one filter silently decides who continues —
and who gets stopped right here.

Even if you say nothing, your behavior speaks.

If you brute-force first, it signals panic.
If you jump straight into code, it shows a weak mental model.

But if you ask clarifying questions, you show structure.
If you narrate your logic, you show teamwork.
And if you solve from first principles, you show real intelligence — not memorization.

Because in these interviews, you're not judged on the final answer.
You're judged on the thinking path.

So, how do you actually prepare the right way?

First: build a clear thinking base.
Math sense. Pattern recognition.
Understanding how to break problems before solving them.
This is what prevents your brain from freezing.

Second: learn a small set of transferable patterns.
Arrays, trees, graphs, dynamic programming, greedy.
Not seven hundred random problems —
but a focused set you deeply understand.

Third: practice communication.
Say out loud:
What I see… what matters… what I’ll try… and why this approach is safe.
This is what makes you look hireable — not just correct.

Wrong prep looks like grind.
Solving daily without learning why.
Copying editorials.
Skipping timing.
Never practicing the explanation.

Right prep looks intentional.
Write constraints before coding.
Name the invariant.
Plan in three lines.
Explain trade-offs — not “it works.”
Use timed sessions.
And keep a post-mortem log so every mistake teaches you.

Two hard truths:
DSA is not an overnight skill — it compounds slowly.
And you don’t need Olympiad-level mastery — you’re preparing for a job, not a trophy.

And remember:
DSA alone doesn’t make you hireable.
What makes an engineer is thinking plus execution.
Projects, debugging, real-world constraints, and clean code when everything is messy.

Solve like an engineer.
Communicate like one.
And the door will open.

If you want more clarity — not noise — subscribe."""

with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="verse",
    input=input_text,
    instructions="Speak in a cheerful and positive tone.",
) as response:
    response.stream_to_file(speech_file_path)