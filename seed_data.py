# Seeds the DB with 2000 spam messages and 2000 ham messages
import sqlite3, os, random
SPAM_TEMPLATES = [
    "Win a $1000 gift card now! Click here: {url}",
    "You have been selected for a prize. Reply to claim.",
    "Lowest price on meds, buy now: {url}",
    "URGENT: Your account has been compromised. Verify here: {url}",
    "Work from home and earn $500/day. Sign up: {url}",
]
HAM_TEMPLATES = [
    "Meeting tomorrow at 10am about project update.",
    "Here's the invoice for last month's services.",
    "Family dinner on Sunday — are you free?",
    "Please review the attached report and share feedback.",
    "Reminder: clinic appointment on Monday at 9am.",
]
URLS = ['http://bit.ly/offer','http://cheapmeds.example','http://example.com/login']

from models import get_db, init_db
DB = os.path.join(os.path.dirname(__file__), 'data', 'emails.db')
init_db(DB)
conn = get_db(DB)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM emails')
count = cur.fetchone()[0]
if count >= 4000:
    print('Already seeded')
else:
    for i in range(2000):
        t = random.choice(SPAM_TEMPLATES).format(url=random.choice(URLS)) + f" -- promo id {i}"
        cur.execute('INSERT INTO emails (text, label) VALUES (?, ?)', (t, 'spam'))
    for i in range(2000):
        t = random.choice(HAM_TEMPLATES) + f" -- note {i}"
        cur.execute('INSERT INTO emails (text, label) VALUES (?, ?)', (t, 'ham'))
    conn.commit()
    print('Seeded 4000 messages (2000 spam, 2000 ham)')
conn.close()
