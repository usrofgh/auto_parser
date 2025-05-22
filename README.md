# How to run

---

* Put `.env` in the root of the project and type:
```bash
docker compose up
```

---
# Parser's flow

### Main parser:
1. Request a proxy list from webshare(100 proxies)
2. Initialize async clients pool - 100 clients
3. Run the parser
4. Parse count of pages with card's links
5. Parse all existing card's links and save them into a table
6. Loading card's links, visiting them and scraping card's information. Result will be saved into the table

### Helper parser:
1. Load records with status 'ERROR' and type 'COMMON' and try to visit and collect card's links again
   * If success - save parsed links and change the status from 'ERROR' to 'PROCEED' 
   * If error - increment error counter. If it's 3+ errors - change status to 'DEAD'
2. Load records with status 'ERROR' and type 'CARD'
    * If success - save the card and change status of link to 'PROCEED'
    * If error - increment error counter. If it's 3+ errors - change status to 'DEAD'
3. Load records with status 'NEW' and type 'CARD' and try to parse them. It's new records after processing 'ERROR' status


### Cron
* Run main & helper parsers
* Run DB dumper and clean DB
