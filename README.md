# Solana Vanity Address Generator

This application allows you to generate Solana wallet addresses with custom prefixes and/or suffixes through an intuitive graphical user interface (GUI). It uses the Solana CLI tool `solana-keygen` to perform the grinding process and save wallets.

---

## Prerequisites

### 1. Install Rust
Ensure Rust is installed on your system:

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

Restart your terminal and verify the installation:

rustc --version


### 2. Install Solana CLI
Install the Solana CLI to enable wallet generation:

sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"

Verify the installation:

solana-keygen --version

### 3. Install Python Dependencies
Ensure Python is installed and accessible. Install the required dependencies:

pip install -r requirements.txt


---

## Usage

1. Run the application:
python main.py

2. Use the GUI to configure and start a vanity address generation task.

3. Wallets will be saved in the `wallets/` directory.

---

https://t.me/supercontinuity

