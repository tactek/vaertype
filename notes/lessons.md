# Lessons

Lessons learned in this project that every session needs: `CLAUDE.md` imports this file, so it loads at every
session start and travels with the repo to every machine and cloud session. `/handoff` adds a lesson here when it
distils the old handoff (step 2) and saves memories (step 5); a narrow fact goes into a memory instead. Keep it
short: merge rather than append, and drop what no longer holds.

<!-- One section per area (git, long runs, verification, a tool of this project), one line per lesson: the rule,
then its reason in a few words. -->

## Arbeid med eieren

- Svar på norsk (bokmål), med bindestrek, aldri tankestrek. Eieren er ikke utvikler på heltid: forklar Git, GitHub
  og terminalsteg konkret.
- Et spørsmål om «mye kode» er ikke en bestilling om å kutte. Forklar hva delene gjør og hva det koster å fjerne dem,
  og spør før du forenkler. En forenkling ble rullet tilbake 12.10.2026.

## GitHub Actions

- `schedule` er upålitelig her: 4-7 kjøringer i døgnet i stedet for 48. Sjekk `gh run list` før du lover at jobben
  går hver halvtime.
- En push med `GITHUB_TOKEN` starter ikke andre arbeidsflyter. Derfor publiserer jobben selv til Pages i samme
  kjøring.

## Datakildene

- `updated_time` i Haralds filer er år-dag-måned (`2026-09-10` er 9. oktober). Bruk HTTP-headeren `Last-Modified`.
- api.met.no krever en User-Agent som sier hvilken app som spør og hvordan eieren kan nås.
