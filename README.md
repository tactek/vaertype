# Værtype

Velger hvilken værtype værstripen på forsiden skal vise: `warm`, `cold`, `wind` eller `precipitation`. Stripen eies av Harald Nilsen. Når redaksjonen har valgt automatisk værtype i config-siden, henter stripen typen herfra. Svarer fila ikke, eller oppfører den seg rart, bruker stripen typen som står i pconfig.

## Adresser

Én fil per avis:

| Avis | Adresse |
|---|---|
| Vestnytt | `https://tactek.github.io/vaertype/vestnytt.no.json` |
| Askøyværingen | `https://tactek.github.io/vaertype/av-avis.no.json` |
| Bygdanytt | `https://tactek.github.io/vaertype/bygdanytt.no.json` |
| Bømlo-nytt | `https://tactek.github.io/vaertype/bomlo-nytt.no.json` |
| Strilen | `https://tactek.github.io/vaertype/strilen.no.json` |
| Sunnhordland | `https://tactek.github.io/vaertype/sunnhordland.no.json` |

Marsteinen, Randaberg24, Stord24 og Øyposten mangler værdata hos Harald. Når de får det, legger du domenet til i `DOMAINS` øverst i `scripts/velg_type.py`.

```json
{
  "weathertype": "wind",
  "rule": "vind",
  "reason": "Vindkast 17,2 m/s på Hernar",
  "since": "2026-10-09T14:37+02:00",
  "updated": "2026-10-09T15:07+02:00"
}
```

Stripen trenger bare `weathertype`. `updated` oppdateres hver halvtime. Er den mer enn et par timer gammel, har jobben stoppet.

## Reglene

Jobben kjører hver halvtime og bruker de samme tallene som stripen viser (Haralds filer under `weather-data/<domene>/`). Den første regelen som slår til, gjelder:

1. **Farevarsel fra MET** for land som dekker minst ett av avisens steder: vind ved vindvarsel, nedbør ved regn-, flom- eller snøvarsel. Kulingvarsel for havet teller ikke. Det gjelder ytre Øygarden de fleste høstdager.
2. **Vind:** middelvind på minst 10,8 m/s (liten kuling) eller vindkast på minst 17 m/s et sted.
3. **Nedbør:** minst 3 mm i timen et sted, eller minst 1 mm i timen på minst halvparten av stedene.
4. **Uvanlig varmt eller kaldt** for måneden:

   | Måned | Varmt fra | Kaldt fra |
   |---|---|---|
   | jan, feb | 10 | -5 |
   | mar | 12 | -3 |
   | apr | 16 | -1 |
   | mai | 20 | 2 |
   | jun | 23 | 5 |
   | jul | 25 | 7 |
   | aug | 24 | 6 |
   | sep | 20 | 3 |
   | okt | 16 | 0 |
   | nov | 12 | -2 |
   | des | 10 | -4 |

5. **Ellers årstiden:** kaldt i desember-februar, varmt i mars-august og vind i september-november. Nedbør er aldri standard, for på en tørr dag ville stripen bare vist nuller.

Stripen holder en type i minst tre timer, så den ikke bytter fram og tilbake. En regel høyere opp i lista eller
et farevarsel med høyere alvorlighetsgrad kan bytte før det. Alvorlighetsgraden lagres som `alert_level`
(2 = gult, 3 = oransje, 4 = rødt), også når et tidligere farevarsel holdes. Eldre farevarselvalg uten dette feltet
kan erstattes av et nytt farevarsel med kjent alvorlighetsgrad. Ugyldige tidligere resultater forkastes, og
jobben beregner et nytt valg for avisen.

Alle tersklene er første gjetninger og står øverst i `scripts/velg_type.py`.

## Timer

GitHub sin egen timer (`schedule` i arbeidsflyten) startet jobben bare 4-7 ganger i døgnet. Derfor starter
[cron-job.org](https://cron-job.org) jobben hver halvtime ved å sende

```
POST https://api.github.com/repos/tactek/vaertype/actions/workflows/vaertype.yml/dispatches
Authorization: Bearer <nøkkel>
Accept: application/vnd.github+json
{"ref": "main"}
```

GitHub svarer `204` og starter jobben med en gang. Nøkkelen er en fine-grained GitHub-nøkkel som bare gjelder dette
repoet, med tillatelsen Actions: Read and write. Den ligger bare hos cron-job.org. Når den går ut, faller jobben
tilbake til GitHub sin trege timer, så lag en ny før utløpsdatoen. Flyttes repoet, må adressen hos cron-job.org
endres. Jobben hos cron-job.org ligger på Tom Croziers private konto.

## Logg

Hver kjøring legger en linje per avis i `logg/<år>-<måned>.csv`: hva som vises, hva reglene foreslår akkurat nå, og de viktigste tallene. Bruk den til å justere tersklene.

## Kjøre lokalt

```sh
python3 -m unittest discover -s tests       # testene
python3 scripts/velg_type.py --dry-run      # vis valget nå uten å skrive filer
```

## Oppsett på GitHub (én gang)

1. Lag et offentlig repo `vaertype` og push koden.
2. **Settings → Pages → Source:** velg **GitHub Actions**.
3. **Actions → Velg værtype → Run workflow** for første kjøring.
4. Sjekk at adressene over svarer, og send dem til Harald.

GitHub sender e-post hvis en kjøring feiler. I offentlige repoer skrur GitHub av planlagte jobber etter 60 dager uten aktivitet, men jobben committer loggen hver halvtime, så det skjer ikke.
