# Wspólny pokój Memory

Ten sam serwer obsługuje również osobny pokój wyścigów pod `/racing-ws`.
Wyścigi są dostępne w menu lub pod `/games/racing/`. Każdy gracz naciska
„Gotowy!”, potem następuje wspólne odliczanie. Sterowanie: strzałki lewo/prawo
albo przyciski ekranowe. Auta jadą automatycznie; przeszkody spowalniają je.
Po rozłączeniu wyścig się zatrzymuje. Po powrocie kliknij „Wracam do gry!”.
Rewanż jest dostępny po zakończeniu i wymaga ponownej gotowości obu graczy.
Pokoje Memory i wyścigów są niezależne.

Uruchom z katalogu `projects/docker/nginx/`:

```bash
sh deploy.sh
```

Na obu Chromebookach otwórz ten sam adres strony i wybierz Memory.
Przy dostępie przez Wi-Fi użyj adresu serwera, np.
`http://ADRES-IP-SERWERA:8001/games/memory/`, zamiast `localhost`.
Istniejący tunel może nadal kierować na Nginx na porcie 8001;
WebSocket korzysta z tego samego adresu i automatycznie z WSS przy HTTPS.

Skrypt odtwarza kontenery, aby Nginx wczytał zmienioną konfigurację
i aktualny adres serwera gier. Samo `up -d --build` może pozostawić działający
Nginx ze starą konfiguracją. Wdrożenie przerywa bieżące rozgrywki.

Jeśli gra stale ponawia połączenie, sprawdź:

```bash
docker compose ps
docker compose logs --tail 50 memory-server web-serwer
docker compose exec web-serwer nginx -T
```

Aktywna konfiguracja Nginxa musi obsługiwać zarówno `/memory-ws`,
jak i `/racing-ws`. Kod 404 dla `/racing-ws` w logach oznacza brak trasy,
502 wskazuje problem połączenia z backendem, a 403 odrzucenie Origin.

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

W wyścigach sprawdź na dwóch urządzeniach: gotowość obu osób i odliczanie,
strzałki oraz przyciski ekranowe, spowolnienie po przeszkodzie, wspólne wyniki,
rewanż, odświeżenie i wznowienie, odmowę wejścia trzeciej osobie oraz układ
na małym ekranie. Backend wymaga ponownego zbudowania po zmianie kodu.
