import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import uuid
import os
import urllib.parse
import streamlit.components.v1 as components

# ==========================================
# DEMO MODE BANNER + SESSION-ISOLATED DATABASE
# ==========================================

def show_demo_banner():
    st.markdown(
        """
        <div class="no-print" style="
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
            background-color: #ffffff !important;
            color: #111111 !important;
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
            st.dataframe(prop_df, use_container_width=True, hide_index=True)
            
            st.markdown("### 🖋️ Live Review, Edit & Output Processing Module")
            selected_prop_id = st.selectbox("Select Active Document Target Reference ID", options=prop_df["id"].tolist())
            
            target_row = prop_df[prop_df["id"] == selected_prop_id].iloc[0]
            
            st.markdown("#### 🔄 Real-Time Negotiation Override Form")
            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                edit_scope = st.text_area("Modify Working Scope Paragraph", value=target_row["scope_of_work"])
            with col_ed2:
                edit_price = st.number_input("Override Pricing Threshold Matrix Base ($)", value=float(target_row["base_pricing"]))
                
            if st.button("Save Contract Amendments"):
                with get_connection() as conn:
                    new_gross = edit_price * (1 + (new_fee / 100))
                    conn.execute("UPDATE proposals SET scope_of_work = ?, base_pricing = ?, total_with_fees = ? WHERE id = ?", (edit_scope, edit_price, new_gross, selected_prop_id))
                    conn.commit()
                st.success("Amendments updated inside active data pools!")
                st.rerun()

            st.markdown("---")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                decision_state = st.radio("Client Execution Decision Target State", ["Accepted - Pass to Dispatch Routing", "Declined - Clear Record Reference"])
                printed_sig_name = st.text_input("Authorized Approver Printed Full Signature Name")
                signature_confirm = st.checkbox("Signee digital authentication check validation pattern.")
            with col_d2:
                st.markdown("#### 🖨️ Document Output Simulator Console")
                
                logo_emoji = "🛡️" if "Shield" in target_row["logo_name"] else ("👑" if "Gold" in target_row["logo_name"] else "⚜️")
                
                html_preview = f"""
                <div class="report-box">
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <h2>{logo_emoji} {target_row['logo_name'].upper()}</h2>
                        <h4 style='color:#666;'>PREVENTIVE MAINTENANCE PROPOSAL</h4>
                    </div>
                    <hr>
                    <p><b>Prepared For:</b> {target_row['customer_name']}</p>
                    <p><b>Itemized System Units:</b> {target_row['itemized_layouts']}</p>
                    <p><b>Included Safe Accessories Trailing Array:</b> {target_row['accessories_list']}</p>
                    <p><b>Binding Structural Scope of Work Elements:</b> <br><i>{target_row['scope_of_work']}</i></p>
                    <hr>
                    <h3>Total Investment Summary Net Value: ${target_row['base_pricing']:.2f}</h3>
                    <h4>Gross Total (with Credit Card Transaction Processing Surcharge): ${target_row['total_with_fees']:.2f}</h4>
                </div>
                """
                st.markdown(html_preview, unsafe_allow_html=True)
                
                st.download_button(
                    label="📧 Dispatch Document Stream via Local E-Mail/Print System Wrapper",
                    data=f"Proposal ID: {selected_prop_id}\nLogo: {target_row['logo_name']}\nClient: {target_row['customer_name']}\nScope: {target_row['scope_of_work']}\nTotal Due: ${target_row['total_with_fees']:.2f}",
                    file_name=f"GateOps_Professional_Proposal_{selected_prop_id}.txt",
                    mime="text/plain"
                )
                
            if st.button("Commit Document Phase State Update"):
                if decision_state == "Accepted - Pass to Dispatch Routing":
                    if not printed_sig_name or not signature_confirm:
                        st.error("Authentication confirmation logs missing.")
                    else:
                        with get_connection() as conn:
                            conn.execute("UPDATE proposals SET status = 'Accepted' WHERE id = ?", (selected_prop_id,))
                            conn.execute(
                                "INSERT INTO dispatches (proposal_id, customer_id, client_signature, status) VALUES (?, ?, ?, 'Scheduled')",
                                (selected_prop_id, int(target_row["customer_id"]), printed_sig_name)
                            )
                            conn.commit()
                        st.success("Closing execution approved! Task parameters passed onward to tracking calendars.")
                        st.rerun()
                else:
                    with get_connection() as conn:
                        conn.execute("UPDATE proposals SET status = 'Declined' WHERE id = ?", (selected_prop_id,))
                        conn.commit()
                    st.rerun()

# ------------------------------------------
# TAB 3: DISPATCH & SCHEDULING
# ------------------------------------------
with tab3:
    if tier_level < 2:
        st.markdown("## 🔒 Unlock Crew Dispatch & Route Management")
        st.link_button("🚀 Step up to Ops Commander for +$100/mo", "https://yourbillingportal.com/upgrade")
    else:
        st.header("Fleet Coordination Dispatch Board")
        
        with get_connection() as conn:
            calendar_query_df = pd.read_sql_query("SELECT schedule_date, technician_crew FROM dispatches WHERE status != 'Completed' AND schedule_date IS NOT NULL", conn)
        
        st.subheader("📅 Active Field Commitments Calendar Queue")
        st.caption("Real-Time Structural Month-to-Month Schedule Map Grid (Conflict Mitigation Engine)")
        
        scheduled_dates_set = set(calendar_query_df["schedule_date"].tolist())
        
        base_date = datetime.now()
        months_to_display = [0, 1, 2]
        
        c_cols = st.columns(3)
        for idx, m_offset in enumerate(months_to_display):
            with c_cols[idx]:
                target_month_date = base_date + timedelta(days=30 * m_offset)
                m_num = target_month_date.month
                y_num = target_month_date.year
                
                st.markdown(f"##### 📆 {target_month_date.strftime('%B %Y')}")
                
                day_buttons_html = "<div style='display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; text-align: center; font-size:11px;'>"
                days_labels = ["S","M","T","W","T","F","S"]
                for dl in days_labels:
                    day_buttons_html += f"<div style='font-weight:bold; color:#777;'>{dl}</div>"
                    
                for d_idx in range(1, 32):
                    test_str = f"{y_num}-{m_num:02d}-{d_idx:02d}"
                    if test_str in scheduled_dates_set:
                        day_buttons_html += f"<div style='background-color:#FF4B4B; color:white; font-weight:bold; border-radius:4px; padding:2px;' title='Conflict Lock: Job Appointed'>{d_idx}</div>"
                    else:
                        day_buttons_html += f"<div style='background-color:#e0e0e0; color:#333; border-radius:4px; padding:2px;'>{d_idx}</div>"
                day_buttons_html += "</div>"
                st.markdown(day_buttons_html, unsafe_allow_html=True)
                
        st.markdown("---")
        
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
                
                st.markdown("##### Assign Field Technician / Installation Crew Unit")
                selected_dropdown_crew = st.selectbox(
                    "Choose from registered tech profiles:", 
                    options=["-- Use Custom Entry Typed Below --"] + st.session_state.tech_crews
                )
                custom_crew_text = st.text_input(
                    "Or type / edit custom dispatcher name details right here:", 
                    value="",
                    placeholder="e.g., Tech Miller & Apprentice J."
                )
                
                target_date = st.date_input("Scheduled Field Deployment Targeting Date")
                
                if st.form_submit_button("Route Team and Deploy Ticket"):
                    if selected_dropdown_crew == "-- Use Custom Entry Typed Below --":
                        final_crew_identity = custom_crew_text.strip()
                    else:
                        final_crew_identity = selected_dropdown_crew
                        
                    if not final_crew_identity:
                        st.error("Please select a valid team identity or type a custom assignment into the field terminal framework.")
                    else:
                        chosen_date_str = target_date.strftime("%Y-%m-%d")
                        
                        if chosen_date_str in scheduled_dates_set:
                            st.warning(f"⚠️ Schedule Conflict Alert: Another crew asset is already deployed on the date {chosen_date_str}. Review schedules before committing.")
                            
                        with get_connection() as conn:
                            conn.execute(
                                "UPDATE dispatches SET technician_crew = ?, schedule_date = ?, status = 'En Route' WHERE id = ?",
                                (final_crew_identity, chosen_date_str, ticket_map[target_ticket])
                            )
                            conn.commit()
                        st.success(f"Successfully matched and deployed work parameters to: {final_crew_identity}!")
                        st.rerun()

# ------------------------------------------
# TAB 4: COMPLIANCE CHECKS & DIGITAL WORK ORDERS
# ------------------------------------------
with tab4:
    if tier_level < 2:
        st.markdown("## 🔒 Unlock Mobile Field Terminal Handouts")
    else:
        st.header("Mobile Field Service Terminal")
        with get_connection() as conn:
            field_active_tickets = conn.execute("""
                SELECT d.id, c.name, p.accessories_list, p.logo_name FROM dispatches d 
                JOIN customers c ON d.customer_id = c.id 
                JOIN proposals p ON d.proposal_id = p.id
                WHERE d.status IN ('En Route', 'Scheduled') AND d.technician_crew IS NOT NULL
            """).fetchall()
            
        if not field_active_tickets:
            st.info("No active work dispatches are currently marked in open execution fields.")
        else:
            field_ticket_map = {f"Ticket #{row['id']} for {row['name']}": row['id'] for row in field_active_tickets}
            selected_field_id = st.selectbox("Select Active Property Arrival Ticket Target", options=list(field_ticket_map.keys()))
            
            active_ticket_row = [r for r in field_active_tickets if r["id"] == field_ticket_map[selected_field_id]][0]
            
            st.markdown("---")
            if tier_level < 3:
                st.markdown("### 🔒 Protect Your Business with UL 325 Safety Verification Matrices")
                st.link_button("🚀 Unlock Enterprise Compliance for +$200/mo", "https://yourbillingportal.com/upgrade")
                
                with st.form("basic_work_order_closure"):
                    t_id = field_ticket_map[selected_field_id]
                    basic_notes = st.text_area("On-Site Work Summary Progress Notes")
                    if st.form_submit_button("Close Job Ticket (Basic)"):
                        with get_connection() as conn:
                            conn.execute("UPDATE dispatches SET status = 'Completed', technician_notes = ? WHERE id = ?", (basic_notes, t_id))
                            conn.commit()
                        st.rerun()
            else:
                st.subheader("📋 Enforced Safety Compliance Point Checks")
                st.caption("Standardized UL 325 & ASTM F2200 Hardware Testing Console")
                
                with st.form("safety_audit_submission_form"):
                    t_id = field_ticket_map[selected_field_id]
                    serial_no = st.text_input("Gate Operator System Serial Number (For Historical Records)")
                    
                    col_chk1, col_chk2 = st.columns(2)
                    with col_chk1:
                        pe_check = st.checkbox("Photo-Eye Interruption Test: Beam break stops & completely reverses gate travel.")
                        loop_check = st.checkbox("Inductive Loop Matrix Check: Ground coils maintain loop presence hold calls safely.")
                    with col_chk2:
                        edge_check = st.checkbox("Safety Obstruction Edge Test: Contact impact strips activate safety reverse limits instantly.")
                        hw_check = st.checkbox("Mechanical Hardware Integrity: Drive tracking alignment, sprockets, and chains certified.")
                        
                    st.markdown("##### 🔍 Project Scope Accessory Integrity Verification Checklist")
                    st.info(f"The structural contract scope required validation verification for: **{active_ticket_row['accessories_list']}**")
                    
                    parsed_accessories = [a.strip() for a in active_ticket_row['accessories_list'].split(",") if a.strip()]
                    if parsed_accessories:
                        for idx, accessory_item in enumerate(parsed_accessories):
                            st.checkbox(f"Verify Accessory Deployment Diagnostics Status Item: [{accessory_item}] functional pass parameters verified.", key=f"scope_item_{idx}")
                    else:
                        st.caption("*No secondary auxiliary elements were mapped into this contract scope layout profile.*")
                        
                    tech_comments = st.text_area("On-Site Service Engineering Progress Logs & Repair Text Entries")
                    tech_sig = st.text_input("Lead Certified Installer/Technician Name Signature Block")
                    cust_sig_verify = st.text_input("Property Representative/Site Authority Acceptance Name")
                        
                    if st.form_submit_button("Lock Diagnostics & Issue Professional Verification Certificate Report"):
                        if not serial_no or not tech_sig or not cust_sig_verify:
                            st.error("Hardware Serial Number mapping parameters and execution signatures are required to compile professional receipts.")
                        else:
                            with get_connection() as conn:
                                conn.execute("""
                                    UPDATE dispatches 
                                    SET status = 'Completed', photo_eyes_pass = ?, loops_pass = ?, 
                                        edges_pass = ?, hardware_pass = ?, technician_notes = ? , serial_number = ?
                                    WHERE id = ?
                                """, (1 if pe_check else 0, 1 if loop_check else 0, 1 if edge_check else 0, 1 if hw_check else 0, tech_comments, serial_no, t_id))
                                conn.commit()
                            st.success("Compliance diagnostics cataloged permanently!")
                            st.rerun()

        # ==========================================
        # UPGRADED PRINT ENGINE & EMAIL DATA STREAM
        # ==========================================
        st.markdown("---")
        st.subheader("📜 Professional Field Completion Receipt Records Archive")
        with get_connection() as conn:
            completed_history_df = pd.read_sql_query("""
                SELECT d.id as ticket_id, c.name as location, c.email as client_email, d.serial_number, d.schedule_date, 
                       d.photo_eyes_pass, d.loops_pass, d.edges_pass, d.hardware_pass, 
                       d.technician_notes, p.total_with_fees, p.logo_name, p.accessories_list
                FROM dispatches d JOIN customers c ON d.customer_id = c.id 
                JOIN proposals p ON d.proposal_id = p.id WHERE d.status = 'Completed'
            """, conn)
            
        if not completed_history_df.empty:
            st.dataframe(completed_history_df, use_container_width=True, hide_index=True)
            target_receipt_id = st.selectbox("Select Target Handout Report Profile ID", options=completed_history_df["ticket_id"].tolist())
