# Enhanced LANL parser with Shadow DOM cookie handling via helper function
import logging
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, JavascriptException, NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions # For console logs
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

KEYWORDS = [
    "embedded", "firmware", "autosar", "real-time", "real time", "software",
    "bare metal", "bsp", "rtos", "low level", "low-level", "device driver"
]

logger = logging.getLogger(__name__)

def get_browser_console_logs(driver):
    """Helper function to retrieve and log browser console messages."""
    try:
        log_entries = driver.get_log('browser')
        if log_entries:
            logger.info("------ Browser Console Logs ------")
            for entry in log_entries:
                # Filter for messages related to the cookie consent or errors
                if 'JS Cookie Consent:' in entry.get('message', '') or \
                   entry.get('level') == 'SEVERE' or \
                   'usercentrics' in entry.get('message','').lower() or \
                   'uc-app-container' in entry.get('message','').lower():
                    logger.info(f"Browser Log: {entry['level']} - {entry['message']}")
            logger.info("------ End Browser Console Logs ------")
        else:
            logger.info("LANL: No browser console logs found or logging not configured correctly.")
    except Exception as e:
        logger.error(f"LANL: Error fetching browser logs: {e}")

def _attempt_shadow_dom_click(driver_context):
    """
    Internal helper to attempt clicking the cookie button within a given driver context (main document).
    Returns True if successful, False otherwise.
    """
    js_script = """
    function waitForElement(root, selector, timeout = 10000, interval = 100) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            const check = () => {
                const element = root.querySelector(selector);
                if (element) {
                    resolve(element);
                } else if (Date.now() - startTime > timeout) {
                    reject(new Error(`Element ${selector} not found within timeout`));
                } else {
                    setTimeout(check, interval);
                }
            };
            check();
        });
    }

    async function clickShadowDomButton() {
        const log = (level, ...args) => console[level]('JS Cookie Consent:', ...args);
        
        try {
            log('info', 'Attempting to find and click cookie consent button...');

            // The usercentrics-root div is the host for the shadow DOM
            const usercentricsRoot = await waitForElement(document, '#usercentrics-root', 15000);
            log('info', 'Usercentrics root found:', usercentricsRoot);

            if (!usercentricsRoot.shadowRoot) {
                log('error', 'Usercentrics root shadowRoot not found.');
                return {success: false, stage: 'usercentrics_root_shadowRoot_not_found', message: 'Usercentrics root shadowRoot missing'};
            }
            log('info', 'Usercentrics root shadowRoot found.');

            // Now traverse the shadow DOM from usercentricsRoot.shadowRoot
            const container = await waitForElement(usercentricsRoot.shadowRoot, '[data-testid="uc-app-container"]', 10000);
            log('info', 'Container found:', container);
            
            // The banner and button are nested directly within the container's shadowRoot, not another shadowRoot
            const banner = await waitForElement(container, '[data-testid="uc-ccpa-banner"]', 10000);
            log('info', 'Banner found:', banner);

            const button = await waitForElement(banner, 'button[data-testid="uc-ccpa-button"]', 10000);
            log('info', 'Button found:', button);

            const rect = button.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0 || window.getComputedStyle(button).display === 'none' || window.getComputedStyle(button).visibility === 'hidden') {
                log('warn', 'Button is not visible or has zero dimensions. Width:', rect.width, 'Height:', rect.height, 'Display:', window.getComputedStyle(button).display, 'Visibility:', window.getComputedStyle(button).visibility);
                // Attempt to scroll into view even if it has dimensions
                button.scrollIntoView({ block: 'center', inline: 'center' });
                await new Promise(r => setTimeout(r, 500)); // Small pause after scroll
            }
            if (button.disabled) {
                log('warn', 'Button is disabled.');
                return {success: false, stage: 'button_disabled', message: 'Button is disabled'};
            }
            
            // Try direct click first
            log('info', 'Attempting direct button.click()');
            button.click();
            log('info', 'Direct button.click() dispatched.');
            
            // Add a small delay to allow UI to react
            await new Promise(r => setTimeout(r, 1000)); 

            // Re-check if the banner is still present. If so, try dispatchEvent as fallback.
            // Check if the usercentrics-root element (which hosts the entire banner) is still in the DOM.
            const usercentricsRootAfterClick = document.querySelector('#usercentrics-root');
            if (usercentricsRootAfterClick) {
                log('warn', 'Usercentrics root still present after direct click. Trying MouseEvent dispatch.');
                button.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                log('info', 'Cookie consent button click dispatched via MouseEvent.');
                await new Promise(r => setTimeout(r, 1000)); // Another small delay
            } else {
                log('info', 'Usercentrics root disappeared after direct click. Success!');
            }

            // Final check: if usercentrics-root is still present, it means click failed.
            if (document.querySelector('#usercentrics-root')) {
                log('error', 'Cookie banner still present after all click attempts.');
                return {success: false, stage: 'click_failed_persistent_banner', message: 'Banner persisted after click attempts'};
            }


            return {success: true, stage: 'click_attempted', message: 'Click event dispatched successfully'};

        } catch (e) {
            console.error('JS Cookie Consent: Error in shadow DOM interaction:', e.toString(), e.stack);
            return {success: false, stage: 'exception', message: e.toString()};
        }
    }
    return clickShadowDomButton(); // Execute the async function
    """
    try:
        result = driver_context.execute_script(js_script)
    except JavascriptException as e:
        logger.error(f"LANL: JavaScript exception during cookie consent interaction in current context: {e.msg}")
        return False

    if result and result.get('success'):
        logger.info(f"LANL: Cookie consent interaction successful in current context. Stage: {result.get('stage')}, Message: {result.get('message')}")
        return True
    else:
        logger.warning(f"LANL: Failed to click cookie consent in current context. Result: {result}")
        return False


def accept_cookie_shadow_popup(driver):
    """
    Attempts to find and click the "OK" button in the Shadow DOM cookie banner.
    Includes enhanced debugging: console log capture and screenshot on failure.
    This function now focuses only on the main document's Shadow DOM.
    """
    screenshot_path = "cookie_banner_not_found.png"
    
    # First, wait for a stable element on the main page to ensure it's loaded
    logger.info("LANL: Waiting for main page content to load before checking for cookie banner.")
    try:
        # Wait for the search input field using its placeholder, which is a reliable indicator of page readiness
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Keyword / Req. Number"]'))
        )
        logger.info("LANL: Main page content (keyword input field) is present.")
    except TimeoutException:
        logger.warning("LANL: Main page content (keyword input field) not found within timeout. Cookie banner might not appear or page is not fully loaded.")
        get_browser_console_logs(driver)
        driver.save_screenshot(screenshot_path)
        logger.info(f"LANL: Screenshot saved to {os.path.abspath(screenshot_path)}")
        return False # Cannot proceed if main page isn't ready

    # Now, attempt to accept cookie consent directly in the main document context,
    # as the cookie banner is confirmed to be in the main DOM's Shadow DOM.
    logger.info("LANL: Attempting to accept cookie consent in main document context (Shadow DOM).")
    if _attempt_shadow_dom_click(driver):
        logger.info("LANL: Cookie consent handled in main document.")
        time.sleep(2) # Give some time for the banner to fully disappear
        get_browser_console_logs(driver)
        return True
    else:
        logger.warning("LANL: Failed to accept cookie banner in main document Shadow DOM.")
        try:
            driver.save_screenshot(screenshot_path)
            logger.info(f"LANL: Screenshot saved to {os.path.abspath(screenshot_path)}")
        except Exception as e:
            logger.error(f"LANL: Failed to save screenshot: {e}")
        get_browser_console_logs(driver)
        return False


def fetch_jobs():
    jobs = []
    all_titles = []
    
    chrome_options = ChromeOptions()
    # Enable browser logging
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'}) 
    # Optional: Run headless - uncomment for server environments
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--disable-gpu") # Often needed for headless
    # chrome_options.add_argument("--no-sandbox") # If running as root (e.g. in Docker)
    # chrome_options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems

    # To ensure Usercentrics script loads, try mimicking a common user agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')


    driver = webdriver.Chrome(options=chrome_options)

    try:
        logger.info("LANL: Navigating to job search page.")
        driver.get("https://lanl.jobs/search/searchjobs")
        
        # It's good practice to maximize window, sometimes elements behave differently
        driver.maximize_window()
        time.sleep(1) # Brief pause after page load and maximize

        logger.info("LANL: Attempting to accept cookie consent.")
        if not accept_cookie_shadow_popup(driver):
            logger.warning("LANL: Failed to accept cookie banner. Scraping might be affected or impossible.")
            # At this point, a screenshot and console logs should have been captured by accept_cookie_shadow_popup
        else:
            logger.info("LANL: Cookie consent handled (or was not present/already accepted).")

        # Even if cookie consent failed, try to proceed to see if scraping is possible or if other errors occur.
        # Depending on strictness, you might want to `return []` here if cookie consent is mandatory.

        logger.info("LANL: Starting to click 'Load more jobs'.")
        max_clicks = 50
        for i in range(max_clicks):
            try:
                load_more_button_locator = (By.CSS_SELECTOR, "span.jtable-page-number-next.ui-button.ui-state-default:not(.ui-state-disabled)")
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(load_more_button_locator) 
                )
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(load_more_button_locator)
                )
                
                # Scroll into view before clicking, can help with stubborn elements
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(0.5) # Pause for scroll to complete

                ActionChains(driver).move_to_element(load_more_button).click().perform()
                logger.info(f"LANL: Clicked 'Load more jobs' ({i + 1}/{max_clicks})")
                time.sleep(2) # Increased wait for jobs to load after click
            except TimeoutException:
                logger.info("LANL: 'Load more jobs' button not found or not clickable (possibly all jobs loaded or button disabled).")
                break
            except Exception as e:
                logger.warning(f"LANL: Error clicking 'Load more jobs' (iteration {i+1}): {e}")
                # Get console logs if 'load more' fails unexpectedly
                get_browser_console_logs(driver)
                break 
        
        logger.info("LANL: Finished clicking 'Load more'. Parsing page content.")
        # It's good to get final console logs before parsing, in case of JS errors during job loading
        get_browser_console_logs(driver)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("tr.jtable-data-row")
        logger.info(f"LANL: Found {len(rows)} job rows in the table.")

        for row_idx, row in enumerate(rows):
            try:
                title_span = row.select_one("td.title-column span")
                title = title_span.get_text(strip=True) if title_span else None
                
                url_relative = row.get("data-href")
                url = None
                if url_relative:
                    if url_relative.startswith('/'):
                        url = f"https://lanl.jobs{url_relative}"
                    elif not url_relative.startswith('http'):
                         url = f"https://lanl.jobs/{url_relative}"
                    else:
                        url = url_relative

                if not title or not url:
                    logger.warning(f"LANL: Skipping row {row_idx+1} due to missing title or URL. Title: '{title}', URL: '{url}'")
                    continue

                all_titles.append(title)

                if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                    jobs.append({"title": title, "url": url})
                    logger.info(f"LANL: Match found -> {title} | URL: {url}")

            except Exception as e:
                logger.warning(f"LANL: Skipping row {row_idx+1} due to error processing job data: {e}")
        
        logger.info(f"LANL: Found {len(jobs)} relevant jobs out of {len(all_titles)} total titles.")

    except Exception as e:
        logger.error(f"LANL: An error occurred during the fetch_jobs process: {e}", exc_info=True)
        # Get console logs on any major exception in fetch_jobs
        if 'driver' in locals() and driver:
            get_browser_console_logs(driver)
            try:
                driver.save_screenshot("error_in_fetch_jobs.png")
                logger.info(f"LANL: Screenshot saved to {os.path.abspath('error_in_fetch_jobs.png')}")
            except Exception as se:
                logger.error(f"LANL: Failed to save screenshot during error handling: {se}")


    finally:
        logger.info("LANL: Closing WebDriver.")
        if 'driver' in locals() and driver:
            driver.quit()
        
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        all_titles_path = os.path.join(output_dir, "job_titles_lanl.txt")
        with open(all_titles_path, "w", encoding="utf-8") as f:
            for title in all_titles:
                f.write(title + "\n")
        logger.info(f"LANL: All job titles saved to {all_titles_path}")

        results_path = os.path.join(output_dir, "job_results_lanl.txt")
        with open(results_path, "w", encoding="utf-8") as f:
            for job in jobs:
                f.write(f"{job['title']} -> {job['url']}\n")
        logger.info(f"LANL: Filtered job results saved to {results_path}")

    return jobs

if __name__ == '__main__':
    logger.info("Starting LANL job fetcher...")
    fetched_jobs = fetch_jobs()
    if fetched_jobs: # Check if list is not empty
        logger.info(f"Successfully fetched {len(fetched_jobs)} jobs.")
    elif fetched_jobs == []: # Explicitly check for empty list (successful run, no matches)
        logger.info("LANL job fetcher ran successfully but found 0 relevant jobs or 0 total jobs.")
    else: # None or other Falsey value, indicating an issue
        logger.warning("LANL job fetcher did not return a valid job list, likely encountered an issue.")
