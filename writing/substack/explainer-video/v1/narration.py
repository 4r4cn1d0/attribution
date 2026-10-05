"""Build the explainer's narration with Kokoro-82M: one WAV per scene, sentence start times and subtitles.

Every sentence must appear word for word in script-and-storyboard.md, so the audio cannot drift
from the reviewed script. Run with the explainer environment:

    HF_HOME=tmp/explainer-hf tmp/explainer-venv/bin/python writing/substack/explainer-video/narration.py OUT_DIR
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "script-and-storyboard.md"
VOICE, RATE, GAP_SECONDS, LEAD_SECONDS = "af_heart", 24000, 0.35, 0.4

SCENES: list[tuple[str, list[str]]] = [
    ("S01Title", [
        "This is a question from an ongoing research project.",
        "Which training data should we change to make an AI safer?"]),
    ("S02Decision", [
        "Suppose a model fails a specific safety test again and again.",
        "We have some ideas to change the examples in its post-training.",
        "Post-training is the stage that teaches an already trained model how to respond.",
        "We can remove a group of examples.",
        "We can replace a group with different examples.",
        "Each data change sounds reasonable.",
        "But which data change actually helps?",
        "We can retrain the model for every option and compare the results.",
        "That gives us something concrete to measure.",
        "But with many options, it becomes expensive."]),
    ("S03Question", [
        "So here is the question.",
        "We have a specific safety failure and a set of possible data changes.",
        "Which data change will improve the model's behaviour most on new tests?",
        "Can we find it without fully retraining every option?",
        "And can we be honest about how uncertain that choice is?"]),
    ("S04SpecificNew", [
        "Two words matter here: specific and new.",
        "We need a failure that we can define and measure.",
        "We also need test examples that we hold back while we choose.",
        "If we do not hold them back, we can become very good at fixing only the test that we look at."]),
    ("S05SideEffects", [
        "Take a model that too often complies with a clearly harmful request.",
        "A data change can reduce those responses.",
        "But we also need to know about side effects.",
        "Does the model now refuse harmless questions?",
        "Is it now worse at tasks that it did well before?",
        "A lower failure rate on one measure is only part of the result."]),
    ("S06LookBackWhatIf", [
        "There is another distinction.",
        "Some training examples are linked to a bad answer.",
        "That does not tell us which examples to remove to improve future answers.",
        "One question looks back at how the model got here.",
        "The other question asks what happens if we change something.",
        "This research is about the second question."]),
    ("S07Cost", [
        "We still need to retrain some candidates to check our predictions.",
        "The aim is a more efficient search.",
        "So all the work counts toward the cost: scoring candidates, estimating uncertainty and validating the final choice.",
        "If the shortcut uses as much computation as trying every option directly, it does not help very much."]),
    ("S08Status", [
        "This is a research question.",
        "It is not a method that we have shown to work.",
        "We do not yet have evidence that we can make this decision more cheaply or more reliably than strong existing methods."]),
    ("S09Pilot", [
        "The work so far is narrower.",
        "We built a tiny learner.",
        "One copy learns normally.",
        "In the other copy, we suppress the learning contribution from one event.",
        "Then both copies continue to learn.",
        "An early change can alter later choices.",
        "Later choices can alter the information that the learner gets.",
        "This feedback is part of the problem."]),
    ("S10Coupling", [
        "These futures include randomness.",
        "So a comparison between the two copies can be noisy.",
        "Our pilot asked a question: can we coordinate the random choices of the two copies, so that the estimate becomes more precise?",
        "This idea is called coupling, and it is an established idea.",
        "Each copy still follows its own training probabilities at every step, given what has happened in both runs so far.",
        "We change only how the choices are paired."]),
    ("S11Gate", [
        "We checked 1,440 toy configurations with one-step or two-step continuations.",
        "We compared six baseline pairing methods with an oracle.",
        "The oracle could find the best allowed pairing in this tiny setup.",
        "To go on to a longer test, we set a gate: at least 20 percent less variance than the best baseline, in at least one configuration from our target family.",
        "Variance measures how much the comparison changes between random runs."]),
    ("S12Result", [
        "The strongest result in that family was about 18.5 percent.",
        "With full suppression of the event's learning contribution, the strongest result was about 14.1 percent.",
        "These were best cases, not averages.",
        "They came from an oracle, and the oracle's own computation was not a practical shortcut.",
        "So the pilot did not meet the gate for the longer test."]),
    ("S13NotShown", [
        "This result tells us something about the approach that we tested.",
        "It does not answer the larger question.",
        "The pilot did not choose batches of training data to remove or replace.",
        "It did not test safety improvements in a large language model.",
        "It did not show a saving in total computation."]),
    ("S14Next", [
        "Now come three questions.",
        "Which safety failure should we study?",
        "Which candidate changes should we compare?",
        "What evidence makes a recommendation trustworthy?",
        "A good method must also tell us when the evidence is too weak to choose between two options.",
        "That is better than a confident ranking with no reliable basis."]),
    ("S15Close", [
        "AI assistants help with the implementation and the critique.",
        "Their suggestions must still survive checks against the papers and the results.",
        "The project is still underway."]),
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("’", "'")).strip()


def check_against_script() -> None:
    script = _norm(SCRIPT.read_text(encoding="utf-8"))
    missing = [s for _, sentences in SCENES for s in sentences if _norm(s) not in script]
    if missing:
        raise SystemExit("not in the reviewed script, word for word:\n" + "\n".join(missing))


def _srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main(out_dir: str) -> None:
    check_against_script()
    from kokoro import KPipeline  # imported late: the script check needs no model

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    timings, srt, offset, index = {}, [], 0.0, 1
    for key, sentences in SCENES:
        pieces, starts, cursor = [np.zeros(int(LEAD_SECONDS * RATE), dtype=np.float32)], [], LEAD_SECONDS
        for sentence in sentences:
            audio = np.concatenate([np.asarray(a, dtype=np.float32) for _, _, a in pipe(sentence, voice=VOICE, speed=1.0)])
            starts.append(cursor)
            srt.append(f"{index}\n{_srt_time(offset + cursor)} --> {_srt_time(offset + cursor + len(audio) / RATE)}\n{sentence}\n")
            index += 1
            pieces += [audio, np.zeros(int(GAP_SECONDS * RATE), dtype=np.float32)]
            cursor += len(audio) / RATE + GAP_SECONDS
        wav = out / f"{key}.wav"
        sf.write(wav, np.concatenate(pieces), RATE)
        timings[key] = {"wav": str(wav), "starts": starts, "duration": cursor}
        offset += cursor + 0.6       # the scene's closing hold (explainer.py TAIL_SECONDS)
    (out / "timings.json").write_text(json.dumps(timings, indent=1))
    (out / "narration.srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"{len(SCENES)} scenes, {index - 1} sentences, {offset / 60:.2f} min including holds")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tmp/explainer-build/audio")
