from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError
import os
from dotenv import load_dotenv

# Load environment variables for Google credentials
load_dotenv('../../.env.txt')

google_email = os.getenv("google_email")
google_password = os.getenv("google_password")

PROMISED_DOWN = 150
PROMISED_UP = 10


class InternetSpeedTwitterBot:
    def __init__(self, p):
        # Launch a persistent browser context to retain sessions and cookies.
        # This helps avoid being blocked by x.com because the context appears more like a real user.
        self.browser: Browser = p.chromium.launch_persistent_context(
            user_data_dir="/Users/nataliaraz/Library/Application Support/Google/Chrome",
            args=["--disable-infobars", "--disable-blink-features=AutomationControlled"],
            headless=False,
        )
        # Create a new page for actions. A new page is used to perform interactions, and the
        # 'navigator.webdriver' property is masked to reduce bot detection by x.com.
        self.page: Page = self.browser.new_page()
        self.page.evaluate("Object.defineProperty(navigator,'webdriver', { get: () => undefined })")

    def get_internet_speed(self):
        # Navigate to Speedtest.net to measure internet speed.
        self.page.goto('https://www.speedtest.net')

        # Attempt to click the cookie consent button "I Accept" if it appears;
        # if not, continue after a short timeout.
        try:
            self.page.click('text="I Accept"', timeout=3000)
        except TimeoutError:
            print("Cookie banner not found. Continuing...")

        # Click the "GO" button to start the speed test.
        self.page.click('text=GO')

        # Wait until the test results are active.
        self.page.wait_for_selector('.result-container-speed-active', timeout=0)

        # Retrieve download and upload speeds, converting them to float.
        download_speed = float(self.page.inner_text('.download-speed'))
        upload_speed = float(self.page.inner_text('.upload-speed'))
        print(download_speed)
        print(upload_speed)
        return download_speed, upload_speed

    def tweet_at_provider(self):
        # Get current internet speeds.
        down, up = self.get_internet_speed()
        complaint_message = (f"#100daysOfCode:\nHey internet Provider, why is my internet speed "
                             f"{down}down/{up}up\nwhen I pay for {PROMISED_DOWN}down/{PROMISED_UP}up?")

        # If either download or upload speed is below the promised value,
        # proceed with signing in and posting the complaint.
        if down < PROMISED_DOWN or up < PROMISED_UP:
            # Navigate to x.com/home (the main page for posting).
            self.page.goto('https://x.com/home')
            self.page.context.set_default_timeout(3000)

            try:
                # Locate the iframe that contains the Google Sign-In button.
                login_iframe = self.page.frame_locator('iframe[src*="accounts.google.com/gsi/button"]')

                # Wait for a new page to open upon clicking the sign-in button.
                with self.page.context.expect_page(timeout=3000) as new_page_info:
                    login_iframe.locator('div[aria-labelledby="button-label"]').click()
                new_page = new_page_info.value
                new_page.wait_for_load_state()
                print("New page was opened")

                # Check if an account is already recognized (i.e. the account list is shown).
                account_locator = new_page.locator(f'[data-identifier="{google_email}"]')
                print(account_locator.count())
                if int(account_locator.count()) > 0:
                    # If the account is recognized, simply click it to proceed.
                    self.page.context.set_default_timeout(0)
                    account_locator.click()
                else:
                    # Otherwise, perform a full login by entering email and password.
                    self.page.context.set_default_timeout(0)
                    new_page.fill('input[type="email"]', google_email)
                    new_page.click('//*[@id="identifierNext"]/div/button')
                    new_page.fill('input[type="password"]', google_password)
                    new_page.click('//*[@id="passwordNext"]/div/button')

                # Switch back to the main x.com page.
                for pg in self.page.context.pages:
                    print(pg)
                    if "x.com/home" in pg.url:
                        self.page = pg
                        break

            except TimeoutError:
                print("Already logged in. Continuing...")

            # Fill the tweet (complaint) into the text area.
            self.page.fill('.public-DraftStyleDefault-ltr', complaint_message)
            # Click "Post" button here.
            # self.page.click('button[data-testid="tweetButtonInline"]')
            print('Tweet action performed')
        else:
            print('Internet speed is acceptable')
            print(f"Current Speed: {down, up}")
            print(f"Promised Speed: {PROMISED_DOWN, PROMISED_UP}")
            self.browser.close()

        # Wait for user confirmation before closing the browser.
        def wait_for_user_confirmation():
            input("Press Enter to close the browser when finished...")

        wait_for_user_confirmation()
        self.browser.close()


if __name__ == "__main__":
    with sync_playwright() as p:
        bot = InternetSpeedTwitterBot(p)
        bot.tweet_at_provider()
