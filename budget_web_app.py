import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

FILE_NAME = "budget_data.csv"

st.set_page_config(page_title="Budgeting App", layout="centered")

st.title("Personal Finance App")


def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        else:
            df["Date"] = pd.NaT
        return df
    return pd.DataFrame(columns=["Date", "Type", "Amount", "Category"])


def save_data(dataframe):
    save_df = dataframe.copy()
    if "Date" in save_df.columns:
        save_df["Date"] = pd.to_datetime(save_df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    save_df.to_csv(FILE_NAME, index=False)


if "data" not in st.session_state:
    st.session_state.data = load_data()

if "monthly_budget" not in st.session_state:
    st.session_state.monthly_budget = 2000.0

if "savings_goal" not in st.session_state:
    st.session_state.savings_goal = 5000.0


data = st.session_state.data.copy()

if not data.empty:
    data["Amount"] = pd.to_numeric(data["Amount"], errors="coerce").fillna(0)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")


# Sidebar settings
st.sidebar.header("Budget Settings")

st.session_state.monthly_budget = st.sidebar.number_input(
    "Set Monthly Budget (£)",
    min_value=0.0,
    value=float(st.session_state.monthly_budget),
    step=50.0
)

st.session_state.savings_goal = st.sidebar.number_input(
    "Set Savings Goal (£)",
    min_value=0.0,
    value=float(st.session_state.savings_goal),
    step=100.0
)


# Category lists
expense_categories = [
    "Groceries", "Travel", "Mortgage", "Energy", "HCA Coach" ,"PCL HSE INS", "NOW Broadband",
    "Entertainment", "Shopping", "Takeout", "Savings", "Other", "Car LVIC", "DVLA", "Union","Gym", "Aviva Hse", "Nest", "Water", "Council Tax", "TV Licence"
]

income_categories = [
    "Salary", "Freelance", "Bonus", "Business", "Investment", "ISA"
]


# Add transaction
st.subheader("Add Transaction")

col1, col2 = st.columns(2)
with col1:
    transaction_date = st.date_input("Date", value=date.today())
with col2:
    transaction_type = st.selectbox("Type", ["Income", "Expense"])

col3, col4 = st.columns(2)
with col3:
    amount = st.number_input("Amount (£)", min_value=0.0, step=1.0)
with col4:
    category_choice = st.selectbox(
        "Category",
        income_categories if transaction_type == "Income" else expense_categories
    )

custom_category = ""
if category_choice == "Other":
    custom_category = st.text_input("Enter Custom Category")

if st.button("Add Transaction", use_container_width=True):
    final_category = custom_category.strip() if category_choice == "Other" else category_choice

    if amount <= 0:
        st.error("Please enter a valid amount.")
    elif final_category == "":
        st.error("Please enter a category.")
    else:
        new_row = {
            "Date": pd.to_datetime(transaction_date),
            "Type": transaction_type,
            "Amount": float(amount),
            "Category": final_category
        }

        st.session_state.data = pd.concat(
            [st.session_state.data, pd.DataFrame([new_row])],
            ignore_index=True
        )
        save_data(st.session_state.data)
        st.success("Transaction added and saved.")
        st.rerun()


data = st.session_state.data.copy()

if not data.empty:
    data["Amount"] = pd.to_numeric(data["Amount"], errors="coerce").fillna(0)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")


# Dashboard calculations
total_income = data.loc[data["Type"] == "Income", "Amount"].sum()
total_expenses = data.loc[data["Type"] == "Expense", "Amount"].sum()
balance = total_income - total_expenses
remaining_budget = st.session_state.monthly_budget - total_expenses

savings_progress = data.loc[data["Category"] == "Savings", "Amount"].sum()
if st.session_state.savings_goal > 0:
    savings_pct = min((savings_progress / st.session_state.savings_goal) * 100, 100.0)
else:
    savings_pct = 0.0


# Cleaner dashboard
st.subheader("Dashboard")

m1, m2, m3 = st.columns(3)
m1.metric("Income", f"£{total_income:,.2f}")
m2.metric("Expenses", f"£{total_expenses:,.2f}")
m3.metric("Balance", f"£{balance:,.2f}")

st.write(f"**Monthly Budget:** £{st.session_state.monthly_budget:,.2f}")
st.write(f"**Remaining Budget:** £{remaining_budget:,.2f}")

if total_expenses > st.session_state.monthly_budget:
    st.error("You have gone over your monthly budget.")
elif total_expenses > st.session_state.monthly_budget * 0.8:
    st.warning("You are close to your monthly budget limit.")
else:
    st.success("You are within your monthly budget.")

st.subheader("Savings Goal")
st.write(f"**Goal:** £{st.session_state.savings_goal:,.2f}")
st.write(f"**Saved so far:** £{savings_progress:,.2f}")
st.progress(savings_pct / 100)
st.caption(f"{savings_pct:.1f}% of savings goal reached")


# Transactions display
st.subheader("Transactions")

if not data.empty:
    display_data = data.copy()
    display_data["Date"] = display_data["Date"].dt.strftime("%Y-%m-%d")
    display_data["Amount"] = display_data["Amount"].map(lambda x: f"£{x:,.2f}")
    st.dataframe(display_data, width="stretch")
else:
    st.info("No transactions added yet.")


# Edit transaction
st.subheader("Edit Transaction")

if not data.empty:
    edit_options = [
        f"{i} | {row['Date'].strftime('%Y-%m-%d') if pd.notnull(row['Date']) else 'No Date'} | {row['Type']} | £{row['Amount']:.2f} | {row['Category']}"
        for i, row in data.reset_index(drop=True).iterrows()
    ]

    selected_edit = st.selectbox("Select a transaction to edit", edit_options)
    edit_index = int(selected_edit.split(" | ")[0])

    row_to_edit = data.iloc[edit_index]

    e1, e2 = st.columns(2)
    with e1:
        new_date = st.date_input(
            "Edit Date",
            value=row_to_edit["Date"].date() if pd.notnull(row_to_edit["Date"]) else date.today(),
            key="edit_date"
        )
    with e2:
        new_type = st.selectbox(
            "Edit Type",
            ["Income", "Expense"],
            index=0 if row_to_edit["Type"] == "Income" else 1,
            key="edit_type"
        )

    e3, e4 = st.columns(2)
    with e3:
        new_amount = st.number_input(
            "Edit Amount (£)",
            min_value=0.0,
            value=float(row_to_edit["Amount"]),
            step=1.0,
            key="edit_amount"
        )
    with e4:
        category_list = income_categories if new_type == "Income" else expense_categories
        current_category = row_to_edit["Category"] if row_to_edit["Category"] in category_list else "Other"

        new_category_choice = st.selectbox(
            "Edit Category",
            category_list,
            index=category_list.index(current_category) if current_category in category_list else 0,
            key="edit_category_choice"
        )

    edited_custom_category = ""
    if new_category_choice == "Other":
        edited_custom_category = st.text_input(
            "Edit Custom Category",
            value=row_to_edit["Category"] if current_category == "Other" else "",
            key="edit_custom_category"
        )

    if st.button("Update Transaction", use_container_width=True):
        final_edited_category = edited_custom_category.strip() if new_category_choice == "Other" else new_category_choice

        if new_amount <= 0:
            st.error("Please enter a valid amount.")
        elif final_edited_category == "":
            st.error("Please enter a category.")
        else:
            st.session_state.data.loc[edit_index, "Date"] = pd.to_datetime(new_date)
            st.session_state.data.loc[edit_index, "Type"] = new_type
            st.session_state.data.loc[edit_index, "Amount"] = float(new_amount)
            st.session_state.data.loc[edit_index, "Category"] = final_edited_category

            save_data(st.session_state.data)
            st.success("Transaction updated.")
            st.rerun()


# Delete transaction
st.subheader("Delete Transaction")

if not data.empty:
    delete_options = [
        f"{i} | {row['Date'].strftime('%Y-%m-%d') if pd.notnull(row['Date']) else 'No Date'} | {row['Type']} | £{row['Amount']:.2f} | {row['Category']}"
        for i, row in data.reset_index(drop=True).iterrows()
    ]

    selected_delete = st.selectbox("Select a transaction to delete", delete_options)
    delete_index = int(selected_delete.split(" | ")[0])

    if st.button("Delete Selected Transaction", use_container_width=True):
        st.session_state.data = st.session_state.data.drop(index=delete_index).reset_index(drop=True)
        save_data(st.session_state.data)
        st.success("Transaction deleted.")
        st.rerun()


# Expense summary
st.subheader("Expense Summary")

expense_data = data[data["Type"] == "Expense"]

if not expense_data.empty:
    summary = expense_data.groupby("Category", as_index=False)["Amount"].sum()
    summary = summary.sort_values(by="Amount", ascending=False)

    summary_display = summary.copy()
    summary_display["Amount"] = summary_display["Amount"].map(lambda x: f"£{x:,.2f}")
    st.dataframe(summary_display, width="stretch")

    fig1, ax1 = plt.subplots(figsize=(6, 6))
    ax1.pie(summary["Amount"], labels=summary["Category"], autopct="%1.1f%%")
    ax1.set_title("Expense Breakdown")
    st.pyplot(fig1)

    top_category = summary.iloc[0]
    st.info(f"Highest spending category: {top_category['Category']} (£{top_category['Amount']:,.2f})")
else:
    st.info("No expense data available yet.")


# Monthly trend chart
st.subheader("Monthly Trend")

if not data.empty and data["Date"].notna().any():
    trend_data = data.copy()
    trend_data["Month"] = trend_data["Date"].dt.to_period("M").astype(str)

    monthly_summary = trend_data.groupby(["Month", "Type"], as_index=False)["Amount"].sum()
    pivot_summary = monthly_summary.pivot(index="Month", columns="Type", values="Amount").fillna(0)

    st.dataframe(pivot_summary.reset_index(), width="stretch")

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    if "Income" in pivot_summary.columns:
        ax2.plot(pivot_summary.index, pivot_summary["Income"], marker="o", label="Income")
    if "Expense" in pivot_summary.columns:
        ax2.plot(pivot_summary.index, pivot_summary["Expense"], marker="o", label="Expenses")

    ax2.set_title("Monthly Income vs Expenses")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Amount (£)")
    ax2.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig2)
else:
    st.info("Add dated transactions to see monthly trends.")


# Download
st.subheader("Export Data")
if not data.empty:
    csv_data = st.session_state.data.copy()
    csv_data["Date"] = pd.to_datetime(csv_data["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    st.download_button(
        label="Download CSV",
        data=csv_data.to_csv(index=False).encode("utf-8"),
        file_name="budget_data.csv",
        mime="text/csv",
        use_container_width=True
    )


# Reset
st.subheader("Reset")
if st.button("Clear All Data", use_container_width=True):
    st.session_state.data = pd.DataFrame(columns=["Date", "Type", "Amount", "Category"])
    save_data(st.session_state.data)
    st.success("All data cleared.")
    st.rerun()