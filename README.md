# התראה על הופעות חדשות של שחר חסון

הסקריפט בודק פעמיים ביום את [עמוד ההופעות בקומדי בר](https://comedybar.net/%D7%A9%D7%97%D7%A8-%D7%97%D7%A1%D7%95%D7%9F-%D7%94%D7%95%D7%A4%D7%A2%D7%95%D7%AA/).
כשמופיעה הופעה חדשה, נשלח מייל עם התאריך, השעה, האולם וקישור ישיר לקניית כרטיסים.

- `check_shows.py`: הסקריפט עצמו.
- `seen_shows.json`: ההופעות שכבר נראו, ומתעדכן אוטומטית.
- `.github/workflows/check.yml`: התזמון, בסביבות 09:15 ו-18:15 שעון ישראל.

## הגדרה חד-פעמית

1. **App Password של Gmail**
   - צריך להפעיל אימות דו-שלבי בחשבון Google, אם הוא עוד לא מופעל.
   - נכנסים ל-https://myaccount.google.com/apppasswords, יוצרים סיסמה בשם `show-alert` ומעתיקים את 16 התווים.
2. **Secrets ב-GitHub**
   - ברפו נכנסים ל-Settings, אחר כך Secrets and variables, Actions, ואז New repository secret.
   - מוסיפים את הערכים האלה:
     - `GMAIL_USER`: כתובת ה-Gmail ששולחת את המייל.
     - `GMAIL_APP_PASSWORD`: הסיסמה מסעיף 1.
     - `ALERT_TO`: הכתובת שמקבלת את ההתראות. לא חובה, וברירת המחדל היא `GMAIL_USER`.
3. **בדיקה**
   - בלשונית Actions בוחרים את "Check Shahar Hason shows" ולוחצים Run workflow.

אם האתר ישנה את המבנה שלו והסקריפט לא ימצא הופעות, ההרצה תיכשל ו-GitHub ישלח על זה מייל.
