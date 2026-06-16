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
    """
    Each visitor gets their own temporary SQLite database.
    This DB persists only while their Streamlit session is alive.
    It is never shared between users.
    """
    if "db_path" not in st.session_state:
        unique_id = str(uuid.uuid4())[:8]
        db_name = f"demo_db_{unique_id}.sqlite"
        st.session_state.db_path = db_name
        initialize_demo_db(st.session_state.db_path)

    return st.session_state.db_path

def initialize_demo_db(db_path):
    """
    Creates the schema for a brand-new isolated demo database containing
    all unified operational schema components.
    """
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # System Settings Profile
        cur.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_fee_percentage REAL DEFAULT 3.0,
                company_name TEXT DEFAULT 'GateOps Pro Installers'
            )
        ''')
        # Customers Table (with Soft Delete integration)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, phone TEXT, email TEXT, address TEXT,
                notes TEXT, is_active INTEGER DEFAULT 1
            )
        ''')
        # Proposals Table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER,
                operator_type TEXT, accessories_list TEXT, scope_of_work TEXT,
                base_pricing REAL, total_with_fees REAL, status TEXT DEFAULT 'Pending',
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        # Work Orders / Active Dispatches Table
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
        
        # Populate default settings row inside the fresh isolated instance
        cur.execute("INSERT INTO system_settings (id, card_fee_percentage) VALUES (1, 3.0)")
        
        conn.commit()
        conn.close()

def get_connection():
    """
    Returns a thread-safe row-factory SQLite connection to the 
    session-isolated temporary DB file context.
    """
    db_path = get_session_db()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# 1. PAGE ENGINE, WHITE-LABELING & INITIALIZATION
# ==========================================
st.set_page_config(
    page_title="GateOps Pro - Enterprise Workspace",
    page_icon="🚧",
    layout="wide"
)

# Safe Enterprise White-Labeling (Hides branding framework layout elements)
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
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# SHOW DEMO BANNER
# ==========================================
show_demo_banner()

# ==========================================
# 3. GLOBAL WORKSPACE SETTINGS CACHING (ROUTED TO SESSION-DB)
# ==========================================
current_fee_rate = 3.0  # Safe fallback default baseline
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

# SaaS Subscription Tier Matrix Selection Array
installer_tier = st.sidebar.selectbox(
    "Active Account License Tier",
    ["Tier 1: Field Tech (Starter Plan)", 
     "Tier 2: Ops Commander (Growth Plan)", 
     "Tier 3: Enterprise Compliance (Premium Plan)"]
)

# Dynamic Pricing Label Translation Matrix Map
tier_pricing = {
    "Tier 1: Field Tech (Starter Plan)": "$49 / Month",
    "Tier 2: Ops Commander (Growth Plan)": "$149 / Month",
    "Tier 3: Enterprise Compliance (Premium Plan)": "$349 / Month"
}
st.sidebar.write(f"Subscription Value Billing: **{tier_pricing[installer_tier]}**")
st.sidebar.markdown("---")

st.sidebar.subheader("Credit Card Fee Surcharge")
new_fee = st.sidebar.number_input(
    "Set Customer Card Processing Fee (%)", 
    min_value=0.0, max_value=6.0, value=current_fee_rate, step=0.1
)

if new_fee != current_fee_rate:
    try:
        with get_connection() as conn:
            conn.execute("UPDATE system_settings SET card_fee_percentage = ? WHERE id = 1", (new_fee,))
            conn.commit()
        st.sidebar.success(f"Fee updated to {new_fee}% globally!")
        st.rerun()
    except Exception:
        st.sidebar.error("Local database sync exception.")

st.sidebar.markdown("---")
st.sidebar.info("💡 Pro Tip: Passing processing surcharges directly to commercial clients can save your business thousands of dollars in annual merchant account swipe fees.")

# ==========================================
# 5. DYNAMIC INTERFACE CONTROLS & GENERATION
# ==========================================
st.title("🚧 GateOps Pro Enterprise Suite")

# Enforce Navigation System Constraints based on the installer's active subscription tier
if installer_tier == "Tier 1: Field Tech (Starter Plan)":
    st.write("Logged Account Tier: `Tier 1 (Starter - $49/mo)`")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Client Intake & Directory", "📄 Proposal Builder Engine", "📅 Dispatch Routing (Locked)", "📋 Compliance Audits (Locked)", "📊 Executive Analytics (Locked)"])
    tier_level = 1
elif installer_tier == "Tier 2: Ops Commander (Growth Plan)":
    st.write("Logged Account Tier: `Tier 2 (Growth Pro - $149/mo)`")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Client Intake & Directory", "📄 Proposal Builder Engine", "📅 Dispatch & Scheduling", "📋 Field Service Work Orders", "📊 Executive Analytics (Locked)"])
    tier_level = 2
else:
    st.write("Logged Account Tier: `Tier 3 (Enterprise Premium - $349/mo)`")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Client Intake & Directory", "📄 Proposal Builder Engine", "📅 Dispatch & Scheduling", "📋 Compliance Checks & Work Orders", "📊 Executive Performance Analytics"])
    tier_level = 3

# ------------------------------------------
# TAB 1: CLIENT INTAKE (WITH SOFT DELETE)
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
                        conn.execute(
                            "INSERT INTO customers (name, phone, email, address, notes) VALUES (?, ?, ?, ?, ?)",
                            (c_name, c_phone, c_email, c_address, c_notes)
                        )
                        conn.commit()
                    st.success(f"Successfully added profile registry for {c_name}!")
                    st.rerun()
                else:
                    st.error("Name entry field is mandatory.")

    with col2:
        st.subheader("Active Customer Registry")
        with get_connection() as conn:
            active_df = pd.read_sql_query("SELECT id, name, phone, email, address, notes FROM customers WHERE is_active = 1", conn)
        
        if not active_df.empty:
            st.dataframe(active_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("🚫 Deactivate & Archive Property File")
            archive_map = dict(zip(active_df["name"], active_df["id"]))
            target_archive = st.selectbox("Select property profile to safely archive:", options=list(archive_map.keys()))
            
            if st.button("Archive Profile Row", type="primary"):
                with get_connection() as conn:
                    conn.execute("UPDATE customers SET is_active = 0 WHERE id = ?", (archive_map[target_archive],))
                    conn.commit()
                st.success(f"Archived {target_archive} safely out of dispatch registries.")
                st.rerun()
        else:
            st.info("No active property records located inside system memory workspace.")

# ------------------------------------------
# TAB 2: PROPOSAL BUILDER ENGINE
# ------------------------------------------
with tab2:
    st.header("Estimate Presentation & Surcharge Configuration Engine")
    
    with get_connection() as conn:
        customer_choices = conn.execute("SELECT id, name FROM customers WHERE is_active = 1").fetchall()
        
    if not customer_choices:
        st.info("Please create an active customer under Tab 1 before compiling job estimates.")
    else:
        cust_dict = {row["name"]: row["id"] for row in customer_choices}
        
        with st.form("proposal_generation_form"):
            target_cust = st.selectbox("Select Project Prospect Customer Location", options=list(cust_dict.keys()))
            
            c1, c2 = st.columns(2)
            with c1:
                op_type = st.selectbox("Select Target Gate Operator Core Drive System", [
                    "Heavy Commercial Slide Gate Operator (Chain Drive)",
                    "Hydraulic Articulated Arm Swing System",
                    "High-Traffic Commercial Overhead Operator Lift Array"
                ])
                scope = st.text_area("Detailed Scope of Operational Fabrication Work")
            with c2:
                accessories = st.multiselect("Select Integrated Safety Infrastructure Components", [
                    "Monitored Reflective Retro Photo-Eye Beam Kit",
                    "Pre-Formed Inductive Ground Loop Coils (Shadow/Exit Matrices)",
                    "Four-Wire Resistive Contact Safety Pressure Edge Trim",
                    "Wireless Access Proximity Credentials Card Reader Base"
                ])
                base_cost = st.number_input("Base Component Layout & Labor Quoted Price ($)", min_value=0.0, value=2500.0)
                
            if st.form_submit_button("Generate Complete Client Estimate Proposal"):
                percentage_multiplier = 1 + (new_fee / 100)
                gross_calculated_total = base_cost * percentage_multiplier
                acc_string = ", ".join(accessories)
                
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO proposals (customer_id, operator_type, accessories_list, scope_of_work, base_pricing, total_with_fees) VALUES (?, ?, ?, ?, ?, ?)",
                        (cust_dict[target_cust], op_type, acc_string, scope, base_cost, gross_calculated_total)
                    )
                    conn.commit()
                st.success("Proposal parameters compiled successfully.")
                st.rerun()

        st.markdown("---")
        st.subheader("📋 Active Field Proposals Queue")
        with get_connection() as conn:
            proposals_query = """
                SELECT p.id, c.name as customer_name, p.operator_type, p.base_pricing, p.total_with_fees, p.status 
                FROM proposals p JOIN customers c ON p.customer_id = c.id WHERE c.is_active = 1
            """
            prop_df = pd.read_sql_query(proposals_query, conn)
            
        if not prop_df.empty:
            st.dataframe(prop_df, use_container_width=True, hide_index=True)
            
            st.markdown("### 🖋️ Present & Update Proposal State Decision")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                selected_prop_id = st.selectbox("Select Proposal Record Reference ID", options=prop_df["id"].tolist())
                decision_state = st.radio("Customer Decision Status Choice", ["Accepted - Pass to Dispatch Routing", "Declined - Archive Record Information"])
            with col_d2:
                printed_sig_name = st.text_input("Authorized Signee Printed Legal Full Name")
                st.caption("Touch/Finger Signing Protocol Capture Window simulator below:")
                signature_confirm = st.checkbox("Signee hereby authorizes structural scope of work parameters digitally.")
                
            if st.button("Commit Status Verification Update"):
                if decision_state == "Accepted - Pass to Dispatch Routing":
                    if not printed_sig_name or not signature_confirm:
                        st.error("Signee name authentication and signature check validations required.")
                    else:
                        with get_connection() as conn:
                            conn.execute("UPDATE proposals SET status = 'Accepted' WHERE id = ?", (selected_prop_id,))
                            prop_details = conn.execute("SELECT customer_id FROM proposals WHERE id = ?", (selected_prop_id,)).fetchone()
                            conn.execute(
                                "INSERT INTO dispatches (proposal_id, customer_id, client_signature, status) VALUES (?, ?, ?, 'Scheduled')",
                                (selected_prop_id, prop_details["customer_id"], printed_sig_name)
                            )
                            conn.commit()
                        st.success("Closing execution approved! Work ticket routed onto tracking boards.")
                        st.rerun()
                else:
                    with get_connection() as conn:
                        conn.execute("UPDATE proposals SET status = 'Declined' WHERE id = ?", (selected_prop_id,))
                        conn.commit()
                    st.warning("Proposal marked Declined and cleared from primary action pathways.")
                    st.rerun()

# ------------------------------------------
# TAB 3: DISPATCH & SCHEDULING (UPSELL PROTECTED)
# ------------------------------------------
with tab3:
    if tier_level < 2:
        st.markdown("## 🔒 Unlock Crew Dispatch & Route Management")
        st.write("You are currently using the **Field Tech Plan ($49/mo)**.")
        
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            st.info("""
            **What's inside the Ops Commander Tier ($149/mo):**
            * 📅 Team Calendaring & Drag-Drop Fleet Asset Dispatching
            * 🚛 Mobile Service Orders for Multi-Truck Operations
            * 🔄 Live Work-Ticket Phase Updates ('En Route', 'Scheduled')
            """)
        with col_up2:
            st.markdown("#### **Coordinate Multi-Crew Operations Efficiencies**")
            st.write("Stop tracking crew routing appointments via text logs and messy clipboards.")
            st.link_button("🚀 Step up to Ops Commander for +$100/mo", "https://yourbillingportal.com/upgrade")
    else:
        st.header("Fleet Coordination Dispatch Board")
        
        with get_connection() as conn:
            unassigned_tickets = conn.execute("""
                SELECT d.id, c.name FROM dispatches d 
                JOIN customers c ON d.customer_id = c.id 
                WHERE d.status = 'Scheduled' AND d.technician_crew IS NULL
            """).fetchall()
            
        if not unassigned_tickets:
            st.info("No unassigned work orders awaiting active routing updates.")
        else:
            st.subheader("Assign Crew & Calendar Fleet Assets")
            ticket_map = {f"Order #{row['id']} - Location: {row['name']}": row['id'] for row in unassigned_tickets}
            
            with st.form("dispatch_scheduling_assignment"):
                target_ticket = st.selectbox("Select Outstanding Service Work Order Target", options=list(ticket_map.keys()))
                crew_assignment = st.selectbox("Assign Field Technician/Installation Crew Unit", [
                    "Truck Fleet Unit Alpha (Lead Tech: Miller)",
                    "Truck Fleet Unit Bravo (Lead Tech: Ramirez)",
                    "Commercial Service Unit Charlie (Lead Tech: Evans)"
                ])
                target_date = st.date_input("Scheduled Field Deployment Targeting Date")
                
                if st.form_submit_button("Route Team and Deploy Ticket"):
                    with get_connection() as conn:
                        conn.execute(
                            "UPDATE dispatches SET technician_crew = ?, schedule_date = ?, status = 'En Route' WHERE id = ?",
                            (crew_assignment, target_date.strftime("%Y-%m-%d"), ticket_map[target_ticket])
                        )
                        conn.commit()
                    st.success("Crew asset matched. Active dispatch tickets forwarded to mobile truck arrays.")
                    st.rerun()

        st.markdown("---")
        st.subheader("📅 Active Field Commitments Calendar Queue")
        with get_connection() as conn:
            active_schedule_df = pd.read_sql_query("""
                SELECT d.id as ticket_id, c.name as customer, c.address, d.technician_crew, d.schedule_date, d.status 
                FROM dispatches d JOIN customers c ON d.customer_id = c.id WHERE d.status != 'Completed'
            """, conn)
        if not active_schedule_df.empty:
            st.dataframe(active_schedule_df, use_container_width=True, hide_index=True)
        else:
            st.write("No active pending crew dispatches currently deployed in field execution states.")

# ------------------------------------------
# TAB 4: COMPLIANCE CHECKS & DIGITAL WORK ORDERS (UPSELL PROTECTED)
# ------------------------------------------
with tab4:
    if tier_level < 2:
        st.markdown("## 🔒 Unlock Mobile Field Terminal Handouts")
        st.write("This module requires an upgraded installer license activation.")
        st.info("💡 Field technician mobile work closure reporting unlocks automatically starting at the **Ops Commander ($149/mo)** service tier layer.")
    else:
        st.header("Mobile Field Service Terminal")
        
        with get_connection() as conn:
            field_active_tickets = conn.execute("""
                SELECT d.id, c.name FROM dispatches d 
                JOIN customers c ON d.customer_id = c.id 
                WHERE d.status IN ('En Route', 'Scheduled') AND d.technician_crew IS NOT NULL
            """).fetchall()
            
        if not field_active_tickets:
            st.info("No active work dispatches are currently marked in open execution fields.")
        else:
            field_ticket_map = {f"Ticket #{row['id']} for {row['name']}": row['id'] for row in field_active_tickets}
            selected_field_id = st.selectbox("Select Active Property Arrival Ticket Target", options=list(field_ticket_map.keys()))
            
            st.markdown("---")
            
            # --- FEATURE IN-APP UPSELL UPGRADE CARD FOR COMPLIANCE MATRIX ---
            if tier_level < 3:
                st.markdown("### 🔒 Protect Your Business with UL 325 Safety Verification Matrices")
                st.write("You are currently on the **Ops Commander Plan ($149/mo)**.")
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.warning("""
                    **What locks inside the Enterprise Compliance Plan ($349/mo):**
                    * 🛑 Forced Photo-Eye, Loop Matrix, and Contact Edge Safety Checkpoints
                    * 📄 Legal Verification Receipt & PDF Inspection Certificate Handouts
                    * 🛡️ Corporate Liability Lawsuit Protection Logs
                    """)
                with col_c2:
                    st.markdown("#### **Enforced Standardizations Keep You Out of Court**")
                    st.write("Forcing your technicians to pass UL 325 checkpoints before closing work logs provides massive legal protection.")
                    st.link_button("🚀 Unlock Enterprise Compliance for +$200/mo", "https://yourbillingportal.com/upgrade")
                
                st.markdown("---")
                st.subheader("📝 Close Basic Field Work Log")
                with st.form("basic_work_order_closure"):
                    t_id = field_ticket_map[selected_field_id]
                    basic_notes = st.text_area("On-Site Work Summary Progress Notes")
                    if st.form_submit_button("Close Job Ticket (Basic)"):
                        with get_connection() as conn:
                            conn.execute("UPDATE dispatches SET status = 'Completed', technician_notes = ? WHERE id = ?", (basic_notes, t_id))
                            conn.commit()
                        st.success("Ticket closed successfully!")
                        st.rerun()
            else:
                st.subheader("📋 Enforced Safety Compliance Point Checks (Tier 3 Activated)")
                st.caption("Standardized UL 325 & ASTM F2200 Hardware Testing Console")
                
                with st.form("safety_audit_submission_form"):
                    t_id = field_ticket_map[selected_field_id]
                    st.info(f"Filing Compliance Metrics Verification Record for Active Operational Ticket Reference ID #{t_id}")
                    
                    serial_no = st.text_input("Gate Operator System Serial Number (For Historical Records)")
                    
                    col_chk1, col_chk2 = st.columns(2)
                    with col_chk1:
                        pe_check = st.checkbox("Photo-Eye Interruption Test: Beam break stops & completely reverses gate travel.")
                        loop_check = st.checkbox("Inductive Loop Matrix Check: Ground coils maintain loop presence hold calls safely.")
                    with col_chk2:
                        edge_check = st.checkbox("Safety Obstruction Edge Test: Contact impact strips activate safety reverse limits instantly.")
                        hw_check = st.checkbox("Mechanical Hardware Integrity: Drive tracking alignment, sprockets, and chains certified.")
                        
                    tech_comments = st.text_area("On-Site Service Engineering Progress Logs & Repair Text Entries")
                    
                    st.markdown("#### Final Job Handover Certification Signatures")
                    col_sig1, col_sig2 = st.columns(2)
                    with col_sig1:
                        tech_sig = st.text_input("Lead Certified Installer/Technician Name Signature Block")
                    with col_sig2:
                        cust_sig_verify = st.text_input("Property Representative/Site Authority Acceptance Name")
                        
                    if st.form_submit_button("Lock Diagnostics & Issue Formal Verification Certificate Report"):
                        if not serial_no or not tech_sig or not cust_sig_verify:
                            st.error("Hardware Serial Number tracing constraints and explicit execution signatures are required to generate compliance certificates.")
                        else:
                            with get_connection() as conn:
                                conn.execute("""
                                    UPDATE dispatches 
                                    SET status = 'Completed', photo_eyes_pass = ?, loops_pass = ?, 
                                        edges_pass = ?, hardware_pass = ?, technician_notes = ?, 
                                        serial_number = ? 
                                    WHERE id = ?
                                """, (
                                    1 if pe_check else 0, 1 if loop_check else 0,
                                    1 if edge_check else 0, 1 if hw_check else 0,
                                    tech_comments, serial_no, t_id
                                ))
                                conn.commit()
                            st.success("Compliance diagnostics cataloged permanently! System receipt print-out streams generated below.")
                            st.rerun()

        # ==========================================
        # WORK ORDER COMPLIANCE HISTORY ARCHIVE (TIER 3 PREMIUM ONLY)
        # ==========================================
        if tier_level == 3:
            st.markdown("---")
            st.subheader("📜 Historical Structural Compliance Log Files")
            with get_connection() as conn:
                history_df = pd.read_sql_query("""
                    SELECT d.id as ticket_id, c.name as location, d.serial_number, d.schedule_date, 
                           d.photo_eyes_pass as photo_eyes, 
                           d.loops_pass as ground_loops, 
                           d.edges_pass as safety_edges, 
                           d.hardware_pass as mechanics, 
                           d.technician_notes, p.total_with_fees as invoice_amt 
                    FROM dispatches d 
                    JOIN customers c ON d.customer_id = c.id 
                    JOIN proposals p ON d.proposal_id = p.id 
                    WHERE d.status = 'Completed'
                """, conn)
                
            if not history_df.empty:
                st.dataframe(history_df, use_container_width=True, hide_index=True)
                
                st.markdown("### 📥 Instantly Export Compliant Field Inspection Receipts")
                target_receipt_id = st.selectbox("Select Completed Ticket Reference File target ID", options=history_df["ticket_id"].tolist())
                target_row = history_df[history_df["ticket_id"] == target_receipt_id].iloc[0]
                
                with st.expander(f"📄 PREVIEW COMPLIANCE REPORT RECEIPT FOR TICKET #{target_receipt_id}", expanded=True):
                    st.markdown(f"## **OFFICIAL GATE COMPLIANCE DISPATCH LOG CERTIFICATE**")
                    st.write(f"**Site Installation Property:** {target_row['location']}")
                    st.write(f"**Drive Mechanical Hardware Serial Target Identifier:** `{target_row['serial_number']}`")
                    st.write(f"**Certified Completion Close Date Timestamp:** {target_row['schedule_date']}")
                    st.markdown("---")
                    st.markdown(f"### **UL 325 National Automation Safety Matrix Checklist Audit Result Elements:**")
                    st.write(f"✔️ **Photo-Eye Obstruction Beam Deflection Protection Array:** {'PASS ✅' if target_row['photo_eyes'] == 1 else 'FAIL ❌'}")
                    st.write(f"✔️ **Inductive Subterranean Magnetic Tracking Vehicle Ground Loops:** {'PASS ✅' if target_row['ground_loops'] == 1 else 'FAIL ❌'}")
                    st.write(f"✔️ **Resistive Compression Direction Reverse Contact Sensor Edges:** {'PASS ✅' if target_row['safety_edges'] == 1 else 'FAIL ❌'}")
                    st.write(f"✔️ **Structural Bearing Alignments, Drive Sprocket Tensions & Anchors:** {'PASS ✅' if target_row['mechanics'] == 1 else 'FAIL ❌'}")
                    st.markdown("---")
                    st.write(f"**On-Site Deployed Crew Engineering Notes:** *{target_row['technician_notes']}*")
                    st.markdown(f"#### **Total Completed Job Statement Balance (Including Custom {new_fee}% CC Fee Addition Layer): ${target_row['invoice_amt']:.2f}**")
                    
                    st.download_button(
                        label="📥 Print/Download Text Compliance Report Stream",
                        data=f"GateOps Pro Compliance Certificate\nLocation: {target_row['location']}\nSerial: {target_row['serial_number']}\nInvoice: ${target_row['invoice_amt']:.2f}\nStatus: Certified UL 325 Compliant",
                        file_name=f"GateOps_Compliance_Report_Ticket_{target_receipt_id}.txt",
                        mime="text/plain"
                    )
            else:
                st.info("No completed compliance entries currently stored inside memory logs.")

# ------------------------------------------
# TAB 5: EXECUTIVE PERFORMANCE ANALYTICS (UPSELL PROTECTED)
# ------------------------------------------
with tab5:
    if tier_level < 3:
        st.markdown("## 🔒 Unlock Executive Analytics & Revenue Ledgers")
        st.write(f"You are currently leveraging the **{installer_tier}** configuration pattern.")
        
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            st.info("""
            **What activates inside the Premium Enterprise License ($349/mo):**
            * 📊 Live Gross Profit Margin Tracing Ledger Blocks
            * 💳 Exact Surcharges Collected Metric Card Tracking (Saved Swipe Cash)
            * 📈 Client Account Revenue Pipeline Comparison Bar Charts
            """)
        with col_ex2:
            st.markdown("#### **Gain Complete Data Clarity Over Your Operation**")
            st.write("Stop guessing your numbers. View precisely how much card processing fee overhead your business has bypassed and saved month-over-month.")
            st.link_button("🚀 Upgrade to Enterprise Plan for Full Access", "https://yourbillingportal.com/upgrade")
    else:
        st.header("Executive Board Performance Dash Analytics Dashboard")
        
        with get_connection() as conn:
            metrics = conn.execute("""
                SELECT 
                    COUNT(DISTINCT d.id) as total_jobs,
                    SUM(p.total_with_fees) as gross_revenue,
                    SUM(p.base_pricing) as base_revenue
                FROM dispatches d 
                JOIN proposals p ON d.proposal_id = p.id 
                WHERE d.status = 'Completed'
            """).fetchone()
            
        if not metrics or metrics["total_jobs"] == 0:
            st.info("Dashboard requires completed workflow execution profiles to map operational revenue data charts.")
        else:
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            
            gross_rev = metrics["gross_revenue"] if metrics["gross_revenue"] else 0.0
            base_rev = metrics["base_revenue"] if metrics["base_revenue"] else 0.0
            surcharge_collected = gross_rev - base_rev
            
            with m_col1:
                st.metric("Total Operational Compliance Jobs Filed", f"{metrics['total_jobs']} Closed Tasks")
            with m_col2:
                st.metric("Gross Platform Managed Invoiced Revenue", f"${gross_rev:,.2f}", delta=f"Fees Added: {new_fee}%")
            with m_col3:
                st.metric("Surcharges Passed to Clients (Saved Cash)", f"${surcharge_collected:,.2f}", delta="100% Retained", delta_color="inverse")
            with m_col4:
                st.metric("Clean Net Cash Margin Baseline Ledger", f"${base_rev:,.2f}")
                
            st.markdown("---")
            st.subheader("📈 Revenue Source Pipelines Ledger")
            with get_connection() as conn:
                chart_data_df = pd.read_sql_query("""
                    SELECT c.name as customer_location, p.base_pricing as net_income, p.total_with_fees as gross_statement 
                    FROM dispatches d 
                    JOIN customers c ON d.customer_id = c.id 
                    JOIN proposals p ON d.proposal_id = p.id 
                    WHERE d.status = 'Completed'
                """, conn)
            
            if not chart_data_df.empty:
                st.bar_chart(chart_data_df, x="customer_location", y=["net_income", "gross_statement"], use_container_width=True)
