# media-plan.md

One entry per planned video, audio piece, animation, infographic or interactive, grouped by module or week. Producers can work from this file directly or from the generated `docs/media-plan.csv`. Full example: `sample/output/media-plan.md`.

```markdown
# Media plan: Food Safety for Small-Scale Produce Growers

- Course code: FSPG 101

## Notes

- Nothing is linked in a topic until it is streamed in Kaltura with accurate captions and a transcript.

## Module 01: Why produce safety matters

### M01-V01: Why one outbreak can close a small farm

- Topic: t01 (Why produce eaten raw is different)
- Type: talking-head
- Minutes: 4
- Purpose: Make the stakes personal before any technical content.
- Script source: week1 slides, slide 1 speaker notes
- Script status: needs script from faculty outline
- Shoot: studio
- On camera: Instructor
- Production notes: One camera, lower third with name and title.
- Captions: yes
- Transcript: yes
- Audio description: not needed if the photos are described in narration
- Priority: must have
- Existing asset:
- Stream URL:
- Transcript URL:
- Captions verified: no
```

- **ID**: `M01-V01` for video in Module 01, `M01-G01` for a graphic, `M01-A01` for audio. It is what topic files point at.
- **Topic**: the topic ID from the course map. The title in brackets is for people; the build reads only the ID.
- **Type**: talking-head, lightboard, screencast, demonstration, interview, animation, field-footage, narrated-slides, podcast-audio, existing-reuse, infographic, interactive.
- **Captions** and **Transcript** must be yes for anything with sound. **Audio description** must state a decision, even "not needed because ...". Infographics and interactives have a **Text alternative** line instead of those three.
- **Stream URL**, **Transcript URL** and **Captions verified** are filled in by the producer after the video is in Kaltura. A topic shows the video only when it has a Stream URL and Captions verified is yes. Until then the page ships without it and the build lists it.
- Target 3 to 8 minutes per piece; the build warns over 12.

Rules: reuse existing faculty media where it fits, but flag anything with live-cohort language for a trim; group field shoots into as few trips as possible; never plan a video whose only job is to read slide text aloud; when visuals carry information the narration does not, plan audio description or rewrite the narration so it names what is shown.
