import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import threading
import os
import sys
import json
import base58
import time

class TaskWindow(tk.Toplevel):
    def __init__(self, master, task_id):
        super().__init__(master)
        self.title(f"Grind Task #{task_id}")
        self.geometry("1200x800")
        self.minsize(800, 600)
        self.resizable(True, True)

        # Initialize variables specific to this task
        self.prefix_var = tk.StringVar()
        self.suffix_var = tk.StringVar()
        self.count_var = tk.StringVar(value="1")
        self.ignore_case_var = tk.BooleanVar()
        self.use_mnemonic_var = tk.BooleanVar()
        self.no_bip39_passphrase_var = tk.BooleanVar()
        self.word_count_var = tk.StringVar(value="12")
        self.language_var = tk.StringVar(value="english")
        self.threads_var = tk.StringVar(value="10")

        self.process = None  # To track the subprocess
        self.existing_wallet_files = set()  # To track existing JSON files before grinding

        self.available_languages = [
            "english", "chinese-simplified", "chinese-traditional",
            "japanese", "spanish", "korean", "french", "italian"
        ]

        self.is_closing = False  # Flag to indicate window is closing

        self.build_gui(task_id)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_gui(self, task_id):
        """Construct the GUI layout for the task window."""
        pad_x = 10
        pad_y = 5

        # Configure grid weights for responsiveness
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)
        self.columnconfigure(5, weight=1)
        self.rowconfigure(5, weight=1)  # Console Output
        self.rowconfigure(7, weight=1)  # Wallets Treeview

        # -------------- Row 0: Patterns --------------
        tk.Label(self, text="Prefix:", font=("Arial", 12)).grid(row=0, column=0, sticky=tk.W, padx=pad_x, pady=pad_y)
        tk.Entry(self, textvariable=self.prefix_var, width=20, font=("Arial", 12)).grid(row=0, column=1, sticky=tk.W, padx=pad_x, pady=pad_y)

        tk.Label(self, text="Suffix:", font=("Arial", 12)).grid(row=0, column=2, sticky=tk.W, padx=pad_x, pady=pad_y)
        tk.Entry(self, textvariable=self.suffix_var, width=20, font=("Arial", 12)).grid(row=0, column=3, sticky=tk.W, padx=pad_x, pady=pad_y)

        tk.Label(self, text="Count:", font=("Arial", 12)).grid(row=0, column=4, sticky=tk.W, padx=pad_x, pady=pad_y)
        tk.Entry(self, textvariable=self.count_var, width=5, font=("Arial", 12)).grid(row=0, column=5, sticky=tk.W, padx=pad_x, pady=pad_y)

        # -------------- Row 1: Threads -------------
        tk.Label(self, text="Threads:", font=("Arial", 12)).grid(row=1, column=0, sticky=tk.W, padx=pad_x, pady=pad_y)
        tk.Entry(self, textvariable=self.threads_var, width=5, font=("Arial", 12)).grid(row=1, column=1, sticky=tk.W, padx=pad_x, pady=pad_y)
        tk.Label(self, text="(Use multiple cores to speed up)", font=("Arial", 10)).grid(row=1, column=2, columnspan=4, sticky=tk.W, padx=pad_x, pady=pad_y)

        # -------------- Row 2: Advanced Options ---
        advanced_frame = tk.LabelFrame(self, text="Advanced Options", padx=10, pady=10, font=("Arial", 12, "bold"))
        advanced_frame.grid(row=2, column=0, columnspan=6, padx=pad_x, pady=pad_y, sticky=tk.W+tk.E)
        advanced_frame.columnconfigure(1, weight=1)
        advanced_frame.columnconfigure(3, weight=1)

        # Ignore Case
        self.ignore_case_var.set(False)
        ignore_case_check = tk.Checkbutton(
            advanced_frame, 
            text="Ignore Case", 
            variable=self.ignore_case_var,
            font=("Arial", 12)
        )
        ignore_case_check.grid(row=0, column=0, sticky=tk.W, padx=pad_x, pady=pad_y)

        # Use Mnemonic
        use_mnemonic_check = tk.Checkbutton(
            advanced_frame, 
            text="Use Mnemonic", 
            variable=self.use_mnemonic_var,
            command=self.toggle_mnemonic_options,
            font=("Arial", 12)
        )
        use_mnemonic_check.grid(row=0, column=1, sticky=tk.W, padx=pad_x, pady=pad_y)

        # No BIP39 Passphrase (only if Use Mnemonic is checked)
        no_bip39_passphrase_check = tk.Checkbutton(
            advanced_frame, 
            text="No BIP39 Passphrase", 
            variable=self.no_bip39_passphrase_var,
            font=("Arial", 12)
        )
        no_bip39_passphrase_check.grid(row=1, column=0, sticky=tk.W, padx=pad_x, pady=pad_y)

        # Word Count (only if Use Mnemonic is checked)
        tk.Label(advanced_frame, text="Word Count:", font=("Arial", 12)).grid(row=2, column=0, sticky=tk.W, padx=pad_x, pady=pad_y)
        self.word_count_menu = tk.OptionMenu(advanced_frame, self.word_count_var, "12", "24")
        self.word_count_menu.config(width=10, font=("Arial", 12))
        self.word_count_menu.grid(row=2, column=1, sticky=tk.W, padx=pad_x, pady=pad_y)

        # Language (only if Use Mnemonic is checked)
        tk.Label(advanced_frame, text="Language:", font=("Arial", 12)).grid(row=2, column=2, sticky=tk.W, padx=pad_x, pady=pad_y)
        self.language_menu = tk.OptionMenu(advanced_frame, self.language_var, *self.available_languages)
        self.language_menu.config(width=15, font=("Arial", 12))
        self.language_menu.grid(row=2, column=3, sticky=tk.W, padx=pad_x, pady=pad_y)

        # Initially disable mnemonic-related options
        self.toggle_mnemonic_options()

        # -------------- Row 3: Start Button ----------
        self.start_button = tk.Button(
            self, 
            text="Start Grind", 
            command=self.start_grind, 
            bg="green", 
            fg="green",
            font=("Arial", 14, "bold"),
            width=20
        )
        self.start_button.grid(row=3, column=0, columnspan=6, pady=20)

        # -------------- Row 4: Progress Bar ---------
        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=6, padx=pad_x, pady=pad_y, sticky=tk.EW)
        self.progress.grid_remove()  # Hide initially

        # -------------- Row 5: Console Output ------
        console_output_label = tk.Label(self, text="Console Output:", font=("Arial", 12, "bold"))
        console_output_label.grid(row=5, column=0, sticky=tk.W, padx=pad_x, pady=(0, pad_y))

        self.console_output_text = tk.Text(self, wrap=tk.WORD, font=("Courier", 10))
        self.console_output_text.grid(row=6, column=0, columnspan=6, padx=pad_x, pady=pad_y, sticky=tk.NSEW)
        self.console_output_text.config(state=tk.DISABLED)  # Set to DISABLED initially

        console_scrollbar = tk.Scrollbar(self, command=self.console_output_text.yview)
        console_scrollbar.grid(row=6, column=6, sticky='nsew')
        self.console_output_text['yscrollcommand'] = console_scrollbar.set

        # -------------- Row 7: Generated Wallets ------
        generated_wallets_label = tk.Label(self, text="Generated Wallets:", font=("Arial", 12, "bold"))
        generated_wallets_label.grid(row=7, column=0, sticky=tk.W, padx=pad_x, pady=(10, pad_y))

        # Create Treeview
        self.wallets_tree = ttk.Treeview(self, columns=("Address", "Private Key"), show='headings', height=10)
        self.wallets_tree.heading("Address", text="Wallet Address")
        self.wallets_tree.heading("Private Key", text="Private Key")
        self.wallets_tree.column("Address", width=500, anchor='w')
        self.wallets_tree.column("Private Key", width=500, anchor='w')
        self.wallets_tree.grid(row=8, column=0, columnspan=6, padx=pad_x, pady=pad_y, sticky=tk.NSEW)

        # Add scrollbar to Treeview
        tree_scrollbar = tk.Scrollbar(self, command=self.wallets_tree.yview)
        tree_scrollbar.grid(row=8, column=6, sticky='nsew')
        self.wallets_tree['yscrollcommand'] = tree_scrollbar.set

    def toggle_mnemonic_options(self):
        """Enable or disable mnemonic-related options based on the 'Use Mnemonic' checkbox."""
        state = tk.NORMAL if self.use_mnemonic_var.get() else tk.DISABLED
        self.word_count_menu.config(state=state)
        self.language_menu.config(state=state)
        # Enable or disable checkbuttons
        for widget in self.winfo_children():
            if isinstance(widget, tk.LabelFrame) and widget['text'] == "Advanced Options":
                for child in widget.winfo_children():
                    if isinstance(child, tk.Checkbutton) and child.cget("text") in ["No BIP39 Passphrase"]:
                        child.config(state=state)
        # If not using mnemonic, reset related options
        if not self.use_mnemonic_var.get():
            self.no_bip39_passphrase_var.set(False)

    def start_grind(self):
        """Handle the Start/Stop Grind button click."""
        if self.process is None:
            # Start grinding
            self.start_grind_process()
        else:
            # Stop grinding
            self.stop_grind_process()

    def start_grind_process(self):
        """Start the grinding process."""
        # Gather user inputs
        prefix = self.prefix_var.get().strip()
        suffix = self.suffix_var.get().strip()
        count = self.count_var.get().strip()
        ignore_case = self.ignore_case_var.get()
        use_mnemonic = self.use_mnemonic_var.get()
        no_bip39_passphrase = self.no_bip39_passphrase_var.get()
        word_count = self.word_count_var.get().strip()
        language = self.language_var.get()
        num_threads = self.threads_var.get().strip()

        # Validate inputs
        if not prefix and not suffix:
            messagebox.showerror("Input Error", "Please enter at least a prefix or suffix.")
            return

        if use_mnemonic:
            if word_count not in ['12', '24']:
                messagebox.showerror("Input Error", "Word count must be either 12 or 24.")
                return

        # Capture existing wallet files
        wallets_dir = 'wallets'
        if not os.path.exists(wallets_dir):
            try:
                os.makedirs(wallets_dir)
            except Exception as e:
                messagebox.showerror("Directory Error", f"Failed to create 'wallets' directory: {e}")
                return
        self.existing_wallet_files = set(f for f in os.listdir(wallets_dir) if f.endswith('.json'))

        # Build the base command
        command = ["solana-keygen", "grind"]

        # Determine which grind option to use
        if prefix and suffix:
            grind_option = f"--starts-and-ends-with {prefix}:{suffix}:{count}"
        elif prefix:
            grind_option = f"--starts-with {prefix}:{count}"
        elif suffix:
            grind_option = f"--ends-with {suffix}:{count}"
        command += grind_option.split()

        # Add additional flags
        if ignore_case:
            command.append("--ignore-case")
        if use_mnemonic:
            command.append("--use-mnemonic")
            command += ["--word-count", word_count]
            command += ["--language", language]
            if no_bip39_passphrase:
                command.append("--no-bip39-passphrase")
        if num_threads:
            command += ["--num-threads", num_threads]

        # Display the constructed command in the console for debugging
        self.console_output_text.config(state=tk.NORMAL)
        self.console_output_text.insert(tk.END, f"Constructed Command: {' '.join(command)}\n\n")
        self.console_output_text.see(tk.END)
        self.console_output_text.config(state=tk.DISABLED)

        try:
            # Start the subprocess with 'wallets/' as the working directory
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=wallets_dir
            )
        except Exception as e:
            messagebox.showerror("Execution Error", f"An error occurred while starting the process:\n{e}")
            self.process = None
            return

        # Update button to "Stop Grinding" with red color
        self.start_button.config(text="Stop Grinding", fg="red")

        # Show and start the progress bar
        self.progress.grid()
        self.progress.start(10)  # Adjust the speed as needed

        # Start a thread to read the subprocess output
        threading.Thread(target=self.read_process_output, daemon=True).start()

    def stop_grind_process(self):
        """Terminate the grinding process."""
        if self.process:
            self.process.terminate()
            self.append_console_text("\nGrinding process terminated by user.\n")
            self.process = None
            # Update button back to "Start Grind" with green color
            try:
                self.start_button.config(text="Start Grind", bg="green")
            except tk.TclError:
                pass  # Widget has been destroyed
            # Stop and hide the progress bar
            try:
                self.progress.stop()
                self.progress.grid_remove()
            except tk.TclError:
                pass  # Widget has been destroyed

    def read_process_output(self):
        """Read the subprocess output and display it in the console in real-time."""
        try:
            # Read stdout
            for line in self.process.stdout:
                self.append_console_text(line)
            # Read stderr
            for line in self.process.stderr:
                self.append_console_text(line)
        except Exception as e:
            self.append_console_text(f"An error occurred while reading process output: {e}\n")
        finally:
            # Reset the button and process reference
            self.process = None
            if not self.is_closing:
                try:
                    self.start_button.config(text="Start Grind", bg="green")
                    # Stop and hide the progress bar
                    self.progress.stop()
                    self.progress.grid_remove()
                except tk.TclError:
                    pass  # Widget has been destroyed
                # After process completion, read the new wallet files and display wallet details
                self.display_generated_wallets()

    def append_console_text(self, text):
        """Append text to the console_output_text widget in a thread-safe manner."""
        if self.is_closing:
            return  # Do not attempt to update widgets if closing

        def append():
            try:
                self.console_output_text.config(state=tk.NORMAL)
                self.console_output_text.insert(tk.END, text)
                self.console_output_text.see(tk.END)
                self.console_output_text.config(state=tk.DISABLED)
            except tk.TclError:
                # Widget has been destroyed; ignore the error
                pass

        self.after(0, append)

    def display_generated_wallets(self):
        """Read the newly generated JSON file(s) and display wallet address and private key."""
        if self.is_closing:
            return  # Do not attempt to update widgets if closing

        wallets_dir = 'wallets'
        current_wallet_files = set(f for f in os.listdir(wallets_dir) if f.endswith('.json'))
        new_wallet_files = current_wallet_files - self.existing_wallet_files

        if not new_wallet_files:
            self.append_console_text("No new wallets were generated.\n")
            return

        for wallet_file in new_wallet_files:
            wallet_path = os.path.join(wallets_dir, wallet_file)
            try:
                with open(wallet_path, 'r') as f:
                    data = json.load(f)

                # Check if it's a single keypair or multiple
                if isinstance(data, list) and all(isinstance(item, int) for item in data):
                    # Single keypair
                    keypairs = [data]
                elif isinstance(data, list) and all(isinstance(item, list) for item in data):
                    # Multiple keypairs
                    keypairs = data
                else:
                    self.append_console_text(f"Unexpected JSON format in '{wallet_file}'.\n")
                    continue

                for keypair in keypairs:
                    if len(keypair) != 64:
                        self.append_console_text(f"Invalid keypair length in '{wallet_file}'.\n")
                        continue

                    secret_key = bytes(keypair[:32])
                    public_key = bytes(keypair[32:])

                    # Encode keys in base58
                    secret_key_base58 = base58.b58encode(secret_key).decode('utf-8')
                    public_key_base58 = base58.b58encode(public_key).decode('utf-8')

                    # Insert into Treeview
                    self.wallets_tree.insert('', 'end', values=(public_key_base58, secret_key_base58))

                self.append_console_text(f"Displayed wallet(s) from '{wallet_file}'.\n")

            except json.JSONDecodeError:
                self.append_console_text(f"Failed to parse JSON from '{wallet_file}'.\n")
            except Exception as e:
                self.append_console_text(f"An error occurred while reading '{wallet_file}': {e}\n")

    def on_close(self):
        """Handle the window close event with confirmation."""
        if self.process:
            if messagebox.askyesno("Exit Confirmation", "A grinding process is running. Do you want to terminate it and exit?"):
                self.is_closing = True  # Set the flag
                self.stop_grind_process()
                self.destroy()
        else:
            if messagebox.askyesno("Exit Confirmation", "Are you sure you want to exit this task?"):
                self.is_closing = True  # Set the flag
                self.destroy()

class SolanaVanityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SOLVanityGen v1.0")
        self.root.geometry("400x200")
        self.root.minsize(400, 200)
        self.root.resizable(False, False)

        self.task_count = 0  # To keep track of the number of tasks

        self.build_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Corrected line

    def build_gui(self):
        """Construct the main GUI layout."""
        pad_x = 20
        pad_y = 20

        # New Task Button
        new_task_button = tk.Button(
            self.root,
            text="New Grind Task",
            command=self.open_new_task,
            bg="blue",
            fg="blue",
            font=("Arial", 14, "bold"),
            width=20
        )
        new_task_button.pack(padx=pad_x, pady=pad_y)

        # Instructions
        instructions = tk.Label(
            self.root,
            text="Click 'New Grind Task' to start a new vanity address generation task.",
            font=("Arial", 12),
            wraplength=350,
            justify=tk.CENTER
        )
        instructions.pack(padx=pad_x, pady=(0, pad_y))

    def open_new_task(self):
        """Open a new TaskWindow."""
        self.task_count += 1
        TaskWindow(self.root, self.task_count)

    def on_close(self):
        """Handle the main window close event with confirmation."""
        if messagebox.askyesno("Exit Confirmation", "Are you sure you want to exit the application?"):
            self.root.destroy()

def main():
    # Ensure 'wallets' directory exists
    wallets_dir = 'wallets'
    if not os.path.exists(wallets_dir):
        try:
            os.makedirs(wallets_dir)
        except Exception as e:
            messagebox.showerror("Directory Error", f"Failed to create 'wallets' directory: {e}")
            sys.exit(1)

    # Check if solana-keygen is installed
    try:
        result = subprocess.run(["solana-keygen", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError:
        messagebox.showerror("Solana CLI Not Found", "The 'solana-keygen' command was not found. Please install the Solana CLI and ensure it's in your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        messagebox.showerror("Solana CLI Error", "An error occurred while checking 'solana-keygen'. Please ensure it is installed correctly.")
        sys.exit(1)

    root = tk.Tk()
    app = SolanaVanityApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
