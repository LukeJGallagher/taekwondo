# Setup Instructions - Alert System

## Step-by-Step Guide to Get SendGrid API Key

### Option 1: SendGrid (Recommended - Free Tier Available)

#### 1. Create SendGrid Account
- Go to: https://sendgrid.com/
- Click **"Start for Free"**
- Sign up with your email (use your work email)
- **Free tier includes**: 100 emails/day (perfect for testing!)

#### 2. Verify Your Email
- Check your inbox for verification email
- Click the verification link

#### 3. Complete Setup
- Log in to SendGrid dashboard
- You may need to complete sender verification
- Go through the quick setup wizard

#### 4. Create API Key
1. **Navigate to API Keys**:
   - Click on **Settings** (left sidebar)
   - Click **API Keys**

2. **Create New Key**:
   - Click **"Create API Key"** button
   - Name: `Taekwondo Analytics`
   - Permissions: Select **"Full Access"** (for simplicity)
   - Click **"Create & View"**

3. **Copy the API Key**:
   - **IMPORTANT**: Copy the key NOW - you won't see it again!
   - It looks like: `SG.xxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyy`

#### 5. Add to .env File
1. Open `.env` file in your Taekwondo folder
2. Replace `YOUR_SENDGRID_API_KEY_HERE` with your actual key:
   ```
   SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyy
   ```

3. Replace `your.email@example.com` with your actual email:
   ```
   ALERT_EMAILS=your.email@teamsaudi.sa,coach@teamsaudi.sa
   ```

4. Save the file

---

### Option 2: Test Mode (No Email, Just Console Output)

If you want to test without email first:

1. Open `.env` file
2. Set `ALERTS_ENABLED=false`
3. Alerts will print to console instead of sending emails

---

## Verify Your Setup

### Test 1: Check .env File Loads
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key found!' if os.getenv('SENDGRID_API_KEY') else 'API Key missing')"
```

**Expected output**: `API Key found!`

### Test 2: Test Alert System
```bash
python alerts.py
```

**What happens**:
- If `ALERTS_ENABLED=true`: Sends 3 test emails to your configured address
- If `ALERTS_ENABLED=false`: Prints alerts to console only

**Check your inbox** for test emails!

### Test 3: Full System Check
```bash
python quick_start.py
```

This runs a complete system check including:
- Environment setup
- Data validation
- Alert system
- Sample analysis

---

## Troubleshooting

### "SendGrid not installed"
```bash
pip install sendgrid python-dotenv
```

### "No API key found"
- Check that `.env` file exists (not `.env.template`)
- Check that `SENDGRID_API_KEY=` has your actual key
- No quotes needed around the key
- No spaces after `=`

### "Authentication failed"
- Double-check you copied the entire API key
- Make sure you used "Full Access" permissions
- Try creating a new API key

### "No emails received"
- Check spam/junk folder
- Verify email address in `ALERT_EMAILS` is correct
- Check SendGrid dashboard for delivery status
- Try with `ALERTS_ENABLED=false` first to test without sending

### "Module not found: dotenv"
```bash
pip install python-dotenv
```

---

## Alternative: Gmail SMTP (If SendGrid Doesn't Work)

If you have issues with SendGrid, you can use Gmail:

1. **Edit `alerts.py`** and add this alternative method:

```python
import smtplib
from email.mime.text import MIMEText

def send_email_gmail(subject, html_content, to_emails):
    gmail_user = "your.email@gmail.com"
    gmail_password = "your_app_password"  # Use app password, not regular password

    msg = MIMEText(html_content, 'html')
    msg['Subject'] = subject
    msg['From'] = gmail_user
    msg['To'] = ', '.join(to_emails)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(gmail_user, gmail_password)
        smtp.send_message(msg)
```

2. **Get Gmail App Password**:
   - Go to Google Account settings
   - Security > 2-Step Verification (must be enabled)
   - App passwords > Generate new password
   - Use this password in the code above

---

## Current Configuration

After setup, your `.env` file should look like:

```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ALERT_EMAILS=yourname@teamsaudi.sa,coach@teamsaudi.sa
FROM_EMAIL=analytics@saudi-taekwondo.com
ALERTS_ENABLED=true
RANKING_CHANGE_THRESHOLD=5
OPPORTUNITY_SCORE_THRESHOLD=75
```

---

## Next Steps After Setup

Once alerts are working:

1. ✅ **Integrate with scraper**: Add validation to scraping pipeline
2. ✅ **Integrate with agents**: Add alerts to automation
3. ✅ **Customize thresholds**: Adjust alert sensitivity
4. ✅ **Add recipients**: Add coaching staff emails
5. ✅ **Schedule daily summaries**: Set up daily reports

---

## Test Commands Reference

```bash
# 1. Install dependencies
pip install pydantic sendgrid python-dotenv great-expectations

# 2. Test data validation
python data_validator.py

# 3. Test alerts (sends email!)
python alerts.py

# 4. Run full system check
python quick_start.py

# 5. Run scraper with validation
python taekwondo_scraper.py

# 6. Launch dashboard
streamlit run dashboard.py
```

---

## Support

If you have issues:
1. Check this guide first
2. Review error messages carefully
3. Try test mode (`ALERTS_ENABLED=false`) first
4. Check SendGrid dashboard for delivery logs

**SendGrid Support**: https://docs.sendgrid.com/

---

**You're almost ready! Just need to:**
1. Get SendGrid API key (5 minutes)
2. Update .env file (1 minute)
3. Run test (1 minute)

**Total time: ~7 minutes** ⏱️
