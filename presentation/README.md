# Course presentation

- Open `slides.html` for the single-file Marp presentation.
- Open `slides.pdf` for the verified 45-page slide export.
- Open `handout.html` for the full printable class notes, exercises, and worked solutions.
- Edit `../docs/course.json`, then run `python scripts/build_materials.py` from the repo root.
- Rebuild slide HTML with `make slides`. Node 22.12+ is required only for this optional authoring task.

The generated deck uses the Automata theme in `theme/automata.css`. Theme styles are embedded; brand fonts load from Google Fonts when available, with local font fallbacks. Bullet fragments reveal during presentation; printed output shows all bullets. The deck and handout follow the same eight-lesson, 180-minute sequence.

To export a PDF after installing the pinned Node dependencies:

```bash
npm run slides:pdf
```

PDF generation requires a supported Chrome/Chromium installation. HTML remains the portable delivery format if no browser exporter is available.

The lockfile overrides Puppeteer and xmldom to patched versions. Both HTML and PDF builds were verified with these versions; `npm audit` reported zero vulnerabilities at the release check.
