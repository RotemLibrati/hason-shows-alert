# התראה על הופעות חדשות של שחר חסון

הסקריפט בודק כל שעה את [עמוד ההופעות בקומדי בר](https://comedybar.net/%D7%A9%D7%97%D7%A8-%D7%97%D7%A1%D7%95%D7%9F-%D7%94%D7%95%D7%A4%D7%A2%D7%95%D7%AA/).
כשמופיעה הופעה חדשה, נשלח מייל מיד עם התאריך, השעה, האולם וקישור ישיר לקניית כרטיסים.
בנוסף, בכל ערב בסביבות 20:00 (שעון ישראל) נשלח מייל סיכום: כמה בדיקות רצו, כמה הצליחו, ואם נמצאו הופעות חדשות.

- `check_shows.py`: הסקריפט עצמו.
- `seen_shows.json`: ההופעות שכבר נראו, ומתעדכן אוטומטית.
- `run_log.json`: יומן הבדיקות מאז הסיכום האחרון, ומתעדכן אוטומטית.
- `.github/workflows/check.yml`: התזמון, כל שעה.

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

## הרצה על שרת (במקום GitHub Actions)

צריך שרת Linux עם Python 3.9 ומעלה ו-git.

```bash
git clone https://github.com/RotemLibrati/hason-shows-alert.git ~/hason-shows-alert
cd ~/hason-shows-alert
cp .env.example .env
nano .env        # ממלאים כתובת Gmail, App Password, ו-STATE_DIR (למשל /home/<user>/hason-data)
chmod 600 .env
./run.sh && cat "$(grep STATE_DIR .env | cut -d= -f2)/cron.log"   # בדיקה ידנית
crontab -e       # מוסיפים את השורה:  0 * * * * $HOME/hason-shows-alert/run.sh
```

- הקבצים `seen_shows.json`, `run_log.json` ו-`cron.log` נשמרים בתיקיית `STATE_DIR`, מחוץ לקוד, כך ש-`git pull` לעדכון קוד לא מתנגש איתם.
- אחרי שהשרת עובד, מכבים את ההרצה ב-GitHub (Actions → Check Shahar Hason shows → `...` → Disable workflow), אחרת יגיעו מיילים כפולים.
