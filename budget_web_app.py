import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

FILE_NAME = "budget_data.csv"
SETTINGS_FILE = "budget_settings.csv"

st.set_page_config(page_title="Budgeting App", layout="centered")

st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    h1, h2, h3 {
        color: #1f3b73;
    }
    div[data-testid="stMetric"] {
        background-color: #f7f9fc;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e6ecf5;
    }
</style>
""", unsafe_allow_html=True)

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


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        settings_df = pd.read_csv(SETTINGS_FILE)
        if not settings_df.empty:
            return (
                float(settings_df.loc[0, "monthly_budget"]),
                float(settings_df.loc[0, "savings_goal"])
            )
    return 2000.0, 5000.0


def save_settings(monthly_budget, savings_goal):
    settings_df = pd.DataFrame([{
        "monthly_budget": monthly_budget,
        "savings_goal": savings_goal
    }])
    settings_df.to_csv(SETTINGS_FILE, index=False)


if "data" not in st.session_state:
    st.session_state.data = load_data()

if "monthly_budget" not in st.session_state or "savings_goal" not in st.session_state:
    loaded_budget, loaded_goal = load_settings()
    st.session_state.monthly_budget = loaded_budget
    st.session_state.savings_goal = loaded_goal


def prepare_data():
    df = st.session_state.data.copy()
    if not df.empty:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df


expense_categories = [
    "Groceries", "Travel", "Mortgage", "Energy", "HCA Coach", "PCL HSE INS",
    "NOW Broadband", "Entertainment", "Shopping", "Takeout", "Savings", "Other",
    "Car LVIC", "DVLA", "Union", "Gym", "Aviva Hse", "Nest", "Water",
    "Council Tax", "TV Licence"
]

income_categories = [
    "Salary", "Freelance", "Bonus", "Business", "Investment", "ISA"
]

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Add Transaction", "Reports", "Settings"])

data = prepare_data()

total_income = data.loc[data["Type"] == "Income", "Amount"].sum() if not data.empty else 0.0
total_expenses = data.loc[data["Type"] == "Expense", "Amount"].sum() if not data.empty else 0.0
balance = total_income - total_expenses
remaining_budget = st.session_state.monthly_budget - total_expenses

savings_progress = data.loc[data["Category"] == "Savings", "Amount"].sum() if not data.empty else 0.0
savings_pct = min((savings_progress / st.session_state.savings_goal) * 100, 100.0) if st.session_state.savings_goal > 0 else 0.0

with tab1:
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

    st.subheader("Spending Insights")
    expense_data = data[data["Type"] == "Expense"] if not data.empty else pd.DataFrame()

    if not expense_data.empty:
        category_totals = expense_data.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        top_category = category_totals.index[0]
        top_amount = category_totals.iloc[0]
        st.info(f"Highest spending category: {top_category} (£{top_amount:,.2f})")
    else:
        st.info("Add expense transactions to see spending insights.")

with tab2:
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

    if st.button("Add Transaction", width="stretch"):
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

    st.subheader("Edit Transaction")

    data = prepare_data()
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

        if st.button("Update Transaction", width="stretch"):
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
    else:
        st.info("No transactions available to edit.")

    st.subheader("Delete Transaction")

    data = prepare_data()
    if not data.empty:
        delete_options = [
            f"{i} | {row['Date'].strftime('%Y-%m-%d') if pd.notnull(row['Date']) else 'No Date'} | {row['Type']} | £{row['Amount']:.2f} | {row['Category']}"
            for i, row in data.reset_index(drop=True).iterrows()
        ]

        selected_delete = st.selectbox("Select a transaction to delete", delete_options)
        delete_index = int(selected_delete.split(" | ")[0])

        if st.button("Delete Selected Transaction", width="stretch"):
            st.session_state.data = st.session_state.data.drop(index=delete_index).reset_index(drop=True)
            save_data(st.session_state.data)
            st.success("Transaction deleted.")
            st.rerun()
    else:
        st.info("No transactions available to delete.")

with tab3:
    st.subheader("Reports")

    data = prepare_data()

    st.markdown("### Transactions")
    if not data.empty:
        display_data = data.copy()
        display_data["Date"] = display_data["Date"].dt.strftime("%Y-%m-%d")
        display_data["Amount"] = display_data["Amount"].map(lambda x: f"£{x:,.2f}")
        st.dataframe(display_data, width="stretch")
    else:
        st.info("No transactions added yet.")

    st.markdown("### Expense Summary")
    expense_data = data[data["Type"] == "Expense"] if not data.empty else pd.DataFrame()

    if not expense_data.empty:
        summary = expense_data.groupby("Category", as_index=False)["Amount"].sum()
        summary = summary.sort_values(by="Amount", ascending=False)

        summary_display = summary.copy()
        summary_display["Amount"] = summary_display["Amount"].map(lambda x: f"£{x:,.2f}")
        st.dataframe(summary_display, width="stretch")

        fig1 = px.pie(
            summary,
            names="Category",
            values="Amount",
            title="Expense Breakdown"
        )
        st.plotly_chart(fig1, width="stretch")
    else:
        st.info("No expense data available yet.")

    st.markdown("### Monthly Trend")
    if not data.empty and data["Date"].notna().any():
        trend_data = data.copy()
        trend_data["Month"] = trend_data["Date"].dt.to_period("M").astype(str)

        monthly_summary = trend_data.groupby(["Month", "Type"], as_index=False)["Amount"].sum()

        st.dataframe(monthly_summary, width="stretch")

        fig2 = px.line(
            monthly_summary,
            x="Month",
            y="Amount",
            color="Type",
            markers=True,
            title="Monthly Income vs Expenses"
        )
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info("Add dated transactions to see monthly trends.")

    st.markdown("### Export Data")
    if not data.empty:
        csv_data = st.session_state.data.copy()
        csv_data["Date"] = pd.to_datetime(csv_data["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        st.download_button(
            label="Download CSV",
            data=csv_data.to_csv(index=False).encode("utf-8"),
            file_name="budget_data.csv",
            mime="text/csv",
            width="stretch"
        )

    st.markdown("### Reset")
    if st.button("Clear All Data", width="stretch"):
        st.session_state.data = pd.DataFrame(columns=["Date", "Type", "Amount", "Category"])
        save_data(st.session_state.data)
        st.success("All data cleared.")
        st.rerun()

with tab4:
    st.subheader("Budget Settings")

    new_budget = st.number_input(
        "Set Monthly Budget (£)",
        min_value=0.0,
        value=float(st.session_state.monthly_budget),
        step=50.0
    )

    new_goal = st.number_input(
        "Set Savings Goal (£)",
        min_value=0.0,
        value=float(st.session_state.savings_goal),
        step=100.0
    )

    if st.button("Save Settings", width="stretch"):
        st.session_state.monthly_budget = new_budget
        st.session_state.savings_goal = new_goal
        save_settings(new_budget, new_goal)
        st.success("Settings saved.")
        st.rerun()
