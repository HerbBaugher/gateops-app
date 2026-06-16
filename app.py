import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import uuid
import os

# ==========================================
# DEMO MODE BANNER + SESSION-ISOLATED DATABASE
# ==========================================

def show_demo_banner():
    st.markdown(
        """
        <div style="
            background-color:#1E90FF;
            padding:15px;
            border-radius:8px;
            margin-bottom:20px;
            color:white;
            font-size:20px;
            font-weight:bold;
            text-align:center;">
            🚧 DEMO MODE — Your data is temporary and isolated to your session.
        </div>
        """,
        unsafe_allow_html=True
    )

def get_session_db():
    if "db_path" not in st.session_state:
        unique_id = str(uuid.uuid4())[:8]
        db_name = f"demo_db_{unique_id}.sqlite"
        st.session_state.db_path = db_name
        initialize_demo_db(st.session_state.db_path)
    return st.session_state.db_path

def initialize_demo_db(db_path):
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_fee_percentage REAL DEFAULT 3.0,
                company_name TEXT DEFAULT 'GateOps Pro Installers'
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, phone TEXT, email TEXT, address TEXT,
                notes TEXT, is_active INTEGER DEFAULT 1
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER,
                operator_payload TEXT, accessories_list TEXT, scope_of_work TEXT,
                base_pricing REAL, total_with_fees REAL, status TEXT DEFAULT 'Pending',
                logo_name TEXT DEFAULT 'Default Logo',
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS dispatches (
                id INTEGER PRIMARY KEY AUTOINCREMENT, proposal_id INTEGER,
                customer_id INTEGER, technician_crew TEXT, schedule_date TEXT,
                status TEXT DEFAULT 'Scheduled', client_signature TEXT,
                photo_eyes_pass INTEGER DEFAULT 0, loops_pass INTEGER DEFAULT 0,
                edges_pass INTEGER DEFAULT 0, hardware_pass INTEGER DEFAULT 0,
                technician_notes TEXT, serial_number TEXT,
                FOREIGN KEY (proposal_id) REFERENCES proposals (id),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        cur.execute("INSERT INTO system_settings (id, card_fee_percentage) VALUES (1, 3.0)")
        conn.commit()
        conn.close()

def get_connection():
    db_path = get_session_db()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# Initialize Dynamic UI Configuration Caches
# ==========================================
if "multi_gates" not in st.session_state:
    st.session_state.multi_gates = []
if "custom_accessories" not in st.session_state:
    st.session_state.custom_accessories = [
        "Monitored Reflective Retro Photo-Eye Beam Kit",
        "Pre-Formed Inductive Ground Loop Coils",
        "Four-Wire Resistive Contact Safety Pressure Edge",
        "Wireless Access Proximity Card Reader Base"
    ]
if "tech_crews" not in st.session_state:
    st.session_state.tech_crews = [
        "Truck Unit Alpha (Lead Tech: Miller)",
        "Truck Unit Bravo (Lead Tech: Ramirez)",
        "Commercial Service Unit Charlie (Lead Tech: Evans)"
    ]

# ==========================================
# 1. PAGE ENGINE & WHITE-LABELING
# ==========================================
st.set_page_config(page_title="GateOps Pro - Enterprise Workspace", page_icon="🚧", layout="wide")

st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        div[data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6;
            border-radius: 4px 4px 0px 0px;
            padding: 10px 20px;
        }
        .report-box {
            border: 2px solid #333;
            padding: 25px;
            background-color: #ffffff;
            color: #111111;
            border-radius: 8px;
            font-family: Arial, sans-serif;
        }
    </style>
    """,
    unsafe_allow_html=True
)

show_demo_banner()

# ==========================================
# 3. GLOBAL WORKSPACE SETTINGS CACHING
# ==========================================
current_fee_rate = 3.0
try:
    with get_connection() as conn:
        settings_row = conn.execute("SELECT * FROM system_settings WHERE id = 1").fetchone()
        if settings_row is not None:
            current_fee_rate = settings_row["card_fee_percentage"]
except Exception:
    pass

# ==========================================
# 4. DASHBOARD SIDEBAR ENGINE
# ==========================================
st.sidebar.title("⚙️ Workspace Management")
st.sidebar.markdown("---")

installer_tier = st.sidebar.selectbox(
    "Active Account License Tier",
    ["Tier 1: Field Tech (Starter Plan)", "Tier 2: Ops Commander (Growth Plan)", "Tier 3: Enterprise Compliance (Premium Plan)"]
)

tier_pricing = {
    "Tier 1: Field Tech (Starter Plan)": "$49 / Month",
    "Tier 2: Ops Commander (Growth Plan)": "$149 / Month",
    "Tier 3: Enterprise Compliance (Premium Plan)": "$349 / Month"
}
st.sidebar.write(f"Subscription Value Billing: **{tier_pricing[installer_tier]}**")
st.sidebar.markdown("---")

st.sidebar.subheader("Credit Card Fee Surcharge")
new_fee = st.sidebar.number_input("Set Customer Card Processing Fee (%)", min_value=0.0, max_value=6.0, value=current_fee_rate, step=0.1)

if new_fee != current_fee_rate:
    try:
        with get_connection() as conn:
            conn.execute("UPDATE system_settings SET card_fee_percentage = ? WHERE id = 1", (new_fee,))
            conn.commit()
        st.sidebar.success(f"Fee updated to {new_fee}% globally!")
        st.rerun()
    except Exception:
        pass

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Fleet Tech Profile Builder")
new_tech_entry = st.sidebar.text_input("Register New Technician / Crew Identity")
if st.sidebar.button("Add Tech to Rosters"):
    if new_tech_entry and new_tech_entry not in st.session_state.tech_crews:
        st.session_state.tech_crews.append(new_tech_entry)
        st.sidebar.success(f"Added {new_tech_entry} to selection trees!")
        st.rerun()

st.sidebar.markdown("---")

# ==========================================
# 5. DYNAMIC INTERFACE CONTROLS & GENERATION
# ==========================================
st.title("🚧 GateOps Pro Enterprise Suite")

if installer_tier == "Tier 1: Field Tech (Starter Plan)":
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Client Intake & Directory", "📄 Proposal Builder Engine", "📅 Dispatch Routing (Locked)", "📋 Compliance Audits (Locked)", "📊 Executive Analytics (Locked)"])
    tier_level = 1
elif installer_tier == "Tier 2: Ops Commander (Growth Plan)":
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Client Intake & Directory", "📄 Proposal Builder Engine", "📅 Dispatch & Scheduling", "📋 Field Service Work Orders", "📊 Executive Analytics (Locked)"])
    tier_level = 2
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Client Intake & Directory", "📄 Proposal Builder Engine", "📅 Dispatch & Scheduling", "📋 Compliance Checks & Work Orders", "📊 Executive Performance Analytics"])
    tier_level = 3

# ------------------------------------------
# TAB 1: CLIENT INTAKE
# ------------------------------------------
with tab1:
    st.header("Profile Intake Screen")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("New Client Entry Form")
        with st.form("add_customer_form", clear_on_submit=True):
            c_name = st.text_input("Customer/Property Name")
            c_phone = st.text_input("Primary Telephone Number")
            c_email = st.text_input("Billing Email Coordinates")
            c_address = st.text_input("Physical Gate Asset Location Address")
            c_notes = st.text_area("On-Site Ground Notes / Entry Restrictions")
            if st.form_submit_button("Save Property Target"):
                if c_name:
                    with get_connection() as conn:
                        conn.execute("INSERT INTO customers (name, phone, email, address, notes) VALUES (?, ?, ?, ?, ?)", (c_name, c_phone, c_email, c_address, c_notes))
                        conn.commit()
                    st.success(f"Successfully added profile registry for {c_name}!")
                    st.rerun()
    with col2:
        st.subheader("Active Customer Registry")
        with get_connection() as conn:
            active_df = pd.read_sql_query("SELECT id, name, phone, email, address, notes FROM customers WHERE is_active = 1", conn)
        if not active_df.empty:
            st.dataframe(active_df, use_container_width=True, hide_index=True)
            st.markdown("---")
            archive_map = dict(zip(active_df["name"], active_df["id"]))
            target_archive = st.selectbox("Select property profile to safely archive:", options=list(archive_map.keys()))
            if st.button("Archive Profile Row", type="primary"):
                with get_connection() as conn:
                    conn.execute("UPDATE customers SET is_active = 0 WHERE id = ?", (archive_map[target_archive],))
                    conn.commit()
                st.rerun()
        else:
            st.info("No active property records located inside system memory workspace.")

# ------------------------------------------
# TAB 2: PROPOSAL BUILDER ENGINE
# ------------------------------------------
with tab2:
    st.header("Preventive Maintenance Estimate")
    with get_connection() as conn:
        customer_choices = conn.execute("SELECT id, name FROM customers WHERE is_active = 1").fetchall()
        
    if not customer_choices:
        st.info("Please create an active customer under Tab 1 before compiling job estimates.")
    else:
        cust_dict = {row["name"]: row["id"] for row in customer_choices}
        target_cust = st.selectbox("Select Project Prospect Customer Location", options=list(cust_dict.keys()))
        
        st.markdown("---")
        st.subheader("🛠️ Add Gate Operators to this Estimate")
        
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        with col_g1:
            g_name = st.text_input("Select Gate Operator / Name", placeholder="e.g., North Entry Slide")
        with col_g2:
            g_qty = st.number_input("Quantity", min_value=1, value=1, step=1)
        with col_g3:
            g_cost = st.number_input("PM Cost ($ Per Unit)", min_value=0.0, value=250.0, step=10.0)
        with col_g4:
            g_loc = st.text_input("Site Location Details", placeholder="e.g., Back Perimeter Fence")
            
        if st.button("➕ Stage Gate Operator Line Item"):
            if g_name:
                st.session_state.multi_gates.append({
                    "name": g_name, "qty": g_qty, "cost": g_cost, "location": g_loc
                })
                st.success(f"Staged {g_name} into working memory matrix.")
                st.rerun()
                
        if st.session_state.multi_gates:
            st.markdown("#### Staged Gate Operators Queue Summary")
            gate_df = pd.DataFrame(st.session_state.multi_gates)
            st.dataframe(gate_df, use_container_width=True, hide_index=True)
            if st.button("🗑️ Clear Staged Operators"):
                st.session_state.multi_gates = []
                st.rerun()
                
        st.markdown("---")
        st.subheader("Select Integrated Safety and Accessory Components")
        
        col_acc1, col_acc2 = st.columns([3, 1])
        with col_acc1:
            new_acc_entry = st.text_input("Missing an accessory? Enter Custom System Item Element:", placeholder="e.g., Siren Operated Sensor (SOS)")
        with col_acc2:
            if st.button("➕ Add Accessory Option"):
                if new_acc_entry and new_acc_entry not in st.session_state.custom_accessories:
                    st.session_state.custom_accessories.append(new_acc_entry)
                    st.rerun()
                    
        accessories = st.multiselect("Check all system options integrated onto this property package:", st.session_state.custom_accessories)
        
        calc_base_cost = sum(item["qty"] * item["cost"] for item in st.session_state.multi_gates)
        
        st.markdown("---")
        st.subheader("Detailed Scope of Work")
        logo_choice = st.selectbox("Select Asset Brand Template Header Logo:", ["Default Corporate Shield Logo", "Gold Premium Services Logo", "Elite Gate Systems Crest Logo"])
        
        default_template_scope = "Contractor will execute basic multi-point diagnostic assessments, lubrication sequence applications, tension adjustments, and safety performance criteria tracking logs on all listed perimeter access machines matching industrial compliance layouts."
        scope = st.text_area("Edit corporate document baseline formatting text targets directly below:", value=default_template_scope, height=120)
        
        st.markdown("---")
        st.subheader("PM Quoted Price ($)")
        final_base_cost = st.number_input("Calculated Baseline Value Array Aggregate Target", min_value=0.0, value=float(calc_base_cost))
        
        if st.button("Compile & Log Client Proposal Package"):
            if not st.session_state.multi_gates:
                st.error("You must stage at least one Gate Operator element to log a valid configuration profile.")
            else:
                percentage_multiplier = 1 + (new_fee / 100)
                gross_calculated_total = final_base_cost * percentage_multiplier
                
                gate_payload_string = " | ".join([f"{i['qty']}x {i['name']} ({i['location']}) @ ${i['cost']:.2f}" for i in st.session_state.multi_gates])
                acc_string = ", ".join(accessories)
                
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO proposals (customer_id, operator_payload, accessories_list, scope_of_work, base_pricing, total_with_fees, logo_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (cust_dict[target_cust], gate_payload_string, acc_string, scope, final_base_cost, gross_calculated_total, logo_choice)
                    )
                    conn.commit()
                st.success("Proposal parameters compiled into historical tracking blocks successfully!")
                st.session_state.multi_gates = []
                st.rerun()

        st.markdown("---")
        st.subheader("Accept or Deny Proposal")
        
        with get_connection() as conn:
            proposals_query = """
                SELECT p.id, p.customer_id, c.name as customer_name, p.operator_payload as itemized_layouts, 
                       p.base_pricing, p.total_with_fees, p.status, p.scope_of_work, p.logo_name, p.accessories_list
                FROM proposals p JOIN customers c ON p.customer_id = c.id WHERE c.is_active = 1
            """
            prop_df = pd.read_sql_query(proposals_query, conn)
            
        if not prop_df.empty:
            st.dataframe(prop_df, use_container_width
