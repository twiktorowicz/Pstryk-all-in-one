# Pstryk All in One - Home Assistant (fork z poprawkami API)

> **Ten fork rozwiązuje problem z cenami sprzedaży (prosument) po zmianach API Pstryk z kwietnia 2026.**
>
> Oryginalny issue: [szkocot/Pstryk-all-in-one#2 — "This endpoint requires a partner API key"](https://github.com/szkocot/Pstryk-all-in-one/issues/2)

## Co zostało naprawione?

### 1. Ceny sprzedaży — błąd 403 (`/integrations/prosumer-pricing/`)
Pstryk zamknął endpoint `/integrations/prosumer-pricing/` — wymaga teraz **partner API key**, którego zwykli użytkownicy nie mają. Integracja sypała błędami:
```
Błąd autoryzacji (403). Treść: {"detail":"This endpoint requires a partner API key."}
```

**Rozwiązanie:** Ceny sprzedaży (prosument) pobierane są teraz z nowego endpointu `unified-metrics` z parametrem `?metrics=pricing`. Odpowiedź zawiera pola `price_prosumer_net` i `price_prosumer_gross` — nie potrzeba osobnego endpointu.

### 2. Filtrowanie nieopublikowanych cen (`tge_price: null`)
API zwraca `price_prosumer_gross = 0.0` zarówno dla:
- godzin z ujemną ceną TGE (prawidłowo — prosument dostaje 0 zł)
- godzin **jeszcze nieopublikowanych** (nieprawidłowo — to nie jest realna cena)

**Rozwiązanie:** Sprawdzamy `tge_price` — jeśli jest `null`, godzina nie ma jeszcze ceny i jest oznaczana jako `None` zamiast `0.0`.

### 3. Cache cen na jutro — brak retry przy danych częściowych
Oryginalna wersja cache'owała dane na jutro nawet jeśli były niekompletne (np. pobrane o 13:00, gdy TGE opublikowało dopiero 20 z 24 godzin). Potem nie próbowała ponownie.

**Rozwiązanie:** Cache zapisywany jest tylko gdy dane są kompletne (24 godziny z cenami). Dane częściowe są używane, ale nie cache'owane — integracja spróbuje ponownie przy następnym cyklu odświeżania.

### 4. Throttle backoff zmniejszony
Domyślny backoff po HTTP 429 zmniejszony z 3600s (1h) do 120s (2min), z limitem 300s. Dzięki temu po chwilowym throttlingu integracja wraca do działania znacznie szybciej.

---

## Zmienione pliki

| Plik | Opis zmian |
|------|------------|
| `api.py` | Nowa metoda `_normalize_unified_prosumer_pricing_response()` — pobiera ceny sprzedaży z `unified-metrics` zamiast zamkniętego endpointu. Filtruje `tge_price=null`. Skrócony throttle backoff. |
| `__init__.py` | Funkcja `_has_complete_price_data()` — cache na jutro tylko gdy 24h kompletne, dane częściowe nie blokują retry. |
| `const.py` | Usunięty `API_PROSUMER_PRICING_PATH` (endpoint wymaga partner key). |
| `sensor.py` | `price: None` → `price: 0.0` w atrybutach ramek cenowych, żeby godziny nie znikały z dashboardu. |

---

## Oryginalne README
[![Buy me a coffee](https://img.buymeacoffee.com/button-api/?slug=kubass4&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=FFFFFF&text=Buy+me+a+coffee)](https://www.buymeacoffee.com/kubass4)

Integracja Home Assistant dla serwisu Pstryk.pl, zapewniająca dostęp do danych o cenach energii (zakup/sprzedaż), zużyciu, produkcji, kosztach i saldzie rozliczeniowym.

![Przykładowy dashboard](images/dashboard_example.png)

## Funkcje

*   Pobieranie aktualnych i przyszłych (jutrzejszych) cen zakupu i sprzedaży energii.
*   Informacje o dziennym i miesięcznym zużyciu/produkcji energii (w kWh).
*   Informacje o dziennych i miesięcznych kosztach/wartości produkcji (w PLN).
*   Saldo rozliczeniowe dzienne i miesięczne (w PLN i kWh).
*   Atrybuty sensorów zawierające szczegółowy podział godzinowy/dzienny danych.
*   Konfigurowalne progi taniej/drogiej energii.
*   Konfiguracja za pomocą Klucza API.

## Instalacja

### Zalecana metoda (HACS)

1.  Upewnij się, że masz zainstalowany HACS.
2.  W Home Assistant przejdź do HACS -> Integracje.
3.  Dodaj to repozytorium jako niestandardowe repozytorium:
    *   W HACS -> Integracje, kliknij trzy kropki w prawym górnym rogu i wybierz "Niestandardowe repozytoria".
    *   Wklej URL tego repozytorium: `https://github.com/twiktorowicz/Pstryk-all-in-one`
    *   Wybierz kategorię "Integracja".
    *   Kliknij "Dodaj".
4.  Znajdź "Pstryk AIO" na liście i kliknij "Zainstaluj".
5.  Uruchom ponownie Home Assistant.

### Instalacja ręczna

1.  Sklonuj to repozytorium lub pobierz pliki ZIP.
2.  Skopiuj katalog `custom_components/pstryk_aio/` do katalogu `custom_components` w konfiguracji Home Assistant.
3.  Uruchom ponownie Home Assistant.

## Konfiguracja

Po ponownym uruchomieniu Home Assistant:

1.  Przejdź do Ustawienia -> Urządzenia i usługi.
2.  Kliknij przycisk "Dodaj integrację".
3.  Wyszukaj "Pstryk AIO".
4.  Wprowadź swój Klucz API Pstryk.pl. Klucz API znajdziesz w panelu Pstryk.pl w sekcji Konto -> Urządzenia i integracje -> Klucz API.
5.  Skonfiguruj opcje, takie jak progi cenowe i interwał aktualizacji.
6.  Zakończ konfigurację.

Integracja utworzy sensory dla dostępnych danych.

## Zastosowanie

Jeśli chcesz uzyskać widok jak w dashboardzie poniżej, to przejdź do ![Dashboardy](README_dashboards.md) 

![Przykładowy dashboard](images/dashboard.png)

## Sensory

Integracja tworzy następujące sensory:

*   `sensor.pstryk_aio_obecna_cena_zakupu_pradu`
*   `sensor.pstryk_aio_cena_zakupu_pradu_jutro`
*   `sensor.pstryk_aio_obecna_cena_sprzedazy_pradu`
*   `sensor.pstryk_aio_cena_sprzedazy_pradu_jutro`
*   `sensor.pstryk_aio_dzienne_koszty_zuzycia_energii`
*   `sensor.pstryk_aio_dzienna_wartosc_produkcji_energii`
*   `sensor.pstryk_aio_saldo_rozliczeniowe_miesieczne_pln`
*   `sensor.pstryk_aio_saldo_energetyczne_miesieczne_kwh`
*   `sensor.pstryk_aio_saldo_rozliczeniowe_dzienne_pln`
*   `sensor.pstryk_aio_saldo_energetyczne_dzienne_kwh`
*   `sensor.pstryk_aio_dzienne_zuzycie_energii_kwh`
*   `sensor.pstryk_aio_dzienna_produkcja_energii_kwh`
*   `sensor.pstryk_aio_miesieczne_zuzycie_energii_kwh`
*   `sensor.pstryk_aio_miesieczna_produkcja_energii_kwh`
*   `sensor.pstryk_aio_miesieczne_koszty_zuzycia_energii_pln`
*   `sensor.pstryk_aio_miesieczna_wartosc_produkcji_energii_pln`

## Wsparcie

Jeśli napotkasz problemy, otwórz zgłoszenie (issue) w tym repozytorium: `https://github.com/twiktorowicz/Pstryk-all-in-one/issues`.

## Autor

Fork: [twiktorowicz](https://github.com/twiktorowicz) | Oryginał: [szkocot](https://github.com/szkocot/Pstryk-all-in-one)

## Licencja

Ten projekt jest objęty licencją MIT. Szczegóły znajdziesz w pliku LICENSE.
