# RPL_AutoRenewal
 
Automatically renews books that are due soon at the [Regina Public Library](https://www.reginalibrary.ca) and emails you a confirmation for each one. It uses Selenium to log in to your library account, runs on a daily schedule with GitHub Actions, and can also be run on your own computer.
 
## How it works
 
1. Opens the "Overdue Soon" page of your Regina Public Library account.
2. Logs in with your library barcode and password.
3. Clicks **Renew** on each book that is due soon, one at a time.
4. Sends an email (through Gmail) after every renewal, and a final "No more books to be renewed today" email when there is nothing left.
## Files
 
| File | Purpose |
| --- | --- |
| `library_renewal.py` | The Selenium script that logs in, renews books and sends the emails |
| `requirements.txt` | Python dependencies (`selenium`, `python-dotenv`) |
| `.github/workflows/library_renewal.yaml` | GitHub Actions workflow that runs the script every day |
 
## Run it on GitHub Actions (recommended)
 
### 1. Add your credentials as repository secrets
 
Go to **Settings -> Secrets and variables -> Actions -> New repository secret** and create these four secrets:
 
| Secret | Value |
| --- | --- |
| `BARCODE` | Your library card barcode |
| `PASSWORD` | Your library account password |
| `EMAIL` | The Gmail address that sends the emails and receives them |
| `SENDER_PASSWORD` | A [Gmail app password](https://support.google.com/accounts/answer/185833) for that address (not your normal Gmail password) |
 
### 2. Check the schedule
 
The workflow in `.github/workflows/library_renewal.yaml` runs every day at **15:00 UTC (9:00 AM in Regina)**. To change the time, edit the `cron` line:
 
```yaml
schedule:
  - cron: "0 15 * * *"
```
 
Saskatchewan does not use daylight saving time, so Regina is always UTC-6.
 
### 3. Run it manually to test
 
Open the **Actions** tab, choose **RPL Auto Renewal** on the left, and click **Run workflow**. A green check means it finished; a red X means something failed, so open the run to read the log.
 
## Run it on your own computer
 
1. Install Python 3 and Google Chrome.
2. Install the dependencies:
```bash
   pip install -r requirements.txt
```
 
3. Create a file named `.env` in the project folder (it is already in `.gitignore`, so it will not be committed):
```env
   BARCODE=your_library_barcode
   PASSWORD=your_library_password
   EMAIL=your_gmail_address
   SENDER_PASSWORD=your_gmail_app_password
```
 
4. Run the script:
```bash
   python library_renewal.py
```
 
On your computer the browser opens normally so you can watch it. On GitHub Actions it runs headless (no visible window) automatically.
 
## Notes and limitations

- **Name Environment Secrets:** BARCODE, PASSWORD, EMAIL, SENDER_PASSWORD if using GitHub Actions
- **Website changes can break it.** The script finds buttons and fields with fixed XPaths, so if the library redesigns its site, the XPaths in `library_renewal.py` will need updating.
- **Library renewal limits still apply.** The script can only renew books the library allows you to renew.
- **Keep your secrets private.** Never commit your `.env` file or put credentials in the code. The workflow logs deliberately do not print book titles, because logs in a public repository can be seen by anyone.
- **Scheduled runs can pause.** GitHub disables scheduled workflows after 60 days without any activity in the repository. If that happens, re-enable the workflow from the Actions tab.
