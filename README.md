# How to run

Place the `.env` file in the project root
```bash
git pull https://github.com/usrofgh/auto_parser.git
cd auto_parser
docker compose up
```
---

# Parser's flow

### Main parser:

1. Request 100 proxies from Webshare 
2. Initialize an asynchronous client pool of 100 clients 
3. Start parsing 
4. Determine how many pages contain card links 
5. Extract all card links and save them to the links table 
6. Load each link, visit the page, scrape the card data, and save it to the data table

### Helper parser:

1. Retry failed “COMMON” records:
   * Load entries with status ERROR and type COMMON 
   * For each, try to fetch and extract card links 
     * On success, delete an item from this errors table
     * On failure, increment error count; if ≥ 3, mark as DEAD (the problem must be verified on yourself)


2. Retry failed “CARD” records:
   * Load entries with status ERROR and type CARD
   * For each, try to fetch and scrape the card data
     * On success, save data and set status to PROCEED 
     * On failure, increment error count; if ≥ 3, mark as DEAD


3. Process new “CARD” records:
   * Load entries with status NEW and type CARD (they appeared after retrying 'COMMON' parsing) 
   * For each, attempt to parse as above

---

### Cron
* Run main and helper parsers 
* Dump the database and perform cleanup
