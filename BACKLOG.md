# Værtype — Backlog (open work)

The queue of **open** work. Owner decisions and deliberate non-fixes are not here: they are in `questions.md`. What
is in flight today (running jobs, the task of the day) is in `notes/handoff.md`.

**Rules**
- **No finished work.** When an item lands, delete it; git has the history. A done entry rots while still reading
  as authoritative. Measured results go to `notes/`.
- **Sections are cut along repos or file trees**, so one session (or one worktree) can take a section while another
  session takes another, and their work merges cleanly.
- **⚠ cross-repo** marks an item that needs more than one section's tree. It runs alone, in order (producer first,
  then each consumer); never inside one section's batch.
- ⏸️ marks an item that waits for a trigger (a date, a measurement, the user). The trigger is named in the item.
- An item is what is wrong or missing, a pointer to the detail, and when it is **done**. How it was found goes in
  the commit message.
- Cite an item by its **title**, never by a number: numbers move.
- **Re-confirm before acting**: an item can be done already (`/session-start` step 3). A deleted item can also come
  back through a long-lived branch that carried an old copy of this file: `git log -S'<phrase>' -- BACKLOG.md`.


---

## Jobben (`scripts/`, `.github/`)

- 🔲 **Planlagte kjøringer kommer for sjelden**: GitHub startet jobben bare 4-7 ganger i døgnet (12.-20.10.2026).
  Eieren har valgt cron-job.org (`questions.md`, «cron-job.org starter jobben»). Jobben hos cron-job.org ble satt
  opp 20.10.2026, og testkjøringen kl. 14.19 gav `204` og en vellykket kjøring. Ferdig når: `gh run list --workflow
  vaertype.yml` viser `workflow_dispatch` hver halvtime gjennom et døgn.
- ⏸️ **Forny GitHub-nøkkelen til cron-job.org**: Nøkkelen har en utløpsdato. Når den går ut, faller jobben tilbake
  til GitHub sin trege timer. Utløser: datoen eieren valgte da nøkkelen ble laget. Ferdig når: ny nøkkel ligger hos
  cron-job.org og en testkjøring gir `204`. GitHub svarer at API-versjonen `2022-11-28` forsvinner 10.3.2028; sjekk
  da også om cron-job.org må sende headeren `X-GitHub-Api-Version` med en nyere versjon.
- ⏸️ **Juster tersklene etter loggen**: Tersklene er første gjetninger. Venter på at Haralds av/på-bryter er klar.
  Da oppsummeres `logg/` (hvor ofte hver type ble valgt, bytter, hva som utløste dem). Ferdig når: tersklene er gått
  gjennom med eieren, og koden og README er oppdatert.

## Avisene

- ⏸️ **Legg til Marsteinen, Randaberg24, Stord24 og Øyposten**: De har verken værdata eller steder hos Harald
  (403 under `weather-data/<domene>/`). Venter på at dataene dukker opp. Ferdig når: domenet står i `DOMAINS` i
  `scripts/velg_type.py`, fila svarer på Pages og avisen står i README-tabellen.
- ⏸️ **Skru på automatisk værtype for én avis**: Venter på Haralds av/på-bryter i config-siden. Start med én avis,
  for eksempel Vestnytt, og ta de andre etter et par dager. Ferdig når: stripen på forsiden følger fila.
