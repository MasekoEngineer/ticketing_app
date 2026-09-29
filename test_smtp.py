import smtplib
from email.mime.text import MIMEText

SENDER = 'peniatest@gmail.com'
APP_PASSWORD = 'cjwf dprh otrh sxiy'
RECIPIENT = 'peniatest@gmail.com'

msg = MIMEText('Test from TicketHub')
msg['Subject'] = 'SMTP Test'
msg['From'] = SENDER
msg['To'] = RECIPIENT

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER, APP_PASSWORD)
    server.send_message(msg)
    server.quit()
    print('[SUCCESS] SMTP works — email sent')
except Exception as e:
    print(f'[FAILED] {e}')