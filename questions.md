# Værtype — open questions and deliberate non-fixes

| file | holds |
|---|---|
| `BACKLOG.md` | the open-work queue |
| this file | **§1** questions only the owner can decide · **§2** rulings and deliberate non-fixes, so they are not "rediscovered" as bugs or "rescued" by a push |

Status: 💬 needs the owner's decision · 🟢 decided (ruling in force) · ⏸️ deferred, with its trigger

An entry is the question (or the ruling), its reason, and a pointer to the detail. Name things by what the owner
sees (a screen's title, a command), not by code names. A question carries the options and a recommendation. When
the owner rules, the entry moves to §2 as 🟢 with their words and the date, or it is deleted if nothing is left to
guard. Cite an entry by its **title**.

---

# 1. Open decisions 💬

## 💬 Skal repoet flyttes til en organisasjon?
Repoet og Pages-siden ligger på eierens private GitHub-konto (`tactek`). Det låser ikke kontoen, men en tjeneste for
avisene blir avhengig av én persons konto. Valg: flytte til en GitHub-organisasjon jobben eier (adressen blir
`<organisasjon>.github.io/vaertype`), eller bli liggende. Anbefaling: flytt, hvis Polaris eller PM Vest har en
organisasjon, og gjør det før Harald legger adressen inn i stripen. Da må også adressen hos cron-job.org endres.

# 2. Rulings and deliberate non-fixes — do not "fix" these by reflex

## 🟢 GitHub Pages, ikke Render
Fila skrives på nytt hver halvtime. På Render ville hver ny versjon vært et bygg, og gratisplanen har 500
byggeminutter i måneden. Går de tomme, stopper alle bygg ut måneden, også for andre prosjekter som foerognaa.
Pages er gratis for dette og ligger i samme repo. Foreslått 9.10.2026 og tatt i bruk da repoet ble
satt opp 12.10.2026.

## 🟢 cron-job.org starter jobben
GitHub sin `schedule` startet jobben bare 4-7 ganger i døgnet (12.-20.10.2026). Eieren valgte cron-job.org (valg A
av A: cron-job.org, B: Render cron job, C: godta GitHub sin timer): «Kjør A da.», 20.10.2026. `schedule` står igjen
i arbeidsflyten som reserve. Oppsettet står i README under «Timer». Kontoen hos cron-job.org står på eierens private
e-post, fordi bekreftelsen til jobbadressen aldri kom fram: «Jeg tenker at jeg tar det på min private mail
isteden.», 20.10.2026.

## 🟢 Kulingvarsel for havet teller ikke
Bare farevarsler for land (`geographicDomain` = `land`) som dekker minst ett av avisens steder, teller. 9.10.2026
dekket kulingvarselet «Slåtterøy - Fedje» 15 av Vestnytts 61 steder, mens vinden på land var 8 m/s. Slike varsler
gjelder ytre Øygarden de fleste høstdager.

## 🟢 Hele versjonen av skriptet beholdes
En forenklet versjon (ett punkt per avis for farevarsler, ingen prioriteter, færre tester) ble prøvd 12.10.2026.
Eieren valgte å gå tilbake til den hele versjonen. Ikke forenkle reglene eller fjern tester uten å spørre.

## 🟢 Begrunnelsen er intern
`reason` er faste setninger med tall satt inn, ikke KI-tekst, og stripen leser den ikke. Den trenger derfor ikke
nynorsk eller leserspråk.
