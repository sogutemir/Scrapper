import concurrent.futures

import customtkinter
import random
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

import requests.exceptions
from requests_html import AsyncHTMLSession, HTMLSession

customtkinter.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    WIDTH = 900
    HEIGHT = 550
    MIN_WIDTH = WIDTH
    MIN_HEIGHT = HEIGHT
    HEADER_NAME = "URL Scraper"

    def __init__(self):
        super().__init__()
        self.create_window()

    def create_window(self):
        self.visited_urls = []
        self.target_urls = []
        self.fetched_urls = []
        self.max_url = 1000

        # configure windows
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.title(self.HEADER_NAME)
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # configure grid layout
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        # Sidebar Frame
        self.sidebar_frame = customtkinter.CTkFrame(self, width=int(self.WIDTH / 4))
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.sidebar_label = customtkinter.CTkLabel(self.sidebar_frame, font=customtkinter.CTkFont(size=14),
                                                    text="Options")
        self.sidebar_label.grid(row=0, column=0, padx=20, pady=5)

        self.sidebar_proxy_checkbox = customtkinter.CTkCheckBox(self.sidebar_frame, text="Proxy", command=self.create_session)
        self.sidebar_proxy_checkbox.grid(row=1, column=0, padx=20, pady=15)

        self.sidebar_multithread_checkbox = customtkinter.CTkCheckBox(self.sidebar_frame, text="Multi Thread")
        self.sidebar_multithread_checkbox.grid(row=2, column=0, padx=20, pady=15)

        self.sidebar_only_absolute_path = customtkinter.CTkCheckBox(self.sidebar_frame, text="Absolute Path")
        self.sidebar_only_absolute_path.grid(row=3, column=0, padx=20, pady=15)

        self.sidebar_url_limit_input = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Url Limit")
        self.sidebar_url_limit_input.grid(row=4, column=0, padx=20, pady=15)

        self.sidebar_error = customtkinter.CTkLabel(self.sidebar_frame, text="", text_color="red", wraplength=120)
        self.sidebar_error.grid(row=5, column=0, padx=20, pady=15)

        # Main Frame
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, rowspan=4, sticky="nwsew")

        self.url_input_var = customtkinter.StringVar()
        self.url_input = customtkinter.CTkEntry(self.main_frame, placeholder_text="Url", width=self.WIDTH - self.WIDTH / 4 - 100, textvariable=self.url_input_var)
        self.url_input_var.trace("w", lambda name, index, mode, url_var=self.url_input_var: self.url_input_handler())
        self.url_input.grid(row=0, column=0, padx=10, pady=10)

        self.button = customtkinter.CTkButton(self.main_frame, text="Scrape", width=125, command=self.fetch_urls)
        self.button.grid(row=0, column=1, padx=10, pady=10)

        self.textbox = customtkinter.CTkTextbox(self.main_frame, width=self.WIDTH - self.WIDTH / 4 - 100,
                                                height=self.HEIGHT - 75)
        self.textbox.grid(row=1, column=0, padx=10, pady=10)

        # info frame
        self.info_frame = customtkinter.CTkFrame(self.main_frame)
        self.info_frame.grid(row=1, column=1)

        self.fethed_count_label = customtkinter.CTkLabel(self.info_frame, text="Fetched: 0 link")
        self.fethed_count_label.grid(row=0, column=0, padx=10, pady=10)

        self.button_save = customtkinter.CTkButton(self.info_frame, text="Save", width=125, command=self.save_urls)
        self.button_save.grid(row=2, column=0, padx=10, pady=10)

        self.button_clear = customtkinter.CTkButton(self.info_frame, text="Clear", width=125,
                                                    command=self.clear_textbox)
        self.button_clear.grid(row=3, column=0, padx=10, pady=10)

    def save_urls(self):
        with open("outputs/output.txt", "w+") as file:
            file.write(self.textbox.get("0.0", "end"))

    def clear_textbox(self):
        self.fethed_count_label.configure(text="Fetched: 0 link")
        self.textbox.delete("0.0", "end")
        self.visited_urls = []

    def url_input_handler(self):
        self.sidebar_error.configure(text="")

    def create_session(self):
        if (self.sidebar_proxy_checkbox.get()):
            proxies = {
                "http": self.get_proxy(),
                "https": self.get_proxy(),
            }
            session = AsyncHTMLSession()
            session.proxies.update(proxies)
            return session
        else:
            return HTMLSession()

    def get_proxy(self):
        with open("./inputs/proxies.txt") as file:
            try:
                return random.choice(file.readlines())
            except IndexError as ex:
                self.sidebar_error.configure(text="Empty proxy list")

    def fetch_urls_sync(self, urls=[]):
        self.target_urls = []
        if len(urls) > 0 and len(self.fetched_urls) <= self.max_url:
            url_absolute_path = urlparse(self.url_input.get()).scheme + "://" + urlparse(self.url_input.get()).netloc
            url_path = urlparse(self.url_input.get()).netloc
            session = self.create_session()
            for url in urls:
                try:
                    if url not in self.visited_urls:
                        response = session.get(url)
                        self.visited_urls.append(url)
                        links = response.html.absolute_links
                        links = [link for link in links if "https" in link or "http" in link]
                        if self.sidebar_only_absolute_path.get():
                            links = [link for link in links if url_path in link]
                        for link in links:
                            if link not in self.fetched_urls:
                                self.fetched_urls.append(link)
                        for link in links:
                            if url_path in link:
                                self.target_urls.append(link)
                except Exception as ex:
                    pass
            print(self.target_urls)
            self.fetch_urls_sync(self.target_urls)


    def fetch_urls_multi_thread(self, urls=[]):
        self.target_urls = []
        if len(urls) > 0 and len(self.fetched_urls) <= self.max_url:
            sessions = self.create_session()
            url_absolute_path = urlparse(self.url_input.get()).scheme + "://" + urlparse(self.url_input.get()).netloc
            url_path = urlparse(self.url_input.get()).netloc

            with ThreadPoolExecutor(max_workers=len(urls)) as executor:
                results = [executor.submit(sessions.post, url) for url in urls]
                concurrent.futures.wait(results)
                for result in results:
                    result = result.result()
                    self.visited_urls.append(result.url)
                    try:
                        links = result.html.absolute_links
                        links = [link for link in links if "https" in link or "http" in link]
                    except:
                        pass
                    if self.sidebar_only_absolute_path.get():
                        links = [link for link in links if url_path in link]
                    for link in links:
                        if link not in self.fetched_urls:
                            self.fetched_urls.append(link)
                    for link in links:
                        if url_path in link:
                            self.target_urls.append(link)
            print(self.target_urls)
            self.fetch_urls_multi_thread(self.target_urls)


    def fetch_urls(self):
        try:
            self.fetched_urls = []
            self.target_urls = []
            self.visited_urls = []
            try:
                self.max_url = 1000 if int(self.sidebar_url_limit_input.get()) > 0 else int(
                    self.sidebar_url_limit_input.get())
            except:
                self.max_url = 1000

            if self.sidebar_multithread_checkbox.get():
                self.fetch_urls_multi_thread(urls=[self.url_input.get()])
            else:
                self.fetch_urls_sync(urls=[self.url_input.get()])

            for link in self.fetched_urls:
                self.textbox.insert("0.0", link + "\n")
            self.fethed_count_label.configure(text=f"Fetched: {str(len(self.fetched_urls))} link")

        except requests.exceptions.MissingSchema as ex:
            self.sidebar_error.configure(text=ex)
        except requests.exceptions.ConnectionError as ex:
            self.sidebar_error.configure(text=f"Connection Error {ex}")
        except requests.exceptions.ProxyError as ex:
            self.sidebar_error.configure(text=f"Proxy Error : {ex}")
        except Exception as ex:
            print(ex)
            self.sidebar_error.configure(text=f"System Error")


if __name__ == "__main__":
    app = App()
    app.mainloop()
