import streamlit as st
import sqlite3
import qrcode
import os


if not os.path.exists('qr'):
    os.makedirs('qr')


def init_db():
    con = sqlite3.connect("banking_app.sqlite")
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Accounts (
            AccountNumber INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT,
            Password TEXT,
            Balance REAL DEFAULT 0
        )
    ''')
    con.commit()
    con.close()


def generate_qr_code(account_number, name, balance):
    qr_data = f"Account Number: {account_number}\nName: {name}\nBalance: {balance} Rs."
    qr_img = qrcode.make(qr_data)
    qr_file_path = f"qr/account_{account_number}.png"
    qr_img.save(qr_file_path)
    return qr_file_path


def create_account(name, password, initial_balance):
    try:
        con = sqlite3.connect("banking_app.sqlite")
        cur = con.cursor()

        cur.execute("INSERT INTO Accounts (Name, Password, Balance) VALUES (?, ?, ?)", 
                    (name, password, initial_balance))
        con.commit()

        cur.execute("SELECT AccountNumber FROM Accounts WHERE Name = ? AND Password = ?", (name, password))
        account_number = cur.fetchone()[0]

    
        qr_file_path = generate_qr_code(account_number, name, initial_balance)

        st.success(f"Account created successfully! Your account number is {account_number}.")
        st.image(qr_file_path, caption="Scan this QR code for account details", use_column_width=True)
        
        con.close()

    except Exception as e:
        st.error(f"Error: {e}")


def login(account_number, password):
    con = sqlite3.connect("banking_app.sqlite")
    cur = con.cursor()
    cur.execute("SELECT * FROM Accounts WHERE AccountNumber = ? AND Password = ?", (account_number, password))
    account = cur.fetchone()
    con.close()
    return account


def withdraw_money(account_number, amount):
    con = sqlite3.connect("banking_app.sqlite")
    cur = con.cursor()

    cur.execute("SELECT Balance FROM Accounts WHERE AccountNumber = ?", (account_number,))
    balance = cur.fetchone()[0]

    if amount > balance:
        st.error("Withdrawal amount exceeds the current balance!")
    else:
        new_balance = balance - amount
        cur.execute("UPDATE Accounts SET Balance = ? WHERE AccountNumber = ?", (new_balance, account_number))
        con.commit()
        st.success(f"Rs.{amount} withdrawn successfully. New balance: Rs.{new_balance}")
    
    con.close()


def deposit_money(account_number, amount):
    con = sqlite3.connect("banking_app.sqlite")
    cur = con.cursor()

    cur.execute("SELECT Balance FROM Accounts WHERE AccountNumber = ?", (account_number,))
    balance = cur.fetchone()[0]

    new_balance = balance + amount
    cur.execute("UPDATE Accounts SET Balance = ? WHERE AccountNumber = ?", (new_balance, account_number))
    con.commit()

    st.success(f"Rs.{amount} deposited successfully. New balance: Rs.{new_balance}")
    con.close()


def check_balance(account_number):
    con = sqlite3.connect("banking_app.sqlite")
    cur = con.cursor()

    cur.execute("SELECT Balance FROM Accounts WHERE AccountNumber = ?", (account_number,))
    balance = cur.fetchone()[0]
    
    st.info(f"Your current balance is Rs.{balance}.")
    con.close()


def get_account_details(account_number):
    con = sqlite3.connect("banking_app.sqlite")
    cur = con.cursor()

    cur.execute("SELECT Name, Balance FROM Accounts WHERE AccountNumber = ?", (account_number,))
    account_info = cur.fetchone()

    con.close()
    return account_info


init_db()


st.set_page_config(page_title="IINO - Banking App", page_icon="💰")

st.title("IINO - Your Personal Banking System")


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_ac_no' not in st.session_state:
    st.session_state.current_ac_no = None

if not st.session_state.logged_in:
    st.subheader("Create an Account or Login")


    with st.expander("Create New Account"):
        name = st.text_input("Name", key="create_name")
        password = st.text_input("Password", type="password", key="create_password")
        initial_balance = st.number_input("Initial Deposit", min_value=0, step=1, value=0, key="create_balance")

        if st.button("Create Account", key="create_button"):
            if name and password:
                create_account(name, password, initial_balance)
            else:
                st.error("Please fill in all fields.")


    with st.expander("Login to Your Account"):
        account_number = st.text_input("Account Number", key="login_acno")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if account_number.isdigit() and password:
                account = login(int(account_number), password)
                if account:
                    st.session_state.logged_in = True
                    st.session_state.current_ac_no = account[0]
                    st.success(f"Welcome back, {account[1]}!")
                else:
                    st.error("Incorrect account number or password!")
            else:
                st.error("Please enter valid account details.")
else:
  
    account_info = get_account_details(st.session_state.current_ac_no)
    if account_info:
        st.subheader(f"Account Holder: {account_info[0]}")
        st.subheader(f"Account Number: {st.session_state.current_ac_no}")
        st.subheader(f"Current Balance: Rs.{account_info[1]}")

    
        qr_file_path = f"qr/account_{st.session_state.current_ac_no}.png"
        if os.path.exists(qr_file_path):
            st.image(qr_file_path, caption="Your Account QR Code", use_column_width=True)
        else:
            st.error("QR code not found for this account.")

 
    st.subheader("...BANKING MENU...")


    with st.expander("Withdraw Money"):
        withdraw_amount = st.number_input("Enter amount to withdraw:", min_value=0, step=1, key="withdraw_amount")
        if st.button("Withdraw", key="withdraw_button"):
            withdraw_money(st.session_state.current_ac_no, withdraw_amount)


    with st.expander("Deposit Money"):
        deposit_amount = st.number_input("Enter amount to deposit:", min_value=0, step=1, key="deposit_amount")
        if st.button("Deposit", key="deposit_button"):
            deposit_money(st.session_state.current_ac_no, deposit_amount)


    with st.expander("Check Balance"):
        if st.button("Check Balance", key="check_balance_button"):
            check_balance(st.session_state.current_ac_no)


    if st.button("Logout", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.current_ac_no = None
        st.success("You have been logged out.")
