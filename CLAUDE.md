# Værtype

Velger automatisk hvilken værtype (`warm`, `cold`, `wind` eller `precipitation`) værstripen på forsiden til
Polaris-avisene i Vest skal vise, og publiserer valget som én JSON-fil per avis. Eier: Tom Crozier, som bestemmer
prioriteringer og alt som går utad. Stripen selv, værdataene og stedslistene eies av Harald Nilsen; vi bare leser
dem. Koden ligger i ett **offentlig** repo (`github.com/tactek/vaertype`), så alt som committes er offentlig: ingen
nøkler, ingen interne samtaler, ingen personopplysninger utover navn som allerede står i README.

**Sessions:** start with `/session-start`, end with `/handoff` (skills in `.claude/skills/`). Both first run
`.claude/skills/session-start/ground-truth.sh` (repos, worktrees, open PRs + CI, background jobs; configured in
`.claude/ground-truth.conf`): the handoff is a claim, the script is the fact, and a contradiction is reported first.

**Trackers:** open work is in `BACKLOG.md` (a finished item is deleted), questions for the owner and standing rulings
in `questions.md`, today's tasks and what runs in `notes/handoff.md`. This file keeps only state, rules and
how-tos: no to-dos, no decisions waiting, no PR lists or history (git has them).

**Lessons** learned in this project, loaded every session: @notes/lessons.md

This setup comes from the workflow repo (`.claude/workflow-version` names the commit). When a
session improves a generic piece (a skill, the ground-truth script), port that part back there.

## Rules

- **Outward actions need the owner's OK:** push, PR, merge, release, comments, messages to anyone. An approval
  covers the action it was given for, not the next one.
- **Handoff rule:** /handoff asks before committing.
- Stage the paths you changed (`git add <paths>`), never `git add -A` / `git add .`; read `git diff --cached
  --name-only` before committing. The owner drops working files into the tree.
- No secrets in tracked files. If one is needed, write that it is needed and where it lives, never its value.
- **Kontrakten med Harald er bare `weathertype`**, pluss `updated`, som han kan bruke til å se om fila er gammel.
  De andre feltene kan endres fritt. `reason` er intern og vises aldri for leserne.
- **`public/` og `logg/` skrives av jobben**, aldri for hånd. Boten committer på `main` ved hver kjøring, så kjør
  `git pull` før du endrer noe.
- **Reglene står to steder:** tersklene øverst i `scripts/velg_type.py` og forklaringen i `README.md`. Endres den
  ene, endres den andre.
- **Ikke en CNP-widget:** ingen `embed.js` og ingen embed-linje. Haralds stripe leser fila direkte.
- **Hosting er GitHub Pages, ikke Render** (se `questions.md` §2).
- Verifiser med testene og en `--dry-run` mot ekte data før push.

## Repos and layout

Ett repo, standardgren `main`, remote `origin` = `https://github.com/tactek/vaertype`.

- `scripts/velg_type.py`: reglene og jobben (bare standardbiblioteket).
- `tests/`: enhetstester for reglene og holdetiden.
- `.github/workflows/vaertype.yml`: kjører testene og jobben, committer `public/` og `logg/`, publiserer `public/`
  til GitHub Pages.
- `public/<domene>.json`: filene stripen leser, `https://tactek.github.io/vaertype/<domene>.json`.
- `logg/<år>-<måned>.csv`: én linje per avis per kjøring, til å justere tersklene.

## Commands

```sh
python3 -m unittest discover -s tests       # porten: testene (kjøres også først i hver jobb)
python3 scripts/velg_type.py --dry-run      # valget nå mot ekte data, uten å skrive filer
gh workflow run vaertype.yml                # start jobben for hånd
gh run list --workflow vaertype.yml         # siste kjøringer
```
