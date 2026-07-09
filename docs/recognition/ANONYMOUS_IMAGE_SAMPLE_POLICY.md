# Anonymous Image Sample Policy

An anonymous image is a single answer-sheet image prepared so it cannot identify a real student, school, class, exam number, or real score.

Forbidden content:

- real student name
- real student number
- school name
- class name
- exam number
- real score
- any real personally identifying mark

Allowed demo content:

- `Demo`
- `S001`
- `Test Student A`
- synthetic marks created only for this trial

How to prepare one by hand:

1. Use a blank or copied answer sheet layout.
2. Fill identity fields with demo labels only.
3. Mark a few choice cells and blank answers with synthetic content.
4. Photograph or scan the page.
5. Name it with a neutral local filename such as `demo_anonymous_image.png`.
6. Store it under an untracked local path such as `data/tmp`.

Do not commit the image. The repository may contain manifest metadata and synthetic ROI JSON, but not the image bytes.

Do not commit raw API responses. Raw responses can contain vendor metadata, OCR text, or accidental sensitive content.

A successful single anonymous image check does not permit batch use. It only permits considering a later single explicit real API trial.
