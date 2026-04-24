# sukhdeepsingh.eu

Personal blog by Sukhi Singh. Notes from the edge of biology and machine intelligence.

**[sukhdeepsingh.eu](https://sukhdeepsingh.eu)**

---

Writing about antibody engineering, AI, bioinformatics, and the intersection of life science and software. Based in the Netherlands, working at ENPICOM.

## Stack

- [Astro 6](https://astro.build) + Bookworm Light theme
- Hosted on GitHub Pages, deployed via GitHub Actions on push to `main`
- Comments via [Giscus](https://giscus.app)
- Newsletter via [Buttondown](https://buttondown.com)

## Local dev

```
npm install --legacy-peer-deps
npm run dev
```

## Publishing

Stage your changes, then:

```
bash scripts/commit.sh "what changed"
git push
```

Each commit gets a short UUID as its message. The full changelog lives in [log/](log/).
