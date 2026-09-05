import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

from openai import OpenAI

client = OpenAI()

# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Finance OS",
    page_icon="💰",
    layout="wide"
)


# =========================================================
# CUSTOM DESIGN
# =========================================================

st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

h1 {
    font-size: 48px !important;
    font-weight: 800 !important;
}

h2 {
    font-weight: 700 !important;
}

div[data-testid="stMetric"] {
    background-color: #151515;
    border: 1px solid #333333;
    padding: 20px;
    border-radius: 15px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# RECONCILIATION ENGINE
# =========================================================

def reconcile(orders, payments):

    results = []

    # Find duplicate payments
    duplicate_ids = payments[
        payments.duplicated(
            subset=["order_id"],
            keep=False
        )
    ]["order_id"].unique()

    # Check every order
    for _, order in orders.iterrows():

        order_id = order["order_id"]
        expected_amount = order["order_amount"]

        matching_payments = payments[
            payments["order_id"] == order_id
        ]

        # ---------------------------------------------
        # MISSING PAYMENT
        # ---------------------------------------------

        if matching_payments.empty:

            results.append({
                "order_id": order_id,
                "expected_amount": expected_amount,
                "received_amount": 0,
                "difference": expected_amount,
                "status": "MISSING_PAYMENT"
            })

        # ---------------------------------------------
        # DUPLICATE PAYMENT
        # ---------------------------------------------

        elif order_id in duplicate_ids:

            received_amount = matching_payments[
                "payment_amount"
            ].sum()

            results.append({
                "order_id": order_id,
                "expected_amount": expected_amount,
                "received_amount": received_amount,
                "difference": received_amount - expected_amount,
                "status": "DUPLICATE_PAYMENT"
            })

        # ---------------------------------------------
        # NORMAL PAYMENT
        # ---------------------------------------------

        else:

            received_amount = matching_payments.iloc[0][
                "payment_amount"
            ]

            difference = received_amount - expected_amount

            if difference == 0:
                status = "MATCHED"
            else:
                status = "AMOUNT_MISMATCH"

            results.append({
                "order_id": order_id,
                "expected_amount": expected_amount,
                "received_amount": received_amount,
                "difference": difference,
                "status": status
            })

    result_df = pd.DataFrame(results)

    # ---------------------------------------------
    # UNKNOWN PAYMENTS
    # ---------------------------------------------

    unknown_payments = payments[
        ~payments["order_id"].isin(
            orders["order_id"]
        )
    ]

    return result_df, unknown_payments


# =========================================================
# HEADER
# =========================================================

st.title("FINANCE OS")

st.markdown(
    "### Autonomous AI Finance Controller"
)

st.caption(
    "RECONCILE  •  INVESTIGATE  •  RESOLVE  •  REPORT"
)

st.divider()


# =========================================================
# FILE UPLOAD
# =========================================================

st.subheader("📂 Financial Data")

col1, col2 = st.columns(2)

with col1:

    orders_file = st.file_uploader(
        "Upload Orders CSV",
        type=["csv"]
    )

with col2:

    payments_file = st.file_uploader(
        "Upload Payments CSV",
        type=["csv"]
    )


# =========================================================
# PROCESS DATA
# =========================================================

if orders_file and payments_file:

    orders = pd.read_csv(orders_file)
    payments = pd.read_csv(payments_file)

    st.success("Financial data loaded successfully!")

    # Run reconciliation
    results, unknown_payments = reconcile(
        orders,
        payments
    )

    # =====================================================
    # CALCULATE METRICS
    # =====================================================

    total_records = len(results)

    matched = len(
        results[
            results["status"] == "MATCHED"
        ]
    )

    exceptions = total_records - matched

    match_rate = (
        matched / total_records * 100
        if total_records > 0
        else 0
    )

    unresolved_amount = results[
        results["status"] != "MATCHED"
    ]["difference"].abs().sum()

    # =====================================================
    # FINANCE OVERVIEW
    # =====================================================

    st.divider()

    st.subheader("📊 Finance Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "TOTAL RECORDS",
        total_records
    )

    col2.metric(
        "MATCHED",
        matched
    )

    col3.metric(
        "EXCEPTIONS",
        exceptions
    )

    col4.metric(
        "MATCH RATE",
        f"{match_rate:.2f}%"
    )

    st.metric(
        "💰 UNRESOLVED EXPOSURE",
        f"₹{unresolved_amount:,.0f}"
    )

    # =====================================================
    # EXCEPTION RADAR
    # =====================================================

    st.divider()

    st.subheader("🚨 Exception Radar")

    exception_counts = results[
        results["status"] != "MATCHED"
    ]["status"].value_counts()

    if not exception_counts.empty:

        st.bar_chart(exception_counts)

    else:

        st.success("No exceptions detected!")


    # =====================================================
    # RECONCILIATION RESULTS
    # =====================================================

    st.divider()

    st.subheader("🔎 Reconciliation Results")

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # TRANSACTION INVESTIGATION
    # =====================================================

    st.divider()

    st.subheader("🕵️ Transaction Investigation")

    search_id = st.text_input(
        "Enter Order ID",
        placeholder="Example: ORD010"
    )

    if search_id:

        transaction = results[
            results["order_id"].astype(str).str.upper()
            == search_id.upper()
        ]

        if not transaction.empty:

            st.write("### Transaction Details")

            st.dataframe(
                transaction,
                use_container_width=True,
                hide_index=True
            )

            status = transaction.iloc[0]["status"]

            if status == "MATCHED":

                st.success(
                    f"✅ {search_id} is successfully reconciled."
                )

            else:

                st.warning(
                    f"⚠️ {search_id} requires investigation: {status}"
                )

        else:

            st.error(
                f"❌ No transaction found for {search_id}"
            )


    # =====================================================
    # EXCEPTIONS
    # =====================================================

    st.divider()

    st.subheader("⚠️ Unresolved Exceptions")

    exception_results = results[
        results["status"] != "MATCHED"
    ]

    if not exception_results.empty:

        st.dataframe(
            exception_results,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "🎉 All transactions successfully reconciled!"
        )


    # =====================================================
    # UNKNOWN PAYMENTS
    # =====================================================

    st.divider()

    st.subheader("🔍 Unknown Payments")

    if not unknown_payments.empty:

        st.dataframe(
            unknown_payments,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "No unknown payments detected!"
        )

else:

    st.info(
        "👆 Upload the Orders CSV and Payments CSV to begin reconciliation."
    )


      # =====================================================
    # AI FINANCE AGENT
    # =====================================================

    st.markdown("---")
    st.header("🤖 AI Finance Controller")

    st.write(
        "Ask questions about your transactions, payments, and reconciliation exceptions."
    )

    user_question = st.text_input(
        "Ask your Finance Agent:",
        placeholder="Example: Why are there unresolved transactions?"
    )

    if st.button("Ask AI Agent"):

        if user_question:

            with st.spinner(
                "AI Finance Agent is analyzing your financial data..."
            ):

                matched_count = len(
                    results[
                        results["status"] == "MATCHED"
                    ]
                )

                exception_count = len(
                    results[
                        results["status"] != "MATCHED"
                    ]
                )

                financial_context = f"""
You are an AI Finance Controller.

Financial reconciliation data:

Total orders: {len(orders)}
Total payments: {len(payments)}
Matched transactions: {matched_count}
Exceptions: {exception_count}

Reconciliation results:

{results.to_string(index=False)}

Unknown payments:

{unknown_payments.to_string(index=False)}

Answer the user's question using ONLY the financial data provided.

User question:
{user_question}

Give a clear and concise finance-operations answer.
"""

                response = client.responses.create(
                    model="gpt-5",
                    input=financial_context
                )

                st.success("AI Finance Agent Response")

                st.write(response.output_text)

        else:

            st.warning("Please enter a question first.")