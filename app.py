import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE CONFIGURATION (Strictly First!)
# ==========================================
st.set_page_config(
    page_title="GateOps Pro - Field Service Dashboard",
    page_icon="🛠️", 
    layout="wide"
)

# ==========================================
# 2. LOCAL DATABASE ENGINE (SQLite)
# ==========================================
def get_db_connection():
    """Establishes connection to a local SQLite file database."""
    conn = sqlite3.connect("gateops_local_production.db")
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def init_db():
    """Initializes local schema tables using standard SQLite structures."""
    with get_db_connection() as conn:
        # 1. Customers Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, phone TEXT, email TEXT, address TEXT
            )
        ''')
        # 2. Maintenance Contracts Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER,
                contract_type TEXT, start_date TEXT, end_date TEXT, price REAL,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        # 3. Service Dispatches Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS dispatches (
                id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER,
                technician TEXT, scheduled_date TEXT, issue_description TEXT, status TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        # 4. UL 325 PM Checklists Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pm_checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT, dispatch_id INTEGER,
                photo_eyes_pass INTEGER, loop_detectors_pass INTEGER, edge_sensors_pass INTEGER,
                gate_hardware_pass INTEGER, technician_notes TEXT,
                FOREIGN KEY (dispatch_id) REFERENCES dispatches (id)
            )
        ''')
        # 5. App Settings / SaaS Agreement Configuration Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                saas_accepted INTEGER DEFAULT 0,
                trial_start_date TEXT
            )
        ''')
        
        # Check if initial system configuration seeding is required
        settings_check = conn.execute("SELECT COUNT(*) as count FROM app_settings").fetchone()
        if settings_check["count"] == 0:
            today_str = datetime.now().strftime("%Y-%m-%d")
            conn.execute("INSERT INTO app_settings (saas_accepted, trial_start_date) VALUES (0, ?)", (today_str,))
        
        conn.commit()

# Execute database initialization
init_db()

# Query local settings configuration to check app state
with get_db_connection() as conn:
    settings = conn.execute("SELECT * FROM app_settings WHERE id = 1").fetchone()

saas_accepted = settings["saas_accepted"]
trial_start = datetime.strptime(settings["trial_start_date"], "%Y-%m-%d").date()
trial_end = trial_start + timedelta(days=14)
days_remaining = (trial_end - datetime.now().date()).days

# ==========================================
# WORKFLOW SCREEN A: SAAS AGREEMENT GATEWAY
# ==========================================
if not saas_accepted:
    st.title("🚧 Welcome to GateOps Pro")
    st.subheader("Software Setup & End User License Agreement")
    st.info("Before establishing your installation account and launching your 14-day free trial, please review and accept our SaaS Subscription Terms.")
    
    with st.expander("📄 CLICK HERE TO READ THE FULL SAAS SERVICE & LICENSE AGREEMENT", expanded=True):
        st.markdown("""
        ### GATEOPS PRO – SOFTWARE AS A SERVICE (SaaS) AGREEMENT
        
        **1. License & Scope of Service**
        Provider grants Subscriber a non-exclusive, non-transferable, revocable right to access and use the GateOps Pro application solely for Subscriber’s internal business operations (managing customers, contracts, dispatches, and safety checklists).
        
        **2. Free Trial & Subscription Terms**
        * **2.1 14-Day Free Trial:** The software is initially configured on a trial basis free of charge for 14 calendar days.
        * **2.2 Data Erasure:** ANY DATA ENTERED INTO THE SOFTWARE DURING THE 14-DAY FREE TRIAL WILL BE PERMANENTLY LOST UNLESS SUBSCRIBER PURCHASES A DOWNSTREAM PAID SUBSCRIPTION PRIOR TO THE EXPIRATION OF THE TRIAL PERIOD.
        
        **3. Subscriber Responsibilities & Data**
        * **3.1 Field Connectivity:** Subscriber acknowledges that the Software requires an active cellular data or internet connection for field deployment. Provider is not responsible for a technician's inability to submit UL 325 PM checklists due to lack of local signal.
        
        **4. Intellectual Property & Code Protection**
        * Subscriber shall not reverse engineer, decompile, or attempt to extract the source code of the Software or build a competitive product using similar features.
        
        **5. Disclaimer of Warranties & UL 325 Compliance Liability**
        * **5.1 Technical Compliance Disclaimer:** While the Software provides interactive "UL 325 Compliance Checklists" for field convenience, the accurate physical execution of these safety tests remains the sole responsibility of Subscriber and its technicians.
        
        **6. Limitation of Liability**
        IN NO EVENT SHALL THE PROVIDER BE LIABLE FOR ANY CONSEQUENTIAL, INDIRECT, INCIDENTAL, OR PUNITIVE DAMAGES (INCLUDING LOSS OF BUSINESS PROFITS, DATA LOGS, OR UNLOGGED PROPERTY DAMAGE CLAIMS) ARISING OUT OF THE USE OF THE SOFTWARE.
        """)
    
    with st.form("saas_acceptance_form"):
        agree_check = st.checkbox("I accept all the terms, conditions, and liability disclaimers of the GateOps Pro SaaS Agreement, including the 14-day trial limitations.")
        submit_acceptance = st.form_submit_button("Confirm & Activate Dashboard")
        
        if submit_acceptance:
            if agree_check:
                with get_db_connection() as conn:
                    conn.execute("UPDATE app_settings SET saas_accepted = 1 WHERE id = 1")
                    conn.commit()
                st.success("Agreement accepted successfully! Reloading system...")
                st.rerun()
            else:
                st.error("You must click the check-box accepting the terms before accessing the software dashboard.")
    st.stop()

# ==========================================
# WORKFLOW SCREEN B: CORE DASHBOARD SUITE
# ==========================================

# Check Trial Expiration Window
if days_remaining < 0:
    st.title("🔒 Access Suspended - Trial Expired")
    st.error(f"Your 14-day free trial expired on {trial_end}. To reactivate your account and secure your existing database, please subscribe below.")
    st.link_button("🚀 Upgrade to Pro Account ($99/mo)", "https://buy.stripe.com/your_stripe_link")
    st.stop()

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.title("💳 Subscription Management")
st.sidebar.info(f"🗓️ **Account Status:** 14-Day Free Trial\n\n**Days Left:** {max(0, days_remaining)} Days Remaining")
st.sidebar.markdown("---")
st.sidebar.write("Upgrade anytime to prevent database lockouts or data erasure at the end of your 14-day window.")
st.sidebar.link_button("🚀 Go Pro ($99/mo)", "https://buy.stripe.com/your_stripe_link")

# --- CENTRAL APP HEADER ---
st.title("🚧 GateOps Pro Dashboard")
st.subheader("Field Service, Contract Automation & UL 325 Compliance")
st.markdown("---")

# Global Customer Lookup cache initialization
with get_db_connection() as conn:
    global_customers = conn.execute("SELECT id, name FROM customers ORDER BY name ASC").fetchall()
customer_map = {cust["name"]: cust["id"] for cust in global_customers} if global_customers else {}

# Define Tabs Architecture
tab1, tab2, tab3, tab4 = st.tabs([
    "👥 Customer Management", 
    "📜 Maintenance Contracts", 
    "📅 Service Dispatch Board", 
    "📋 UL 325 PM Compliance Checks"
])

# ==========================================
# TAB 1: CUSTOMER MANAGEMENT
# ==========================================
with tab1:
    st.header("Register New Customer Property")
    with st.form("add_customer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cust_name = st.text_input("Customer/Company Name (e.g., FedEx Hub 4)")
            cust_phone = st.text_input("Site Contact Phone")
        with col2:
            cust_email = st.text_input("Billing Email Address")
            cust_address = st.text_input("Physical Gate Operator Location (Address)")
        
        if st.form_submit_button("Save Customer Profile") and cust_name:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO customers (name, phone, email, address) VALUES (?, ?, ?, ?)",
                             (cust_name, cust_phone, cust_email, cust_address))
                conn.commit()
            st.success(f"Successfully recorded customer profile for '{cust_name}'.")
            st.rerun()

    st.markdown("### 📋 Active Customer Registry")
    if global_customers:
        with get_db_connection() as conn:
            st.dataframe(conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall(), use_container_width=True)
    else:
        st.info("No customers currently logged in system database.")

# ==========================================
# TAB 2: MAINTENANCE CONTRACTS
# ==========================================
with tab2:
    st.header("Issue Recurring Service Contract")
    if not global_customers:
        st.warning("You must enter a customer in Tab 1 before creating a service agreement.")
    else:
        with st.form("contract_form", clear_on_submit=True):
            selected_cust = st.selectbox("Link to Customer Profile", options=list(customer_map.keys()))
            contract_type = st.selectbox("Service Interval Type", ["Commercial Quarterly PM", "Commercial Semi-Annual", "Residential Annual"])
            duration_months = st.number_input("Agreement Term Length (Months)", min_value=1, max_value=36, value=12)
            price = st.number_input("Total Agreement Valuation ($)", min_value=0.0, value=1200.0)
            
            if st.form_submit_button("Activate Service Contract"):
                start_date = datetime.now().date()
                end_date = start_date + timedelta(days=duration_months * 30)
                with get_db_connection() as conn:
                    conn.execute('''
                        INSERT INTO contracts (customer_id, contract_type, start_date, end_date, price) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', (customer_map[selected_cust], contract_type, str(start_date), str(end_date), price))
                    conn.commit()
                st.success(f"Service Contract authorized for {selected_cust}. Valid through {end_date}.")

        st.markdown("### 📜 Executed Maintenance Agreements")
        with get_db_connection() as conn:
            active_contracts = conn.execute('''
                SELECT con.id, cust.name as customer_name, con.contract_type, con.start_date, con.end_date, con.price 
                FROM contracts con JOIN customers cust ON con.customer_id = cust.id ORDER BY con.id DESC
            ''').fetchall()
            if active_contracts: 
                st.dataframe(active_contracts, use_container_width=True)

# ==========================================
# TAB 3: SERVICE DISPATCH BOARD
# ==========================================
with tab3:
    st.header("Create Service Ticket / Dispatch Directive")
    if not global_customers:
        st.warning("You must have active records in the customer registry to run dispatch operations.")
    else:
        with st.form("dispatch_form", clear_on_submit=True):
            selected_cust_dispatch = st.selectbox("Target Site Property", options=list(customer_map.keys()))
            tech = st.text_input("Assigned Service Technician")
            sched_date = st.date_input("Target Service Window Date", datetime.now().date())
            issue = st.text_area("Scope of Maintenance Call / Reported Malfunction Description")
            status = st.selectbox("Dispatch Routing Status", ["Pending", "In Progress", "Completed"])
            
            if st.form_submit_button("Log & Route Dispatch Ticket"):
                with get_db_connection() as conn:
                    conn.execute('''
                        INSERT INTO dispatches (customer_id, technician, scheduled_date, issue_description, status) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', (customer_map[selected_cust_dispatch], tech, str(sched_date), issue, status))
                    conn.commit()
                st.success("Dispatch instruction successfully pushed onto the service board schedule.")
                st.rerun()

        st.markdown("### 📅 Active Service Schedule Board")
        with get_db_connection() as conn:
            active_dispatches = conn.execute('''
                SELECT d.id, c.name as customer_name, d.technician, d.scheduled_date, d.issue_description, d.status 
                FROM dispatches d JOIN customers c ON d.customer_id = c.id 
                WHERE d.status != "Completed" ORDER BY d.scheduled_date ASC
            ''').fetchall()
            if active_dispatches: 
                st.dataframe(active_dispatches, use_container_width=True)
            else:
                st.info("No active pending or in-progress maintenance visits registered for today.")

# ==========================================
# TAB 4: UL 325 PM COMPLIANCE CHECKS & RECEIPT GENERATOR
# ==========================================
with tab4:
    st.header("📋 Technical PM Checklist (UL 325 Safety Standards)")
    st.caption("Technicians field deployed on property sites use this checklist system to execute safety sweeps and confirm legal safety operations.")
    
    with get_db_connection() as conn:
        active_jobs = conn.execute('''
            SELECT d.id, c.name, d.scheduled_date 
            FROM dispatches d JOIN customers c ON d.customer_id = c.id
            WHERE d.status != "Completed"
        ''').fetchall()
    
    if not active_jobs:
        st.info("No unresolved active service tickets found to submit safety checklist sweeps for.")
    else:
        job_options = {f"Ticket #{j['id']} - Account: {j['name']} ({j['scheduled_date']})": j["id"] for j in active_jobs}
        selected_job = st.selectbox("Target Service Ticket Identifier", options=list(job_options.keys()))
        
        st.markdown("---")
        st.markdown("#### Safety Mechanism Physical Function Interactivity")
        
        with st.form("pm_checklist_form", clear_on_submit=True):
            pe = st.checkbox("Photo-Electric Eyes: Obstruction detection signals loop reversals properly and mechanisms align.")
            loops = st.checkbox("Underground Vehicle Inductive Loops: Safety, shadow, and free-exit sensors track vehicle dynamics.")
            edges = st.checkbox("Safety Contact Edges: Impact arrays immediately interrupt physical drive logic on gate impact.")
            hardware = st.checkbox("Mechanical Infrastructure: Chains tensioned, rollers greased, hinge alignment verified, brackets stable.")
            
            tech_notes = st.text_area("Field Assessment Comments / Recommended Mandatory Infrastructure Upgrades")
            
            if st.form_submit_button("Verify Safety Sweep Compliance & Submit Report"):
                with get_db_connection() as conn:
                    # Log safety answers
                    conn.execute('''
                        INSERT INTO pm_checklists (dispatch_id, photo_eyes_pass, loop_detectors_pass, edge_sensors_pass, gate_hardware_pass, technician_notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (job_options[selected_job], int(pe), int(loops), int(edges), int(hardware), tech_notes))
                    
                    # Complete ticket automatically
                    conn.execute('UPDATE dispatches SET status = "Completed" WHERE id = ?', (job_options[selected_job],))
                    conn.commit()
                st.success("✅ Legal safety log archived. Corresponding dispatch entry marked 'Completed'.")
                st.rerun()

        st.markdown("---")
        st.markdown("### 📜 Safety Inspection Historical Database & Printout Generator")
        st.caption("Expand a finished historical row to view checklist details or generate a printable client receipt text file.")
        
        with get_db_connection() as conn:
            history = conn.execute('''
                SELECT pm.id, c.name as client, pm.photo_eyes_pass as photo_eyes, pm.loop_detectors_pass as loop_detectors, 
                       pm.edge_sensors_pass as safety_edges, pm.gate_hardware_pass as mechanical, pm.technician_notes as comments
                FROM pm_checklists pm
                JOIN dispatches d ON pm.dispatch_id = d.id
                JOIN customers c ON d.customer_id = c.id ORDER BY pm.id DESC
            ''').fetchall()
        
               if history:
            for record in history:
                # Convert SQLite Row objects explicitly to dict keys to prevent rendering bugs
                rec_id = record['id']
                rec_client = record['client']
                rec_pe = record['photo_eyes']
                rec_loops = record['loop_detectors']
                rec_edges = record['safety_edges']
                rec_mech = record['mechanical']
                rec_comments = record['comments']

                with st.expander(f"📄 Inspection Summary - Client: {rec_client} (ID: #{rec_id})"):
                    col_view, col_action = st.columns([4, 1])
                    
                    with col_view:
                        st.write(f"**Photo-Electric Eyes Check:** {'✅ PASS' if rec_pe else '❌ FAIL / NOT TESTED'}")
                        st.write(f"**Vehicle Loop Detectors Check:** {'✅ PASS' if rec_loops else '❌ FAIL / NOT TESTED'}")
                        st.write(f"**Safety Edge Arrays Check:** {'✅ PASS' if rec_edges else '❌ FAIL / NOT TESTED'}")
                        st.write(f"**Mechanical Hardware Review:** {'✅ PASS' if rec_mech else '❌ FAIL / NOT TESTED'}")
                        st.write(f"**Technician Notes:** *{rec_comments}*")
                    
                    with col_action:
                        # Construct a beautifully aligned text receipt layout
                        receipt_text = f"""==================================================
              GATEOPS PRO - SERVICE RECEIPT       
==================================================
Property / Client: {rec_client}
Safety Inspection Log ID: #{rec_id}
Date Generated: {datetime.now().strftime('%Y-%m-%d')}
--------------------------------------------------
UL 325 COMPLIANCE SAFETY TESTING AUDIT:

[{"X" if rec_pe else " "}] Photo-Electric Eyes Alignment & Reverse Test
[{"X" if rec_loops else " "}] Vehicle Inductive Ground Loop System Test
[{"X" if rec_edges else " "}] Contact Safety Edge Reversal Sensor Test
[{"X" if rec_mech else " "}] Mechanical Drive Chain & Hardware Structural Test

--------------------------------------------------
FIELD SERVICE TECHNICIAN SUMMARY NOTES:
{rec_comments}
--------------------------------------------------
Thank you for executing routine compliance maintenance agreements!
==================================================
"""
                        # Export button layout with distinct string identity hashes
                        st.download_button(
                            label="📥 Export Receipt",
                            data=receipt_text,
                            file_name=f"Service_Receipt_Log_{rec_id}_{rec_client.replace(' ', '_')}.txt",
                            mime="text/plain",
                            key=f"dl_btn_secure_{rec_id}"
                        )
        else:
            st.info("No compiled testing history records found in the local file database.")

