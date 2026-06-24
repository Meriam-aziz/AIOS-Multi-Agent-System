import os
import json
import folium
from streamlit_folium import st_folium
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from config import configure_gemini, EMERGENCY_SCENARIOS, SEVERITY_LEVELS
from orchestrator import WorkforceOrchestrator
from memory import WorkforceMemory

# Page setup
st.set_page_config(
    page_title="AIOS EOC Command | Emergency Response Swarm 🚨",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM DARK MODE CSS & PULSING ANIMATIONS ---
st.markdown("""
<style>
    /* Global EOC Theme */
    .stApp {
        background-color: #060B14;
        color: #E0E1DD;
        font-family: 'Inter', 'Roboto', sans-serif;
    }
    
    /* Top Header EOC Banner */
    .eoc-header {
        background: linear-gradient(135deg, #1A0505 0%, #060B14 100%);
        padding: 2.5rem;
        border-radius: 12px;
        border: 2px solid #D90429;
        box-shadow: 0 0 35px rgba(217, 4, 41, 0.5);
        margin-bottom: 2.5rem;
        position: relative;
        overflow: hidden;
    }
    .eoc-header::before {
        content: '🔴 LIVE AUTONOMOUS SWARM ACTIVE';
        position: absolute;
        top: 15px;
        right: 25px;
        font-size: 0.85rem;
        font-weight: 800;
        color: #FF0000;
        letter-spacing: 2px;
        animation: pulse-red 1.5s infinite;
    }
    @keyframes pulse-red {
        0% { opacity: 1; box-shadow: 0 0 10px #FF0000; }
        50% { opacity: 0.3; box-shadow: 0 0 20px #D90429; }
        100% { opacity: 1; box-shadow: 0 0 10px #FF0000; }
    }
    .eoc-header h1 {
        color: #FFFFFF;
        font-weight: 900;
        font-size: 3.2rem;
        letter-spacing: -1px;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px rgba(217, 4, 41, 0.9);
    }
    .eoc-header p {
        font-size: 1.25rem;
        color: #A0AEC0;
        font-weight: 500;
        margin: 0;
    }

    /* Severity Gauge Bar */
    .severity-banner {
        background: rgba(217, 4, 41, 0.15);
        border: 2px solid #D90429;
        padding: 1rem 2rem;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
        box-shadow: 0 0 25px rgba(217, 4, 41, 0.3);
    }
    .severity-title {
        font-size: 1.4rem;
        font-weight: 900;
        color: #FF1A1A;
        letter-spacing: 1.5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .severity-level-box {
        background: #D90429;
        color: #FFFFFF;
        padding: 6px 18px;
        border-radius: 4px;
        font-weight: 900;
        font-size: 1.2rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        border: 1px solid #FF0000;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.8);
    }
    
    /* Tactical Agent Cards */
    .tactical-card {
        background: rgba(12, 18, 30, 0.95);
        border: 1px solid #1C2B40;
        border-left: 8px solid #00FFFF;
        padding: 1.8rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .tactical-header {
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 900;
        font-size: 1.4rem;
        color: #00FFFF;
        margin-bottom: 1rem;
        border-bottom: 1px solid rgba(28, 43, 64, 0.8);
        padding-bottom: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .tactical-meta {
        background: rgba(0, 255, 255, 0.08);
        color: #00FFFF;
        font-size: 0.85rem;
        padding: 6px 14px;
        border-radius: 4px;
        font-weight: 700;
        margin-top: 14px;
        display: inline-block;
        border: 1px solid rgba(0, 255, 255, 0.4);
        letter-spacing: 1px;
    }
    
    /* Emergency Alert Box */
    .eas-alert {
        background: repeating-linear-gradient(
          45deg,
          #4A0000,
          #4A0000 20px,
          #2A0000 20px,
          #2A0000 40px
        );
        border: 4px solid #FF0000;
        padding: 2rem;
        border-radius: 8px;
        color: #FFFFFF;
        box-shadow: 0 0 40px rgba(255, 0, 0, 0.7);
        margin-top: 1rem;
        margin-bottom: 2rem;
    }
    .eas-header {
        font-size: 1.6rem;
        font-weight: 900;
        color: #FFFFFF;
        text-shadow: 0 0 10px #FF0000;
        letter-spacing: 2px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    /* KPI Boxes */
    .eoc-kpi {
        background: rgba(12, 18, 30, 0.95);
        border: 1px solid #1C2B40;
        padding: 1.8rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    }
    .kpi-label {
        font-size: 0.95rem;
        color: #8A9BAE;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 700;
    }
    .kpi-val {
        font-size: 2.6rem;
        font-weight: 900;
        color: #00FFFF;
        text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
        margin: 10px 0;
    }
    .kpi-val-red {
        font-size: 2.6rem;
        font-weight: 900;
        color: #FF1A1A;
        text-shadow: 0 0 15px rgba(217, 4, 41, 0.6);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "crisis_state" not in st.session_state:
    st.session_state.crisis_state = "idle"
if "crisis_logs" not in st.session_state:
    st.session_state.crisis_logs = []
if "logistics_metrics" not in st.session_state:
    st.session_state.logistics_metrics = {}
if "crisis_files" not in st.session_state:
    st.session_state.crisis_files = {}
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = WorkforceOrchestrator()

# Header Banner
st.markdown("""
<div class="eoc-header">
    <h1>🚨 MULTI-AGENT AUTONOMOUS EMERGENCY EOC SWARM</h1>
    <p>State-of-the-Art Crisis Command Center. 6 Elite First-Responder AI Agents collaborate in real-time to analyze chemical dispersion, calculate fleet logistics, issue Wireless Emergency Broadcasts, and compile official Incident Action Plans.</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("### 🛰️ EOC COMMAND CONSOLE")
    api_key_input = st.text_input("🔑 Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""), placeholder="AIzaSy...")
    if api_key_input:
        try:
            configure_gemini(api_key_input)
            st.success("🛰️ Secure EOC Link Verified!")
        except Exception as e:
            st.error(f"Link Error: {e}")
            
    st.markdown("---")
    st.markdown("### 🚨 INCIDENT SELECTION")
    scenario_choice = st.selectbox("Select Active Crisis Scenario", EMERGENCY_SCENARIOS, index=0)
    
    custom_incident = st.text_area("Or Input Custom Emergency Report", placeholder="e.g., Massive fire near industrial area with possible chemical leak...")
    
    incident_text = custom_incident if custom_incident.strip() else scenario_choice
    
    location_input = st.text_input("Primary Zone / Location", value="Cairo Industrial Zone (Sector 4)")
    hazard_cat = st.selectbox("Hazard Category", ["Industrial Chemical Leak ☣️", "Petrochemical Explosion 🔥", "High-Voltage Substation Fire ⚡", "Structural Tunnel Collapse ⚠️", "Severe Flood & Cyclone 🌪️"], index=0)
    
    st.markdown("---")
    st.markdown("### 🔴 THREAT SEVERITY & METRICS")
    sev_choice = st.selectbox("Assigned Threat Level", SEVERITY_LEVELS, index=0)
    # Map index 0 to Level 5, index 1 to Level 4, etc.
    sev_num = 5 - SEVERITY_LEVELS.index(sev_choice)
    
    radius_km = st.slider("Affected Threat Radius (km)", min_value=1.0, max_value=50.0, value=5.0, step=0.5)
    pop_density = st.slider("Population Density (people/sq km)", min_value=100, max_value=25000, value=8500, step=500)
    wind_speed = st.slider("Wind Dispersion Speed (km/h)", min_value=0.0, max_value=120.0, value=22.0, step=1.0)
    
    st.markdown("---")
    st.markdown("### 📂 HAZMAT RAG DATABASE")
    uploaded_file = st.file_uploader("Upload HAZMAT Safety Sheets / City Maps (PDF/TXT/CSV)", type=["pdf", "txt", "csv"])
    doc_text = ""
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".txt") or uploaded_file.name.endswith(".csv"):
            doc_text = uploaded_file.read().decode("utf-8")
            st.success(f"🛰️ Indexed {uploaded_file.name} successfully!")
        elif uploaded_file.name.endswith(".pdf"):
            try:
                import pypdf
                reader = pypdf.PdfReader(uploaded_file)
                doc_text = "\n".join([page.extract_text() for page in reader.pages])
                st.success(f"🛰️ Extracted tactical context from PDF!")
            except ImportError:
                st.warning("Install pypdf to read PDF directly, or upload .txt/.csv")
                
    st.markdown("---")
    execute_btn = st.button("🚨 ACTIVATE EMERGENCY SWARM 🚨", type="primary", use_container_width=True)

# --- EXECUTION TRIGGER ---
if execute_btn:
    if not api_key_input and not os.getenv("GEMINI_API_KEY"):
        st.error("⚠️ Please provide a Gemini API Key in the sidebar before executing.")
    else:
        st.session_state.crisis_state = "running"
        st.session_state.crisis_logs = []
        st.session_state.logistics_metrics = {}
        st.session_state.crisis_files = {}
        st.session_state.orchestrator = WorkforceOrchestrator()

# --- MAIN DASHBOARD TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛰️ LIVE TACTICAL SWARM", 
    "🗺️ FLEET & TRIAGE LOGISTICS", 
    "📢 PUBLIC EAS BROADCAST & SITREP", 
    "🛡️ SWARM WORKFLOW MATRIX",
    "ℹ️ ABOUT THIS SYSTEM"
])

# TAB 1: LIVE TACTICAL COORDINATION
with tab1:
    # Live Severity Bar
    st.markdown(f"""
    <div class="severity-banner">
        <div class="severity-title"><span>⚠️</span> INCIDENT SEVERITY LEVEL:</div>
        <div class="severity-level-box">LEVEL {sev_num} - {sev_choice.split(':')[1]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    status_container = st.empty()
    progress_bar = st.progress(0)
    spinner_container = st.empty()
    log_container = st.container()
    
    if st.session_state.crisis_state == "running":
        orch = st.session_state.orchestrator
        generator = orch.run_crisis_orchestration(
            incident_report=incident_text,
            location=location_input,
            severity_level=sev_num,
            affected_radius_km=radius_km,
            population_density=pop_density,
            wind_speed_kmh=wind_speed,
            hazard_type=hazard_cat,
            uploaded_doc_text=doc_text
        )
        
        step_idx = 0
        total_steps = 6
        
        icon_map = {
            "Commander": "🚨 Major Vance (Incident Commander)",
            "Risk": "🔍 Dr. Aris (HAZMAT Lead)",
            "Recon": "🚁 SkyEye-1 (Aerial Recon Unit)",
            "Resources": "🗺️ Captain Logan (Dispatch Master)",
            "Communication": "📢 Officer Sarah (Public Safety PIO)",
            "SITREP": "📊 Chief Riley (EOC Intelligence Lead)"
        }
        
        for step_title, agent_key, message, metadata in generator:
            step_idx += 1
            progress_pct = min(int((step_idx / total_steps) * 100), 100)
            progress_bar.progress(progress_pct)
            
            full_agent_name = icon_map.get(agent_key, f"🛰️ {agent_key}")
            status_container.info(f"🛰️ **TACTICAL PROTOCOL ACTIVE:** {step_title} (Current Executive: {full_agent_name})")
            
            # Show active thinking spinner
            with spinner_container:
                with st.spinner(f"🛰️ {full_agent_name} is actively calculating containment parameters and dispatch protocols... (~2 seconds)"):
                    time.sleep(1.5) # Cinematic pacing
                    
            # Save log entry
            log_item = {"step": step_title, "agent": full_agent_name, "msg": message, "meta": metadata}
            st.session_state.crisis_logs.append(log_item)
            
            # Update logistics metrics
            if metadata and "metrics" in metadata:
                st.session_state.logistics_metrics = metadata["metrics"]
            if metadata and "logistics_metrics" in metadata:
                st.session_state.logistics_metrics = metadata["logistics_metrics"]
                
            # Update files
            if metadata and "pdf_path" in metadata:
                st.session_state.crisis_files["pdf"] = metadata["pdf_path"]
            if metadata and "txt_path" in metadata:
                st.session_state.crisis_files["txt"] = metadata["txt_path"]
            if metadata and "audio_path" in metadata:
                st.session_state.crisis_files["audio_path"] = metadata["audio_path"]
                
            with log_container:
                meta_html = ""
                if metadata:
                    meta_html = f"<div class='tactical-meta'>🛰️ SECURE TOOL LINK ACTIVE: {metadata.get('tool_used', 'EOC Engine')}</div>"
                st.markdown(f"""
                <div class="tactical-card">
                    <div class="tactical-header"><span>{full_agent_name.split(' ')[0]}</span> {full_agent_name}</div>
                    <div style="white-space: pre-wrap; font-size: 1.15rem; line-height: 1.7; color: #E0E1DD;">{message}</div>
                    {meta_html}
                </div>
                """, unsafe_allow_html=True)
                
        spinner_container.empty()
        progress_bar.progress(100)
        status_container.success("🚨 EOC Tactical Protocols Complete! Official Incident Action Plan & SITREP compiled successfully.")
        st.session_state.crisis_state = "completed"
        
        # Emergency-themed completion — no balloons, this is a crisis system
        st.markdown("""
        <div style="
            background: repeating-linear-gradient(45deg, #1A0000, #1A0000 20px, #0D0000 20px, #0D0000 40px);
            border: 3px solid #FF0000;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 0 40px rgba(255,0,0,0.6);
            margin-top: 1.5rem;
            animation: pulse-red 1.5s infinite;
        ">
            <div style="font-size: 3rem; letter-spacing: 8px;">🚑 🚒 🚓 🚁 🚑</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #FF0000; text-shadow: 0 0 15px #FF0000; letter-spacing: 3px; margin: 1rem 0;">
                ✅ ALL UNITS: MISSION COMPLETE
            </div>
            <div style="font-size: 1.1rem; color: #E0E1DD; font-weight: 600; letter-spacing: 1px;">
                INCIDENT ACTION PLAN COMPILED · SITREP PDF GENERATED · AUDIT LOG SEALED
            </div>
            <div style="font-size: 2rem; letter-spacing: 8px; margin-top: 1rem;">🚑 🚒 🚓 🚁 🚑</div>
        </div>
        """, unsafe_allow_html=True)
        
    elif len(st.session_state.crisis_logs) > 0:
        for log in st.session_state.crisis_logs:
            meta_html = ""
            if log.get("meta"):
                meta_html = f"<div class='tactical-meta'>🛰️ SECURE TOOL LINK ATTACHED: {log['meta'].get('tool_used', 'EOC Engine')}</div>"
            st.markdown(f"""
            <div class="tactical-card">
                <div class="tactical-header"><span>{log['agent'].split(' ')[0]}</span> {log['agent']}</div>
                <div style="white-space: pre-wrap; font-size: 1.15rem; line-height: 1.7; color: #E0E1DD;">{log['msg']}</div>
                {meta_html}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🛰️ Command Center in Standby Mode. Select a crisis scenario in the sidebar and click **'🚨 ACTIVATE EMERGENCY SWARM 🚨'** to initiate live response.")

# TAB 2: LOGISTICS & RESOURCE DISPATCH
with tab2:
    st.markdown("### 🗺️ Captain Logan's Emergency Fleet Dispatch & Triage Logistics")
    
    logistics = st.session_state.logistics_metrics
    if not logistics:
        st.warning("⚠️ Activate the emergency swarm to calculate fleet dispatch and trauma triage logistics.")
    else:
        fleet = logistics.get("required_fleet", {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="eoc-kpi">
                <div class="kpi-label">Est Affected Population</div>
                <div class="kpi-val-red">{logistics.get('est_affected_population', 0):,}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="eoc-kpi">
                <div class="kpi-label">Total Responders Deployed</div>
                <div class="kpi-val">{fleet.get('total_personnel', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="eoc-kpi">
                <div class="kpi-label">Total Triage Beds Needed</div>
                <div class="kpi-val">{logistics.get('total_beds_allocated', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="eoc-kpi">
                <div class="kpi-label">Est Evacuation Timeline</div>
                <div class="kpi-val">{logistics.get('est_evacuation_hours', 0)} hrs</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Plotly Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### 🚑 Deployed Emergency Fleet Distribution")
            fleet_categories = ["Ambulances", "Fire Engines", "HAZMAT Units", "Medevac Choppers"]
            fleet_counts = [fleet.get("ambulances", 0), fleet.get("fire_engines", 0), fleet.get("hazmat_units", 0), fleet.get("medevac_choppers", 0)]
            
            fig1 = go.Figure(data=[
                go.Bar(x=fleet_categories, y=fleet_counts, marker_color=['#00FFFF', '#FF3366', '#FFB703', '#3A506B'])
            ])
            fig1.update_layout(
                template='plotly_dark',
                paper_bgcolor='#0B132B',
                plot_bgcolor='#0B132B',
                title="Active First-Responder Fleet Units",
                xaxis_title="Fleet Category",
                yaxis_title="Units Dispatched"
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_chart2:
            st.markdown("#### 🏥 Trauma Hospital Bed Triage Allocation")
            hospitals = logistics.get("hospitals_triage", [])
            if hospitals:
                h_names = [h["name"] for h in hospitals]
                h_beds = [h["allocated_beds"] for h in hospitals]
                fig2 = px.pie(names=h_names, values=h_beds, hole=0.4, color_discrete_sequence=['#FF3366', '#00FFFF', '#FFB703'])
                fig2.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='#0B132B',
                    plot_bgcolor='#0B132B',
                    title="Triage Patient Distribution"
                )
                st.plotly_chart(fig2, use_container_width=True)

# TAB 3: PUBLIC BROADCAST & SITREP
with tab3:
    st.markdown("### 📢 Officer Sarah's Public Broadcast & Official SITREP Deliverables")
    files = st.session_state.crisis_files
    
    if not files:
        st.warning("⚠️ Activate the emergency swarm to generate official public safety alerts and SITREP PDF.")
    else:
        # EAS Broadcast Display
        txt_path = files.get("txt")
        eas_content = "EMERGENCY ALERT SYSTEM (EAS) BROADCAST NOT FOUND."
        if txt_path and os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                eas_content = f.read()
                
        st.markdown(f"""
        <div class="eas-alert">
            <div class="eas-header"><span>🚨</span> EMERGENCY ALERT SYSTEM (EAS) ACTIVATION</div>
            <div style="font-size: 1.25rem; line-height: 1.8; white-space: pre-wrap; font-weight: 700;">{eas_content}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # SITREP PDF Download
        st.markdown("#### 📊 Official Incident Action Plan & SITREP (PDF)")
        pdf_path = files.get("pdf")
        
        if pdf_path and os.path.exists(pdf_path):
            # AUDIO LOGIC
            audio_path = files.get('audio_path')
            if audio_path and os.path.exists(audio_path):
                st.markdown('### 🔊 Auto-Generated Emergency Broadcast (EAS) Audio')
                st.audio(audio_path, format='audio/mp3', autoplay=True)
                st.success('Audio EAS Alert Generated and Ready for Public Broadcast.')

            st.success(f"🛰️ Ready for secure download: `{pdf_path}`")
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 DOWNLOAD OFFICIAL SITREP & ACTION PLAN PDF",
                data=pdf_bytes,
                file_name=pdf_path,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        else:
            st.error("PDF SITREP document not found.")

# TAB 4: SWARM WORKFLOW MATRIX
with tab4:
    st.markdown("### 🛡️ Tactical Swarm Chain of Command Matrix")
    st.markdown("Visualizing the autonomous sequential dependencies across the EOC First-Responder Swarm.")
    
    st.markdown("""
    <div style="background: rgba(28, 37, 65, 0.85); padding: 2.5rem; border-radius: 20px; border: 2px solid #00FFFF; text-align: center; margin-top: 1rem;">
        <h2 style="color: #00FFFF; margin-bottom: 2rem;">🚨 INCIDENT COMMAND PIPELINE</h2>
        <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div style="background: #FF3366; padding: 1.2rem 2rem; border-radius: 12px; font-weight: 900; font-size: 1.1rem; color: white; width: 220px;">
                1. Major Vance 🚨<br><span style="font-size: 0.85rem; font-weight: 500;">Incident Commander</span>
            </div>
            <div style="color: #00FFFF; font-size: 2rem;">➔</div>
            <div style="background: #1C2541; border: 2px solid #00FFFF; padding: 1.2rem 2rem; border-radius: 12px; font-weight: 900; font-size: 1.1rem; color: #00FFFF; width: 220px;">
                2. Dr. Aris 🔍<br><span style="font-size: 0.85rem; font-weight: 500;">HAZMAT & Risk Lead</span>
            </div>
            <div style="color: #00FFFF; font-size: 2rem;">➔</div>
            <div style="background: #1C2541; border: 2px solid #00FFFF; padding: 1.2rem 2rem; border-radius: 12px; font-weight: 900; font-size: 1.1rem; color: #00FFFF; width: 220px;">
                3. SkyEye-1 🚁<br><span style="font-size: 0.85rem; font-weight: 500;">Aerial Thermal Recon</span>
            </div>
            <div style="color: #00FFFF; font-size: 2rem;">➔</div>
            <div style="background: #1C2541; border: 2px solid #00FFFF; padding: 1.2rem 2rem; border-radius: 12px; font-weight: 900; font-size: 1.1rem; color: #00FFFF; width: 220px;">
                4. Capt. Logan 🗺️<br><span style="font-size: 0.85rem; font-weight: 500;">Fleet & Dispatch Lead</span>
            </div>
            <div style="color: #00FFFF; font-size: 2rem;">➔</div>
            <div style="background: #FFB703; padding: 1.2rem 2rem; border-radius: 12px; font-weight: 900; font-size: 1.1rem; color: #0B132B; width: 220px;">
                5. Officer Sarah 📢<br><span style="font-size: 0.85rem; font-weight: 500;">Crisis Broadcast PIO</span>
            </div>
            <div style="color: #00FFFF; font-size: 2rem;">➔</div>
            <div style="background: #00FFFF; padding: 1.2rem 2rem; border-radius: 12px; font-weight: 900; font-size: 1.1rem; color: #0B132B; width: 220px;">
                6. Chief Riley 📊<br><span style="font-size: 0.85rem; font-weight: 500;">Official SITREP Compiler</span>
            </div>
        </div>
        <p style="color: #A0AEC0; margin-top: 2.5rem; font-size: 1.1rem;">
            Each agent processes tactical telemetry and feeds structured intelligence directly to the next commanding officer.
        </p>
    </div>
    """, unsafe_allow_html=True)

# TAB 5: ABOUT THIS SYSTEM
with tab5:
    st.markdown("""
    <div style="max-width: 900px; margin: 0 auto;">

    <div style="background: linear-gradient(135deg, #1A0505 0%, #0C121E 100%); border: 2px solid #D90429; border-radius: 12px; padding: 2.5rem; text-align: center; margin-bottom: 2rem; box-shadow: 0 0 40px rgba(217,4,41,0.4);">
        <div style="font-size: 3.5rem; margin-bottom: 1rem;">🚨</div>
        <h1 style="color: #FFFFFF; font-size: 2.5rem; font-weight: 900; margin: 0; letter-spacing: 1px;">AIOS — Autonomous Incident Operations Swarm</h1>
        <p style="color: #8A9BAE; font-size: 1.1rem; margin-top: 0.8rem;">Multi-Agent AI Emergency Coordination System</p>
        <div style="display: flex; justify-content: center; gap: 12px; margin-top: 1.5rem; flex-wrap: wrap;">
            <span style="background: #1C2B40; border: 1px solid #00FFFF; color: #00FFFF; padding: 6px 16px; border-radius: 4px; font-size: 0.85rem; font-weight: 700;">🤖 Google Gemini 1.5 Flash</span>
            <span style="background: #1C2B40; border: 1px solid #00FFFF; color: #00FFFF; padding: 6px 16px; border-radius: 4px; font-size: 0.85rem; font-weight: 700;">🌐 Streamlit</span>
            <span style="background: #1C2B40; border: 1px solid #00FFFF; color: #00FFFF; padding: 6px 16px; border-radius: 4px; font-size: 0.85rem; font-weight: 700;">🗺️ Folium Maps</span>
            <span style="background: #1C2B40; border: 1px solid #00FFFF; color: #00FFFF; padding: 6px 16px; border-radius: 4px; font-size: 0.85rem; font-weight: 700;">🔊 gTTS Audio</span>
            <span style="background: #1C2B40; border: 1px solid #00FFFF; color: #00FFFF; padding: 6px 16px; border-radius: 4px; font-size: 0.85rem; font-weight: 700;">📄 ReportLab PDF</span>
            <span style="background: #1C2B40; border: 1px solid #00FFFF; color: #00FFFF; padding: 6px 16px; border-radius: 4px; font-size: 0.85rem; font-weight: 700;">🔍 DuckDuckGo Search</span>
        </div>
    </div>

    <h2 style="color: #00FFFF; border-bottom: 1px solid #1C2B40; padding-bottom: 0.5rem;">⚙️ How It Works</h2>
    <p style="color: #C0C8D8; font-size: 1.05rem; line-height: 1.8;">
        AIOS deploys a <strong style="color: #FFFFFF;">6-agent autonomous swarm</strong> in a sequential command pipeline.
        Each agent is a specialized AI persona powered by <strong style="color: #FFFFFF;">Google Gemini 1.5 Flash</strong>.
        They collaborate in real-time, passing intelligence to the next agent — exactly like a real Emergency Operations Center (EOC).
    </p>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.5rem 0;">
        <div style="background: #0C121E; border: 1px solid #1C2B40; border-left: 4px solid #D90429; padding: 1.2rem; border-radius: 8px;">
            <div style="font-size: 1.5rem;">🚨</div>
            <div style="font-weight: 700; color: #FFFFFF; margin: 0.4rem 0;">Major Vance — Commander</div>
            <div style="color: #8A9BAE; font-size: 0.9rem;">Sets strategic command objectives & distributes directives to all units</div>
        </div>
        <div style="background: #0C121E; border: 1px solid #1C2B40; border-left: 4px solid #00FFFF; padding: 1.2rem; border-radius: 8px;">
            <div style="font-size: 1.5rem;">🔍</div>
            <div style="font-weight: 700; color: #FFFFFF; margin: 0.4rem 0;">Dr. Aris — HAZMAT Lead</div>
            <div style="color: #8A9BAE; font-size: 0.9rem;">Runs live web searches for chemical data, BLEVE risk & plume analysis</div>
        </div>
        <div style="background: #0C121E; border: 1px solid #1C2B40; border-left: 4px solid #00FFFF; padding: 1.2rem; border-radius: 8px;">
            <div style="font-size: 1.5rem;">🚁</div>
            <div style="font-weight: 700; color: #FFFFFF; margin: 0.4rem 0;">SkyEye-1 — Aerial Recon</div>
            <div style="color: #8A9BAE; font-size: 0.9rem;">Maps thermal signatures, blast radius, and perimeter cordon coordinates</div>
        </div>
        <div style="background: #0C121E; border: 1px solid #1C2B40; border-left: 4px solid #00FFFF; padding: 1.2rem; border-radius: 8px;">
            <div style="font-size: 1.5rem;">🗺️</div>
            <div style="font-weight: 700; color: #FFFFFF; margin: 0.4rem 0;">Captain Logan — Logistics</div>
            <div style="color: #8A9BAE; font-size: 0.9rem;">Calculates ambulances, fire engines, HAZMAT trucks & hospital triage beds</div>
        </div>
        <div style="background: #0C121E; border: 1px solid #1C2B40; border-left: 4px solid #FFB703; padding: 1.2rem; border-radius: 8px;">
            <div style="font-size: 1.5rem;">📢</div>
            <div style="font-weight: 700; color: #FFFFFF; margin: 0.4rem 0;">Officer Sarah — Broadcast PIO</div>
            <div style="color: #8A9BAE; font-size: 0.9rem;">Generates AI-voiced EAS emergency broadcast unique to each incident</div>
        </div>
        <div style="background: #0C121E; border: 1px solid #1C2B40; border-left: 4px solid #00FFFF; padding: 1.2rem; border-radius: 8px;">
            <div style="font-size: 1.5rem;">📊</div>
            <div style="font-weight: 700; color: #FFFFFF; margin: 0.4rem 0;">Chief Riley — SITREP Lead</div>
            <div style="color: #8A9BAE; font-size: 0.9rem;">Compiles official Incident Action Plan PDF + enterprise CSV audit trail</div>
        </div>
    </div>

    <h2 style="color: #00FFFF; border-bottom: 1px solid #1C2B40; padding-bottom: 0.5rem; margin-top: 2rem;">📦 System Outputs</h2>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div style="background: #0C121E; border: 1px solid #1C2B40; padding: 1rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 2rem;">📄</div>
            <div style="color: #FFFFFF; font-weight: 700;">SITREP PDF</div>
            <div style="color: #8A9BAE; font-size: 0.85rem;">Official Incident Action Plan</div>
        </div>
        <div style="background: #0C121E; border: 1px solid #1C2B40; padding: 1rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 2rem;">🔊</div>
            <div style="color: #FFFFFF; font-weight: 700;">EAS Audio Alert</div>
            <div style="color: #8A9BAE; font-size: 0.85rem;">AI Text-to-Speech broadcast</div>
        </div>
        <div style="background: #0C121E; border: 1px solid #1C2B40; padding: 1rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 2rem;">🗺️</div>
            <div style="color: #FFFFFF; font-weight: 700;">Live Tactical Map</div>
            <div style="color: #8A9BAE; font-size: 0.85rem;">Epicenter + containment zone</div>
        </div>
        <div style="background: #0C121E; border: 1px solid #1C2B40; padding: 1rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 2rem;">📋</div>
            <div style="color: #FFFFFF; font-weight: 700;">Audit Trail CSV</div>
            <div style="color: #8A9BAE; font-size: 0.85rem;">Enterprise compliance log</div>
        </div>
    </div>

    </div>
    """, unsafe_allow_html=True)
