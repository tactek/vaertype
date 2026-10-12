# Værtype

Velger hvilken værtype værstripen på forsiden skal vise: `warm`, `cold`, `wind` eller `precipitation`. Stripen eies av Harald Nilsen. Når redaksjonen har valgt automatisk værtype i config-siden, henter stripen typen herfra. Svarer fila ikke, eller oppfører den seg rart, bruker stripen typen som står i pconfig.

Gjelder foreløpig Vestnytt og Askøyværingen.

## Adresser

Forventede adresser. De må bekreftes etter første publisering:

- `https://tactek.github.io/vaertype/vestnytt.no.json`
- `https://tactek.github.io/vaertype/av-avis.no.json`

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

Stripen holder en type i minst tre timer, så den ikke bytter fram og tilbake. Bare en regel høyere opp i lista kan bytte før det.

Alle tersklene er første gjetninger og står øverst i `scripts/velg_type.py`.

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
