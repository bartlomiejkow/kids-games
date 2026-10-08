# Wspólny pokój Memory

Uruchom z katalogu `projects/docker/nginx/`:

```bash
docker compose config --quiet
docker compose up -d --build
```

Na obu Chromebookach otwórz ten sam adres strony i wybierz Memory.
Przy dostępie przez Wi-Fi użyj adresu serwera, np.
`http://ADRES-IP-SERWERA:8001/games/memory/`, zamiast `localhost`.
Istniejący tunel może nadal kierować na Nginx na porcie 8001;
WebSocket korzysta z tego samego adresu i automatycznie z WSS przy HTTPS.

Tryb „Dwa urządzenia” włącza się domyślnie. Dwie pierwsze otwarte karty
zajmują miejsca graczy. Zamknij zbędne karty, jeśli pokój jest pełny.
Po rozłączeniu gra czeka na drugą osobę; wolne miejsce może zająć
kolejne połączenie. „Nowa gra” resetuje planszę obu graczom.
Tryb „Jedno urządzenie” działa lokalnie, bez serwera synchronizacji.

Pokój nie wymaga logowania: każdy, kto ma dostęp do strony, może dołączyć.
Stan gry znajduje się w pamięci. Restart serwera albo wyjście obu graczy
rozpoczyna nową grę.

Testy logiki (z zainstalowanymi zależnościami z requirements.txt):

```bash
cd memory-server
python -m unittest discover -s tests
```

Po uruchomieniu sprawdź na dwóch urządzeniach: wspólną planszę, blokadę
ruchu drugiego gracza, dobraną i niedobraną parę, wyniki, zakończenie,
restart podczas odkrytej pary, odświeżenie strony i rozłączenie.
Sprawdź też tryb lokalny oraz konsolę przeglądarki.
