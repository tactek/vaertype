# Handoff (2026-10-20 10:25 CEST)

Read by /session-start. Open work: `BACKLOG.md`. Decisions and rulings: `questions.md`. Rewritten at each /handoff.

## Next (task of the day, in order)
1. [jobben] Sjekk at cron-job.org starter jobben: eieren valgte det 20.10.2026 og setter det opp selv etter
   README, «Timer». Jobben ble lagt inn 20.10.2026, og testkjøringen kl. 14.19 gav `204`. Sjekk `gh run list --workflow vaertype.yml`:
   `workflow_dispatch` skal komme hver halvtime. Ferdig når det har holdt et døgn.
2. [avisene] Når Haralds av/på-bryter er klar: oppsummer `logg/`, gå gjennom tersklene med eieren og skru på for
   Vestnytt først (BACKLOG: «Juster tersklene etter loggen», «Skru på automatisk værtype for én avis»).

## Waiting for the user
- Skal repoet flyttes til en organisasjon?

## Running in the background
| What | Unit / process | Ends | Check | Stop |
|---|---|---|---|---|
| Velg værtype | GitHub Actions `.github/workflows/vaertype.yml`, startet av cron-job.org hver halvtime, `schedule` som reserve | aldri | `gh run list --workflow vaertype.yml`; `updated` i `https://tactek.github.io/vaertype/vestnytt.no.json` | `gh workflow disable vaertype.yml` |

## Last session (2026-10-09 til 2026-10-20)
- Done: jobben bygd, testet og publisert med GitHub Pages for vestnytt.no, av-avis.no, bygdanytt.no, bomlo-nytt.no,
  strilen.no og sunnhordland.no. Meldingen til Harald med adressemønsteret `https://tactek.github.io/vaertype/<domene>.json`
  ble skrevet 12.10.2026. Ikke bekreftet at den er sendt. Harald lager en av/på-bryter med pconfig-typen som reserve. Workflowen satt opp i prosjektet 20.10.2026.
- Unfinished: ingenting.
- Learned: GitHub sin `schedule` er upålitelig her (se `notes/lessons.md`).
