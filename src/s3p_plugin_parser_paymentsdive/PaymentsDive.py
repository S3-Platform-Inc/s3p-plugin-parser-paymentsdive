import datetime
import time

from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument, S3PPlugin
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import pytz
import dateparser


class PaymentsDive(S3PParserBase):
    """
    A Parser payload that uses S3P Parser base class.
    """
    HOST = "https://www.paymentsdive.com/?page=2"
    utc = pytz.UTC

    def __init__(self, refer: S3PRefer, plugin: S3PPlugin, web_driver: WebDriver, max_count_documents: int = None,
                 last_document: S3PDocument = None):
        super().__init__(refer, plugin, max_count_documents, last_document)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -

        self._driver.get(self.HOST)  # Открыть страницу с материалами
        self._wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.dash-feed')))

        # Окно с куками пропадает самостоятельно через 2-3 секунды
        # try:
        #    cookies_btn = self._driver.find_element(By.CLASS_NAME, 'ui-button').find_element(By.XPATH,
        #                                                                                    '//*[text() = \'Accept\']')
        #    self._driver.execute_script('arguments[0].click()', cookies_btn)
        #    self.logger.info('Cookies убран')
        # except:
        #    self.logger.exception('Не найден cookies')
        #    pass

        # self.logger.info('Прекращен поиск Cookies')
        time.sleep(3)

        while True:

            # self.logger.debug('Загрузка списка элементов...')

            doc_table = self._driver.find_element(By.CLASS_NAME, 'dash-feed').find_elements(By.XPATH,
                                                                                            '//*[contains(@class,\'row feed__item\')]')
            # self.logger.debug('Обработка списка элементов...')

            # Цикл по всем строкам таблицы элементов на текущей странице
            # self.logger.info(f'len(doc_table) = {len(doc_table)}')
            # print(doc_table)
            # for element in doc_table:
            #     print(element.text)
            #     print('*'*45)

            for i, element in enumerate(doc_table):
                # continue
                # print(i)
                # print(element)
                # print(doc_table[i])
                if 'feed-item-ad' in doc_table[i].get_attribute('class'):
                    # print(doc_table[i].get_attribute('class'))
                    # print(doc_table[i].text)
                    continue

                element_locked = False

                try:
                    title = doc_table[i].find_element(By.XPATH, './/*[contains(@class,\'feed__title\')]').text
                    # print(title)
                    # title = element.find_element(By.XPATH, '//*[@id="feed-item-title-1"]/a').text

                except:
                    # self.logger.exception('Не удалось извлечь title')
                    title = ' '

                # try:
                #     other_data = element.find_element(By.CLASS_NAME, "secondary-label").text
                # except:
                #     self.logger.exception('Не удалось извлечь other_data')
                #     other_data = ''
                # // *[ @ id = "main-content"] / ul / li[1] / div[2] / span[2]
                # // *[ @ id = "main-content"] / ul / li[2] / div[2] / span[2]
                other_data = None

                # try:
                #    date = dateparser.parse(date_text)
                # except:
                #    self.logger.exception('Не удалось извлечь date')
                #    date = None

                try:
                    abstract = doc_table[i].find_element(By.CLASS_NAME, 'feed__description').text
                except:
                    # self.logger.exception('Не удалось извлечь abstract')
                    abstract = None

                book = ' '

                try:
                    web_link = doc_table[i].find_element(By.XPATH,
                                                         './/*[contains(@class,\'feed__title\')]').find_element(
                        By.TAG_NAME, 'a').get_attribute('href')
                except:
                    # self.logger.exception('Не удалось извлечь web_link, пропущен')
                    web_link = None
                    continue
                    # web_link = None

                self._driver.execute_script("window.open('');")
                self._driver.switch_to.window(self._driver.window_handles[1])
                self._driver.get(web_link)
                time.sleep(5)
                # self._wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.print-wrapper')))

                try:
                    pub_date = self.utc.localize(
                        dateparser.parse(
                            ' '.join(self._driver.find_element(By.CLASS_NAME, 'published-info').text.split()[1:])))
                except:
                    # self.logger.exception('Не удалось извлечь pub_date')
                    pub_date = None

                try:
                    text_content = self._driver.find_element(By.XPATH,
                                                             '//div[contains(@class, \'large medium article-body\')]').text
                except:
                    # self.logger.exception('Не удалось извлечь text_content')
                    text_content = None

                doc = S3PDocument(None,
                                  title,
                                  abstract,
                                  text_content,
                                  web_link,
                                  None,
                                  other_data,
                                  pub_date,
                                  datetime.datetime.now())

                self._find(doc)

                self._driver.close()
                self._driver.switch_to.window(self._driver.window_handles[0])
            try:
                pagination_arrow = self._driver.find_element(By.XPATH, '//div[contains(@class,\'pagination\')]/a[2]')
                pg_num = pagination_arrow.get_attribute('href')
                self._driver.execute_script('arguments[0].click()', pagination_arrow)
                time.sleep(3)
                # self.logger.info(f'Выполнен переход на след. страницу: {pg_num}')
                print('=' * 90)

                # if int(pg_num[-1]) > 5:
                #     # self.logger.info('Выполнен переход на 6-ую страницу. Принудительное завершение парсинга.')
                #     break

            except:
                # self.logger.exception('Не удалось найти переход на след. страницу. Прерывание цикла обработки')
                break

        # ---
        # ========================================
        ...
