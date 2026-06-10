import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE ENGINE & SYSTEM INTENT INITIALIZATION
# ==========================================
st.set_page_config(
    page_title="GateOps Pro - Enterprise Workspace",
    page_icon="🚧",
    layout="wide"
)

# ==========================================
# 2. THREAD-SAFE DATABASE CONFIGURATION
# ==========================================
def get_db_connection():
    """Generates an isolated, thread-safe local file connection factory."""
    conn = sqlite3.connect("gateops_enterprise_production.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_database_schema():
    """Compiles all required tables matching the operational blueprint."""
    with get_db_connection() as conn:
        # App System Configuration Profile
        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_fee_percentage REAL DEFAULT 3.0,
                company_name TEXT DEFAULT 'GateOps Pro Installers'
            )
        ''')
        # Customers Table (with Soft Delete integration)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, phone TEXT, email TEXT, address TEXT,
                notes TEXT, is_active INTEGER DEFAULT 1
            )
        ''')
        # Proposals Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER,
                operator_type TEXT, accessories_list TEXT, scope_of_work TEXT,
                base_pricing REAL, total_with_fees REAL, status TEXT DEFAULT 'Pending',
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        # Work Orders / Active Dispatches Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS dispatches (
                id INTEGER PRIMARY KEY AUTOINCREMENT, proposal_id INTEGER,
                customer_id INTEGER, technician_crew TEXT, schedule_date TEXT,
                status TEXT DEFAULT 'Scheduled', client_signature TEXT,
                photo_eyes_pass INTEGER DEFAULT 0, loops_pass INTEGER DEFAULT 0,
                edges_pass INTEGER DEFAULT 0, hardware_pass INTEGER DEFAULT 0,
                tech_notes TEXT, serial_number TEXT,
                FOREIGN KEY (proposal_id) REFERENCES proposals (id),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Populate default settings row if completely fresh build
        check = conn.execute("SELECT COUNT(*) as count FROM system_settings").fetchone()
        if check["count"] == 0:
            conn.execute("INSERT INTO system_settings (card_fee_percentage) VALUES (3.0)")
        conn.commit()

# Execute structural database build
init_database_schema()

# ==========================================
# 3. GLOBAL WORKSPACE SETTINGS CACHING
# ==========================================
with get_db_connection() as conn:
    settings_row = conn.execute("SELECT * FROM system_settings WHERE id = 1").fetchone()
    current_fee_rate = settings_row["card_fee_percentage"]

# ==========================================
# 4. DASHBOARD SIDEBAR CORE ENGINE
# ==========================================
st.sidebar.title("⚙️ Workspace Controls")
st.sidebar.markdown("---")
st.sidebar.subheader("Credit Card Fee Surcharge")
new_fee = st.sidebar.number_input(
    "Set Customer Card Processing Fee (%)", 
    min_value=0.0, max_value=6.0, value=current_fee_rate, step=0.1
)

if new_fee != current_fee_rate:
    with get_db_connection() as conn:
        conn.execute("UPDATE system_settings SET card_fee_percentage = ? WHERE id = 1", (new_fee,))
        conn.commit()
    st.sidebar.success(f"Fee updated to {new_fee}% globally!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 Pro Tip: Passing processing surcharges directly to commercial clients can save your business thousands of dollars in annual merchant account swipe fees.")

# ==========================================
# 5. CORE INTERFACE LAYOUT MODULES
# ==========================================
st.title("🚧 GateOps Pro Enterprise Suite")
st.write("Complete Automated Operational Pipeline Framework")

# Generate the Blueprint Navigation Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👥 Client Intake & Directory", 
    "📄 Proposal Builder Engine", 
    "📅 Dispatch & Scheduling", 
    "📋 Compliance Checks & Work Orders", 
    "📊 Executive Performance Analytics"
])

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
                    with get_db_connection() as conn:
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
        with get_db_connection() as conn:
            # Query active customers only (Soft Delete filtering layer)
            active_df = pd.read_sql_query("SELECT id, name, phone, email, address, notes FROM customers WHERE is_active = 1", conn)
        
        if not active_df.empty:
            st.dataframe(active_df, use_container_width=True, hide_index=True)
            
            # Soft Delete Interactive Section
            st.markdown("---")
            st.subheader("🚫 Deactivate & Archive Property File")
            archive_map = dict(zip(active_df["name"], active_df["id"]))
            target_archive = st.selectbox("Select property profile to safely archive:", options=list(archive_map.keys()))
            
            if st.button("Archive Profile Row", type="primary"):
                with get_db_connection() as conn:
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
    
    with get_db_connection() as conn:
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
                accessories = st.multiselect("Select Integrated UL 325 Safety Infrastructure Components", [
                    "Monitored Reflective Retro Photo-Eye Beam Kit",
                    "Pre-Formed Inductive Ground Loop Coils (Shadow/Exit Matrices)",
                    "Four-Wire Resistive Contact Safety Pressure Edge Trim",
                    "Wireless Access Proximity Credentials Card Reader Base"
                ])
                base_cost = st.number_input("Base Component Layout & Labor Quoted Price ($)", min_value=0.0, value=2500.0)
                
            if st.form_submit_button("Generate Complete Client Estimate Proposal"):
                # Handle processing fee calculation loops matching settings metrics
                percentage_multiplier = 1 + (new_fee / 100)
                gross_calculated_total = base_cost * percentage_multiplier
                acc_string = ", ".join(accessories)
                
                with get_db_connection() as conn:
                    conn.execute(
                        "INSERT INTO proposals (customer_id, operator_type, accessories_list, scope_of_work, base_pricing, total_with_fees) VALUES (?, ?, ?, ?, ?, ?)",
                        (cust_dict[target_cust], op_type, acc_string, scope, base_cost, gross_calculated_total)
                    )
                    conn.commit()
                st.success("Proposal parameters compiled successfully.")
                st.rerun()

        st.markdown("---")
        st.subheader("📋 Active Field Proposals Queue")
        with get_db_connection() as conn:
            proposals_query = """
                SELECT p.id, c.name as customer_name, p.operator_type, p.base_pricing, p.total_with_fees, p.status 
                FROM proposals p JOIN customers c ON p.customer_id = c.id WHERE c.is_active = 1
            """
            prop_df = pd.read_sql_query(proposals_query, conn)
            
        if not prop_df.empty:
            st.dataframe(prop_df, use_container_width=True, hide_index=True)
            
            # Decision Handling Block
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
                        with get_db_connection() as conn:
                            # Update statement status
                            conn.execute("UPDATE proposals SET status = 'Accepted' WHERE id = ?", (selected_prop_id,))
                            # Grab related user fields to auto-create work dispatch ticket downstream
                            prop_details = conn.execute("SELECT customer_id FROM proposals WHERE id = ?", (selected_prop_id,)).fetchone()
                            conn.execute(
                                "INSERT INTO dispatches (proposal_id, customer_id, client_signature, status) VALUES (?, ?, ?, 'Scheduled')",
                                (selected_prop_id, prop_details["customer_id"], printed_sig_name)
                            )
                            conn.commit()
                        st.success("Closing execution approved! Work ticket routed onto scheduling tracking boards.")
                        st.rerun()
                else:
                    with get_db_connection() as conn:
                        conn.execute("UPDATE proposals SET status = 'Declined' WHERE id = ?", (selected_prop_id,))
                        conn.commit()
                    st.warning("Proposal marked Declined and cleared from primary action pathways.")
                    st.rerun()

# ------------------------------------------
# TAB 3: DISPATCH & SCHEDULING BOARD
# ------------------------------------------
with tab3:
    st.header("Fleet Coordination Dispatch Board")
    
    with get_db_connection() as conn:
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
                with get_db_connection() as conn:
                    conn.execute(
                        "UPDATE dispatches SET technician_crew = ?, schedule_date = ?, status = 'En Route' WHERE id = ?",
                        (crew_assignment, target_date.strftime("%Y-%m-%d"), ticket_map[target_ticket])
                    )
                    conn.commit()
                st.success("Crew asset matched. Active dispatch tickets forwarded to mobile truck arrays.")
                st.rerun()

    st.markdown("---")
    st.subheader("📅 Active Field Commitments Calendar Queue")
    with get_db_connection() as conn:
        active_schedule_df = pd.read_sql_query("""
            SELECT d.id as ticket_id, c.name as customer, c.address, d.technician_crew, d.schedule_date, d.status 
            FROM dispatches d JOIN customers c ON d.customer_id = c.id WHERE d.status != 'Completed'
        """, conn)
    if not active_schedule_df.empty:
        st.dataframe(active_schedule_df, use_container_width=True, hide_index=True)
    else:
        st.write("No active pending crew dispatches currently deployed in field execution states.")

# ------------------------------------------
# TAB 4: COMPLIANCE CHECKS & DIGITAL WORK ORDERS
# ------------------------------------------
with tab4:
    st.header("Mobile Field Service Terminal")
    st.caption("Standardized UL 325 & ASTM F2200 Hardware Testing Console")
    
    with get_db_connection() as conn:
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
        st.subheader("📋 Enforced Safety Compliance Point Checks")
        
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
                    with get_db_connection() as conn:
                        conn.execute("""
                            UPDATE dispatches 
                            SET status = 'Completed', photo_eyes_pass = ?, loop_detectors_pass = ?, 
                                edge_sensors_pass = ?, gate_hardware_pass = ?, technician_notes = ?, 
                                serial_number = ? 
                            WHERE id = ?
                        """, (
                            1 if pe_check else 0, 1 if loop_check else 0,
                            1 if edge_check else 0, 1 if hw_check else 0,
                            tech_comments, serial_no, t_id
                        ))
                        conn.commit()
                    st.success("Compliance diagnostics cataloged permanently inside site history parameters! System receipt print-out streams generated below.")
                    st.rerun()

    # ==========================================
    # WORK ORDER COMPLIANCE HISTORY ARCHIVE
    # ==========================================
    st.markdown("---")
    st.subheader("📜 Historical Structural Compliance Log Files")
    with get_db_connection() as conn:
        history_df = pd.read_sql_query("""
            SELECT d.id as ticket_id, c.name as location, d.serial_number, d.schedule_date, 
                   d.photo_eyes_pass as photo_eyes, d.loop_detectors_pass as ground_loops, 
                   d.edge_sensors_pass as safety_edges, d.gate_hardware_pass as mechanics, 
                   d.technician_notes, p.total_with_fees as invoice_amt 
            FROM dispatches d 
            JOIN customers c ON d.customer_id = c.id 
            JOIN proposals p ON d.proposal_id = p.id 
            WHERE d.status = 'Completed'
        """, conn)
        
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True, hide_index=True)
        
        # Interactive Receipt Generator Module Tool
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
# TAB 5: EXECUTIVE PERFORMANCE ANALYTICS
# ------------------------------------------
with tab5:
    st.header("Executive Board Performance Dash Analytics Dashboard")
    
    with get_db_connection() as conn:
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
        # Business Financial Performance Metric Cards Display
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
        with get_db_connection() as conn:
            chart_data_df = pd.read_sql_query("""
                SELECT c.name as customer_location, p.base_pricing as net_income, p.total_with_fees as gross_statement 
                FROM dispatches d 
                JOIN customers c ON d.customer_id = c.id 
                JOIN proposals p ON d.proposal_id = p.id 
                WHERE d.status = 'Completed'
            """, conn)
        
        if not chart_data_df.empty:
            st.bar_chart(chart_data_df, x="customer_location", y=["net_income", "gross_statement"], use_container_width=True)

