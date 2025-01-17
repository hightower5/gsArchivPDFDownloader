import logging

from selenium import webdriver
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains

import os
import json
from time import sleep, time


def download_edition(jahr_start, ausgaben_start, jahr_end, ausgaben_end,
                     filestring_download, filestring_target):
    wait_de = WebDriverWait(driver, 10)

    for jahr in range(jahr_start, jahr_end+1):
        for ausgabe in range(ausgaben_start, ausgaben_end+1):
            filenamepattern_4target = filestring_target
            filenamepattern_4download = filestring_download

            if user_data[0]['edition2d'].lower() == 'yes':
                for filenamerepl in (("<ausgabe>", f"{ausgabe:02d}"), ("<jahr>", str(jahr))):
                    filenamepattern_4target = filenamepattern_4target.replace(*filenamerepl)

            else:
                for filenamerepl in (("<ausgabe>", str(ausgabe)), ("<jahr>", str(jahr))):
                    filenamepattern_4target = filenamepattern_4target.replace(*filenamerepl)


            for filenamerepl in (("<ausgabe>", str(ausgabe)), ("<jahr>", str(jahr))):
                filenamepattern_4download = filenamepattern_4download.replace(*filenamerepl)

            filenamepattern_download = filenamepattern_4download
            filenamepattern_local = filenamepattern_4target

            logging.debug(f'Filepattern(from server)     :[{filenamepattern_download}]')
            logging.debug(f'Filepattern(local for target):[{filenamepattern_local}]')

            if jahr == 2017 and ausgabe == 10 and user_data[0]['skip20yearedition'].lower() == "yes":
                logging.info(f"Skip download - this is the current (by 11 March 2021) faulty download link of "
                             f"'{user_data[0]['downloadtarget']}/{jahr}/{filenamepattern_local}'")
                continue

            if os.path.exists(f"{user_data[0]['downloadtarget']}/{jahr}/{filenamepattern_local}"):
                logging.info(f"Skip download - already existing "
                             f"'{user_data[0]['downloadtarget']}/{jahr}/{filenamepattern_local}'")
                continue

            try:
                if os.path.exists(f"{user_data[0]['downloadtarget']}/{filenamepattern_download}"):
                    os.remove(f"{user_data[0]['downloadtarget']}/{filenamepattern_download}")
                sleep(5)
                logging.info(f'Try now download of : Jahr {jahr} and Ausgabe {ausgabe}')
                driver.get(f'https://www.gamestar.de/_misc/plus/showbk.cfm?bky={jahr}&bkm={ausgabe}')
                sleep(5)
                save_button = wait_de.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="top_menu_save"]')))
                ActionChains(driver).move_to_element(save_button).click().perform()
                wait_de.until(ec.visibility_of_element_located((By.XPATH, '//p[@class="title"]')))

                wait_de.until(ec.visibility_of_element_located((By.XPATH, "//a[contains(@href, 'complete.pdf')]")))
                driver.find_element_by_xpath("//a[contains(@href, 'complete.pdf')]").click()
                sleep(1)
                result = wait_for_download(f"{user_data[0]['downloadtarget']}/{filenamepattern_download}",
                                           timeout=user_data[0]['downloadtimeout'])
                if result is True:
                    if not os.path.exists(f"{user_data[0]['downloadtarget']}/{jahr}"):
                        os.mkdir(f"{user_data[0]['downloadtarget']}/{jahr}")
                    # Give it time to sync to disk - not clear
                    sleep(2)
                    os.rename(f"{user_data[0]['downloadtarget']}/{filenamepattern_download}",
                              f"{user_data[0]['downloadtarget']}/{jahr}/{filenamepattern_local}")
                else:
                    logging.warning('Download not yet completed - not possible to move by now')
            except Exception as e:
                logging.exception(f'Exception:{e}')


def wait_for_download(filedownloadfullpath, timeout=30):
    logging.debug(f'Download timeout is:[{timeout}]')
    time_out = time() + 2
    while not os.path.exists(f'{filedownloadfullpath}.part') and time() < time_out:
        logging.debug(f'{filedownloadfullpath}.part not yet seen- waiting for first download')

        sleep(2)
    time_out = time() + timeout
    while os.path.exists(f'{filedownloadfullpath}.part') and time() < time_out:
        logging.debug(f'{filedownloadfullpath}.part Seen- waiting')
        sleep(1.5)
    if os.path.exists(f'{filedownloadfullpath}.part'):
        logging.warning('Download still in progress - may need recheck - aborting wait to continue'
                        ' - may complete in background')
        return False
    else:
        logging.info('Download done successful')
        return True


logging.basicConfig(format='%(asctime)s:[%(levelname)-5.5s]  %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S %p', level=logging.INFO)
# filename='gsArchivPDFDownloader.log'

# Daten aus dem JSON File laden
with open('gs.json', 'r') as file:
    user_data = json.loads(file.read())

logging.info(f"Download location:{user_data[0]['downloadtarget']}")
logging.info(f"filenamepattern_fromserver:{user_data[0]['filenamepattern_fromserver']}")
logging.info(f"filenamepattern_intarget  :{user_data[0]['filenamepattern_intarget']}")

if not os.path.exists(f"{user_data[0]['downloadtarget']}"):
    os.makedirs(f"{user_data[0]['downloadtarget']}")

profile: FirefoxProfile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.folderList', 2)
profile.set_preference('browser.helperApps.alwaysAsk.force', False)
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir', f"{user_data[0]['downloadtarget']}")

profile.set_preference('plugin.disable_full_page_plugin_for_types', 'application/pdf')
profile.set_preference('pdfjs.disabled', True)
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/pdf')
driver = webdriver.Firefox(firefox_profile=profile)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

url = 'https://www.gamestar.de/plus/'
wait = WebDriverWait(driver, 20)

# open browser and login
driver.get(url)
logging.info(f"Browser now started with URL:{url} - "
             f"try now to log in with user/password [{user_data[0]['user']}/******]")

wait.until(ec.visibility_of_element_located((By.LINK_TEXT, 'einloggen')))
driver.find_element_by_link_text('einloggen').click()
wait.until(ec.visibility_of_element_located((By.ID, 'loginbox-login-username')))
driver.find_element_by_id('loginbox-login-username').send_keys(user_data[0]['user'])
driver.find_element_by_id('loginbox-login-password').send_keys(user_data[0]['password'])
driver.find_element_by_css_selector('button.btn:nth-child(9)').click()


year_start = 1997
year_end = 1997
edition_start = 9
edition_end = 12
download_edition(year_start, edition_start, year_end, edition_end, user_data[0]['filenamepattern_fromserver'],
                 user_data[0]['filenamepattern_intarget'])

year_start = 1998
year_end = 2013
edition_start = 1
edition_end = 12
download_edition(year_start, edition_start, year_end, edition_end, user_data[0]['filenamepattern_fromserver'],
                 user_data[0]['filenamepattern_intarget'])

year_start = 2013
year_end = 2013
edition_start = 13
edition_end = 13
download_edition(year_start, edition_start, year_end, edition_end, user_data[0]['filenamepattern_fromserver'],
                 user_data[0]['filenamepattern_intarget'])

year_start = 2014
year_end = 2020
edition_start = 1
edition_end = 12
download_edition(year_start, edition_start, year_end, edition_end, user_data[0]['filenamepattern_fromserver'],
                 user_data[0]['filenamepattern_intarget'])

year_start = 2021
year_end = 2021
edition_start = 1
edition_end = 3
download_edition(year_start, edition_start, year_end, edition_end, user_data[0]['filenamepattern_fromserver']
                 ,user_data[0]['filenamepattern_intarget'])

logging.info(f"Last requested editon downloaded - give job some time (30s) to finish, for no good reason...")
sleep(30)
driver.quit()
logging.info('Job done')
