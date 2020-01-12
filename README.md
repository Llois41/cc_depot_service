# cc_depot_service

## Doku

Es gibt die folgenden API-Aufrufmöglichkeiten

- /user POST
  - fügt einen neuen User hinzu
  - JSON Body:
    - name
    - email
    - pwd (das Passwort)
- /user GET
  - gibt alle user zurück
  - kein JSON Body
- /user PUT
  - Userdaten aktualisieren
  - JSON Body:
    - id
    - name
    - email
    - pwd
- /user/<userid> GET
  - gibt alle Userdaten zu der UserID zurück
- /user/<userid> DELETE
  - löscht einen User
- /depot POST
  - erstellt ein Depot für einen User mit einem angegebenen Budget
  - JSON Body
    - userid
    - budget
- /depot GET
  - gibt alle depots aus?
- /depot/user/<userid> GET
  - gibt alle depots zu einem User aus
- /depot/<depotid> PUT
  - kauft oder verkauft Aktien, je nach Typ angabe:
  - JSON Body:
    - type: 'sell' or 'buy'
    - share
    - amount

