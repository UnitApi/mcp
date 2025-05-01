# Współpraca nad projektem unitmcp

Dziękujemy za zainteresowanie projektem unitmcp! Poniżej znajdziesz informacje, jak możesz przyczynić się do rozwoju biblioteki.

## Sposób współpracy

1. **Zgłaszanie błędów i sugestii**
   - Przed zgłoszeniem sprawdź, czy problem nie został już zgłoszony
   - Użyj szablonu zgłoszenia błędu lub funkcji
   - Podaj jak najwięcej szczegółów, aby ułatwić reprodukcję problemu

2. **Propozycje zmian**
   - Omów swoją propozycję w Issues przed rozpoczęciem pracy
   - Fork repozytorium i stwórz branch dla swojej zmiany
   - Zapoznaj się ze standardami kodowania
   - Napisz testy dla nowej funkcjonalności
   - Wyślij Pull Request

3. **Dokumentacja**
   - Poprawianie istniejącej dokumentacji
   - Dodawanie nowych przykładów
   - Tłumaczenie dokumentacji na inne języki

## Przygotowanie środowiska deweloperskiego

1. Sklonuj repozytorium:
```bash
git clone https://gitlab.com/unitmcp/python.git
cd unitmcp
```

2. Utwórz i aktywuj wirtualne środowisko:
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# lub
venv\Scripts\activate  # Windows
```

3. Zainstaluj pakiet w trybie deweloperskim:
```bash
pip install -e ".[dev]"
```

4. Sprawdz potrzebne i niezbędne pakiety
```bash
pipreqs --force .
```


## Standardy kodowania

- **Formatowanie**: Używamy Black do formatowania kodu
- **Linting**: Używamy flake8 do sprawdzania jakości kodu
- **Importy**: Używamy isort do sortowania importów
- **Testy**: Wymagane testy dla nowej funkcjonalności


## Tworzenie Pull Requesta

1. Upewnij się, że wszystkie testy przechodzą
2. Zaktualizuj dokumentację, jeśli to konieczne
3. Dodaj swoje zmiany do [CHANGELOG.md](CHANGELOG.md)
4. Wyślij Pull Request z jasnym opisem zmian
5. Poczekaj na review od członków zespołu

## Wytyczne dla Pull Requestów

- Jeden Pull Request powinien rozwiązywać jeden problem
- Trzymaj Pull Requesty niewielkie i skoncentrowane na jednej zmianie
- Nazwa brancha powinna mieć format: `[typ]/[krótki-opis]`, np. `feature/add-lora-support`
- Opisz jasno, co i dlaczego zostało zmienione

## Proces Review

1. Maintainerzy projektu przejrzą Twój kod
2. Mogą poprosić o zmiany lub ulepszenia
3. Po akceptacji, zmiany zostaną scalone z głównym branchem

## Wytyczne etyczne

Projekt unitmcp koncentruje się na tworzeniu bezpiecznych narzędzi dla dzieci. Prosimy o przestrzeganie następujących zasad:

1. Priorytetem jest bezpieczeństwo i prywatność dzieci
2. Kod nie powinien zbierać niepotrzebnych danych
3. Wszystkie funkcje AI powinny mieć odpowiednie zabezpieczenia
4. Treści muszą być odpowiednie dla dzieci

## Licencja

Wnosząc wkład do projektu, zgadzasz się na udostępnienie swoich zmian na licencji MIT.

## Kontakt

W razie pytań, skontaktuj się z nami.
Dziękujemy za Twój wkład w projekt unitmcp!