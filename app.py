import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from utils import (
    generate_pdf_report,
    calculate_total_hours,
    generate_single_entry_pdf,
    generate_all_employees_report,
    send_email_with_attachment
)
# --- CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA CHAMADA) ---
st.set_page_config(
    layout="wide",                     # conteúdo ocupa toda a largura da tela
    initial_sidebar_state="collapsed"  # sidebar inicia recolhida
)

# --- Configurações do Supabase ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Fuso horário Brasil (ou fallback UTC) ---
try:
    FUSO_BR = ZoneInfo("America/Sao_Paulo")
except Exception:
    FUSO_BR = None

# --- Funções auxiliares de data (UTC) ---
def _utc_today_start():
    now_utc = datetime.now(timezone.utc)
    return now_utc.replace(hour=0, minute=0, second=0, microsecond=0)

def _utc_today_end():
    start = _utc_today_start()
    return start + timedelta(days=1) - timedelta(microseconds=1)

# --- Seed inicial (com email) ---
def seed_initial_data():
    existing_emp = supabase.from_('employees').select('*', count='exact').execute()
    if existing_emp.count == 0:
        fake_employees = [
            ("Ana Silva", "1000", "ana@empresa.com"),
            ("Bruno Souza", "1001", "bruno@empresa.com"),
            ("Carla Lima", "1002", "carla@empresa.com"),
            ("Daniel Rocha", "1003", "daniel@empresa.com"),
            ("Elisa Melo", "1004", "elisa@empresa.com"),
            ("Fábio Neves", "1005", "fabio@empresa.com"),
            ("Gabriela Reis", "1006", "gabriela@empresa.com"),
            ("Henrique Matos", "1007", "henrique@empresa.com"),
            ("Isabela Nunes", "1008", "isabela@empresa.com"),
            ("João Pedro", "1009", "joao@empresa.com")
        ]
        for name, pin, email in fake_employees:
            supabase.from_('employees').insert({"name": name, "pin": pin, "email": email}).execute()
        st.success("✅ 10 funcionários fictícios adicionados!")

    existing_admin = supabase.from_('admin').select('*', count='exact').execute()
    if existing_admin.count == 0:
        supabase.from_('admin').insert({"id": 1, "password": "admin123"}).execute()

# --- Funções BD (employees com email) ---
def get_employees():
    return supabase.from_('employees').select('*').execute().data

def get_employee_by_pin(pin):
    res = supabase.from_('employees').select('*').eq('pin', pin).execute()
    return res.data[0] if res.data else None

def get_employee_by_id(employee_id):
    return supabase.from_('employees').select('*').eq('id', str(employee_id)).single().execute().data

def add_employee(name, pin, email):
    return supabase.from_('employees').insert({"name": name, "pin": pin, "email": email}).execute().data

def update_employee_pin(employee_id, new_pin):
    return supabase.from_('employees').update({"pin": new_pin}).eq('id', str(employee_id)).execute().data

def update_employee_email(employee_id, new_email):
    return supabase.from_('employees').update({"email": new_email}).eq('id', str(employee_id)).execute().data

def delete_employee(employee_id):
    return supabase.from_('employees').delete().eq('id', str(employee_id)).execute().data

# --- Funções BD (time_entries) ---
def get_time_entries(employee_id=None, start_date=None, end_date=None):
    query = supabase.from_('time_entries').select('*')
    if employee_id:
        query = query.eq('employee_id', str(employee_id))
    if start_date:
        if isinstance(start_date, datetime) and start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        query = query.gte('timestamp', start_date.isoformat())
    if end_date:
        if isinstance(end_date, datetime) and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        query = query.lte('timestamp', end_date.isoformat())
    query = query.order('timestamp', desc=False)
    return query.execute().data

def add_time_entry(employee_id, action):
    return supabase.from_('time_entries').insert({
        "employee_id": str(employee_id),
        "action": action,
        "is_corrected": False
    }).execute().data

def update_time_entry(entry_id, new_timestamp, new_action, corrected_by, reason):
    return supabase.from_('time_entries').update({
        "timestamp": new_timestamp.isoformat(),
        "action": new_action,
        "is_corrected": True,
        "corrected_by": corrected_by,
        "correction_reason": reason
    }).eq('id', str(entry_id)).execute().data

# --- Admin ---
def get_admin_password():
    res = supabase.from_('admin').select('password').eq('id', 1).single().execute()
    return res.data['password'] if res.data else 'admin123'

def update_admin_password(new_password):
    supabase.from_('admin').update({"password": new_password}).eq('id', 1).execute()

def admin_login(username, password):
    if username != "admin":
        return False
    stored_pwd = get_admin_password()
    return password == stored_pwd

# --- Estilo com cores corrigidas e reforçadas ---
def apply_dark_theme():
    st.markdown("""
    <style>
    /* Fundo geral */
    .stApp { background-color: #1a1a2e; color: #e0e0e0; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown p { color: #ffffff; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div { background-color: #ffffff; color: #000000; }

    /* Campo PIN */
    div[data-testid="stTextInput"]:has(input[placeholder="PIN"]) {
        max-width: 200px;
        margin-left: auto;
        margin-right: auto;
    }

    /* ---------- CORES DOS BOTÕES (reforçadas com !important) ---------- */
    /* Botões primários (Confirmar PIN, Registrar Entrada) -> VERDE */
    button[kind="primary"] {
        background-color: #00c853 !important;
        color: white !important;
        border: none !important;
    }

    /* Botões secundários padrão (Alterar PIN, e outros do admin) -> LARANJA */
    button[kind="secondary"] {
        background-color: #ff9800 !important;
        color: white !important;
        border: none !important;
    }

    /* Botão Registrar Saída (está na primeira coluna e é secundário) -> AZUL */
    div[data-testid="column"]:first-of-type button[kind="secondary"] {
        background-color: #1E88E5 !important;
        color: white !important;
    }

    /* Estilo geral dos botões (tamanho, borda, etc.) */
    .stButton > button {
        border-radius: 8px !important;
        font-size: 2.0em;
        padding: 10px 5px;
        margin: 5px 0;
        width: 100%;
        text-transform: uppercase !important;
    }

    /* Sidebar: fonte dos rádios */
    div[data-testid="stSidebar"] .stRadio label {
        font-size: 1.2em !important;
        font-weight: 500 !important;
    }

    /* Mensagem de confirmação */
    .kiosk-message {
        font-size: 2.0em !important;
        font-weight: 900 !important;
        text-align: center;
        margin: 30px 0;
        padding: 15px;
        color: #00FF7F !important;
        text-transform: uppercase;
        text-shadow: 2px 2px 6px rgba(0,0,0,0.4);
        letter-spacing: 1px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.9; }
        50% { transform: scale(1.05); opacity: 1; text-shadow: 4px 4px 12px rgba(0,0,0,0.5); }
        100% { transform: scale(1); opacity: 0.9; }
    }

    .slogan {
        margin-top: -15px !important;
        margin-bottom: 10px !important;
        font-size: 1.2em;
        text-align: center;
        color: #cccccc;
    }

    /* Rodapé da sidebar */
    .sidebar-footer {
        font-size: 0.8em;
        text-align: center;
        color: #888888;
        margin-top: 20px;
        padding-top: 10px;
        border-top: 1px solid #333333;
        animation: fadeIn 1s ease-in-out;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

    # JavaScript para botões especiais: Sair (vermelho) e Enviar Comprovante (amarelo)
    st.markdown("""
    <script>
    (function() {
        function colorSpecialButtons() {
            document.querySelectorAll('button').forEach(btn => {
                const text = btn.innerText.trim();
                // Botão SAIR (qualquer lugar) -> vermelho
                if (text.includes('SAIR')) {
                    btn.style.backgroundColor = '#E53935';
                    btn.style.color = 'white';
                    btn.style.border = 'none';
                }
                // Botão ENVIAR COMPROVANTE (modo quiosque) -> amarelo
                if (text.includes('ENVIAR COMPROVANTE POR E-MAIL')) {
                    btn.style.backgroundColor = '#ffea00';
                    btn.style.color = 'black';
                    btn.style.border = 'none';
                }
                // Garantir que o botão "Registrar Entrada" continue verde
                if (text === 'REGISTRAR ENTRADA') {
                    btn.style.backgroundColor = '#00c853';
                    btn.style.color = 'white';
                }
                // Garantir que o botão "Registrar Saída" continue azul
                if (text === 'REGISTRAR SAÍDA') {
                    btn.style.backgroundColor = '#1E88E5';
                    btn.style.color = 'white';
                }
                // Garantir que "Confirmar PIN" seja verde
                if (text === 'CONFIRMAR PIN') {
                    btn.style.backgroundColor = '#00c853';
                    btn.style.color = 'white';
                }
                // Garantir que "Alterar PIN" seja laranja
                if (text === 'ALTERAR PIN') {
                    btn.style.backgroundColor = '#ff9800';
                    btn.style.color = 'white';
                }
            });
        }
        colorSpecialButtons();
        new MutationObserver(colorSpecialButtons).observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    """, unsafe_allow_html=True)

# --- Função para adicionar o rodapé na sidebar ---
def add_sidebar_footer():
    st.sidebar.markdown("""
    <div class="sidebar-footer">
        Ponto Smart V1.0<br>
        Desenvolvido por: Emerson Lobo &amp; Ubaldo Meireles
    </div>
    """, unsafe_allow_html=True)

# --- Verifica última ação (global) - CORREÇÃO AQUI ---
def get_last_action(employee_id):
    """Retorna a última ação registrada (entrada ou saída) independente da data."""
    entries = get_time_entries(employee_id=employee_id)
    return entries[-1]['action'] if entries else None


def send_registration_receipt(emp, entry):
    """Envia automaticamente o comprovante de registro para o e-mail cadastrado."""
    ts = pd.to_datetime(entry['timestamp'], format='ISO8601', utc=True)
    if FUSO_BR:
        ts_local = ts.tz_convert(FUSO_BR)
    else:
        ts_local = ts

    data_formatada = ts_local.strftime('%d/%m/%Y')
    hora_formatada = ts_local.strftime('%H:%M:%S')
    acao = entry['action'].capitalize()

    if not emp.get('email'):
        return False, "Funcionário não possui e-mail cadastrado. Contate o administrador."

    pdf_bytes = generate_single_entry_pdf(emp, entry)
    subject = f"Comprovante de {acao} - {data_formatada}"
    body = f"""
    Prezado(a) {emp['name']},

    Segue em anexo o comprovante do seu registro de ponto.

    Data: {data_formatada}
    Hora: {hora_formatada}
    Ação: {acao}

    Atenciosamente,
    Sistema Ponto Smart
    """
    filename = f"comprovante_{emp['name']}_{data_formatada}.pdf"
    return send_email_with_attachment(emp['email'], subject, body, pdf_bytes, filename)

# --- Kiosk Mode (com rodapé na sidebar) ---
def kiosk_mode():
    apply_dark_theme()
    if "authenticated_employee" not in st.session_state:
        st.session_state.authenticated_employee = None
    if "show_pin_change" not in st.session_state:
        st.session_state.show_pin_change = False
    if "just_registered" not in st.session_state:
        st.session_state.just_registered = False
    if "registration_email_status" not in st.session_state:
        st.session_state.registration_email_status = None
    if "registration_email_message" not in st.session_state:
        st.session_state.registration_email_message = None

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.image("logo.png", width=450)
        st.markdown("<h1 style='text-align: center;'>Ponto Smart</h1>", unsafe_allow_html=True)
        st.markdown("<div class='slogan'>Tradição na qualidade, inovação no controle.</div>", unsafe_allow_html=True)

    if st.session_state.authenticated_employee is None:
        st.markdown("<div style='text-align: center;'>Digite seu PIN de 4 dígitos</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pin_input = st.text_input("", type="password", max_chars=4, key="pin_input_central", placeholder="PIN", label_visibility="collapsed")
            if st.button("Confirmar PIN", key="confirm_pin", type="primary", use_container_width=True):
                if len(pin_input) == 4 and pin_input.isdigit():
                    emp = get_employee_by_pin(pin_input)
                    if emp:
                        st.session_state.authenticated_employee = emp
                        st.session_state.just_registered = False
                        st.rerun()
                    else:
                        st.error("PIN não encontrado.")
                else:
                    st.error("Digite 4 números.")
        add_sidebar_footer()
        return

    emp = st.session_state.authenticated_employee
    st.markdown(f"<h2 style='text-align:center;'>Bem-vindo, {emp['name']}!</h2>", unsafe_allow_html=True)

    if st.session_state.just_registered:
        start = _utc_today_start()
        end = _utc_today_end()
        today_entries = get_time_entries(employee_id=emp['id'], start_date=start, end_date=end)
        if today_entries:
            last_entry = today_entries[-1]
            ts = pd.to_datetime(last_entry['timestamp'], format='ISO8601', utc=True)
            if FUSO_BR:
                ts_local = ts.tz_convert(FUSO_BR)
            else:
                ts_local = ts
            data_formatada = ts_local.strftime('%d/%m/%Y')
            hora_formatada = ts_local.strftime('%H:%M:%S')
            acao = last_entry['action'].capitalize()
            st.markdown(f"<div class='kiosk-message'>✅ {acao} registrada em {data_formatada} às {hora_formatada}!</div>", unsafe_allow_html=True)

            email_status = st.session_state.get("registration_email_status")
            email_message = st.session_state.get("registration_email_message")
            if email_status is not None:
                if email_status:
                    st.success(email_message)
                else:
                    st.warning(email_message)
        else:
            st.error("Erro inesperado: registro não encontrado. Tente novamente.")
        st.write("")
        if st.button("🔒 Sair", key="btn_logout", type="secondary", use_container_width=True):
            st.session_state.authenticated_employee = None
            st.session_state.show_pin_change = False
            st.session_state.just_registered = False
            st.rerun()
        add_sidebar_footer()
        return

    # ----- CORREÇÃO: usa a última ação global, não apenas do dia -----
    last = get_last_action(emp['id'])  # nova função

    if last is None or last == 'saida':
        action = 'entrada'
        btn_label = "Registrar Entrada"
        btn_key = "btn_entrada"
        btn_type = "primary"
    else:  # last == 'entrada'
        action = 'saida'
        btn_label = "Registrar Saída"
        btn_key = "btn_saida"
        btn_type = "secondary"

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button(btn_label, key=btn_key, type=btn_type, use_container_width=True):
            add_time_entry(emp['id'], action)
            latest_entries = get_time_entries(employee_id=emp['id'])
            if latest_entries:
                last_entry = latest_entries[-1]
                sucesso, msg = send_registration_receipt(emp, last_entry)
                st.session_state.registration_email_status = sucesso
                st.session_state.registration_email_message = (
                    f"✅ Comprovante enviado automaticamente para {emp['email']}"
                    if sucesso else f"⚠️ Falha no envio automático: {msg}"
                )
            else:
                st.session_state.registration_email_status = False
                st.session_state.registration_email_message = "⚠️ Não foi possível localizar o registro recém-criado."
            st.session_state.just_registered = True
            st.rerun()
    with col2:
        if st.button("Alterar PIN", key="btn_change_pin", use_container_width=True):
            st.session_state.show_pin_change = not st.session_state.show_pin_change

    if st.session_state.show_pin_change:
        with st.form("change_pin_form"):
            st.subheader("Trocar seu PIN")
            current_pin = st.text_input("PIN atual", type="password", max_chars=4)
            new_pin = st.text_input("Novo PIN (4 dígitos)", type="password", max_chars=4)
            confirm = st.text_input("Confirme o novo PIN", type="password", max_chars=4)
            if st.form_submit_button("Salvar novo PIN", use_container_width=False):
                if current_pin != emp['pin']:
                    st.error("PIN atual incorreto.")
                elif new_pin != confirm or len(new_pin) != 4 or not new_pin.isdigit():
                    st.error("Novo PIN inválido ou não confere.")
                else:
                    update_employee_pin(emp['id'], new_pin)
                    emp['pin'] = new_pin
                    st.session_state.authenticated_employee = emp
                    st.success("PIN alterado com sucesso!")
                    st.session_state.show_pin_change = False
                    st.rerun()

    st.write("")
    if st.button("🔒 Sair", key="btn_logout_2", type="secondary", use_container_width=True):
        st.session_state.authenticated_employee = None
        st.session_state.show_pin_change = False
        st.session_state.just_registered = False
        st.rerun()

    add_sidebar_footer()

# --- Painel Administrativo com login na área principal e rodapé na sidebar ---
def admin_panel():
    apply_dark_theme()
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.markdown("<h2 style='text-align: center;'>LOGIN ADMINISTRATIVO</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            user = st.text_input("Usuário", key="admin_user_principal")
            pwd = st.text_input("Senha", type="password", key="admin_pass_principal")
            if st.button("Entrar", key="admin_login_principal", type="primary", use_container_width=True):
                if admin_login(user, pwd):
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
        add_sidebar_footer()
        return

    st.sidebar.title("ADMIN PONTO SMART")
    st.sidebar.button("SAIR", on_click=lambda: st.session_state.update(admin_logged_in=False), key="btn_admin_logout")
    
    st.title("PAINEL ADMINISTRATIVO")
    menu = st.sidebar.radio("MENU", ["FUNCIONÁRIOS", "REGISTROS DE PONTO", "RELATÓRIOS", "CONFIGURAÇÕES"])

    if menu == "FUNCIONÁRIOS":
        st.subheader("GESTÃO DE FUNCIONÁRIOS")
        emps = get_employees()
        if emps:
            df_emps = pd.DataFrame(emps)[['name', 'pin', 'email', 'created_at']]
            st.dataframe(df_emps)
        with st.form("add_emp"):
            nome = st.text_input("Nome")
            pin = st.text_input("PIN (4 dígitos)", max_chars=4)
            email = st.text_input("E-mail")
            if st.form_submit_button("Adicionar"):
                if nome and pin and len(pin)==4 and pin.isdigit() and email and "@" in email:
                    add_employee(nome, pin, email)
                    st.success(f"{nome} adicionado!")
                    st.rerun()
                else:
                    st.error("Dados inválidos. Verifique nome, PIN (4 dígitos) e e-mail válido.")
        st.markdown("--- \n### RESETAR PIN")
        if emps:
            emp_map = {e['name']: e['id'] for e in emps}
            sel = st.selectbox("Funcionário", list(emp_map.keys()), key="reset_sel")
            novo_pin = st.text_input("Novo PIN", max_chars=4, key="novo_pin")
            if st.button("Resetar PIN"):
                if novo_pin and len(novo_pin)==4 and novo_pin.isdigit():
                    update_employee_pin(emp_map[sel], novo_pin)
                    st.success("PIN resetado!")
                    st.rerun()
                else:
                    st.error("PIN inválido.")
        st.markdown("--- \n### ATUALIZAR E-MAIL")
        if emps:
            emp_map = {e['name']: e['id'] for e in emps}
            sel_email = st.selectbox("Funcionário", list(emp_map.keys()), key="email_sel")
            novo_email = st.text_input("Novo e-mail", key="novo_email")
            if st.button("Salvar e-mail"):
                if novo_email and "@" in novo_email:
                    update_employee_email(emp_map[sel_email], novo_email)
                    st.success("E-mail atualizado!")
                    st.rerun()
                else:
                    st.error("E-mail inválido.")
        st.markdown("--- \n### EXCLUIR FUNCIONÁRIO")
        if emps:
            emp_map = {e['name']: e['id'] for e in emps}
            sel_del = st.selectbox("Excluir", list(emp_map.keys()), key="del_sel")
            if st.button("Excluir"):
                delete_employee(emp_map[sel_del])
                st.success(f"{sel_del} removido!")
                st.rerun()

    elif menu == "REGISTROS DE PONTO":
        st.subheader("REGISTROS")
        entries = get_time_entries()
        if entries:
            df = pd.DataFrame(entries)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', utc=True)
            emp_df = pd.DataFrame(get_employees())
            df = df.merge(emp_df, left_on='employee_id', right_on='id', suffixes=('','_emp'))
            show = df[['name', 'timestamp', 'action', 'is_corrected', 'corrected_by', 'correction_reason', 'id']]
            show.columns = ['Funcionário', 'Data/Hora', 'Ação', 'Corrigido', 'Por', 'Motivo', 'ID']
            st.dataframe(show)
            st.markdown("--- \n### CORRIGIR")
            eid = st.text_input("ID do registro")
            if eid:
                row = show[show['ID'] == eid]
                if not row.empty:
                    row = row.iloc[0]
                    nd = st.date_input("Nova data", row['Data/Hora'].date())
                    nt = st.time_input("Nova hora", row['Data/Hora'].time())
                    na = st.selectbox("Ação", ['entrada','saida'], index=0 if row['Ação']=='entrada' else 1)
                    motivo = st.text_area("Motivo")
                    if st.button("Aplicar"):
                        ndt = datetime.combine(nd, nt)
                        update_time_entry(eid, ndt, na, "admin", motivo)
                        st.success("Corrigido!")
                        st.rerun()
                else:
                    st.error("ID não encontrado.")
        else:
            st.info("Nenhum registro.")

    elif menu == "RELATÓRIOS":
        st.subheader("RELATÓRIOS")
        emps = get_employees()
        emp_map = {e['name']: e['id'] for e in emps}
        nomes = ["-- TODOS --"] + list(emp_map.keys())
        sel = st.selectbox("Funcionário", nomes)
        
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input("Início", datetime.now().replace(day=1))
        with c2:
            end = st.date_input("Fim", datetime.now())
        
        destinatario = st.text_input("E-mail para envio do relatório:", value=st.secrets.get("ADMIN_EMAIL", ""))
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            baixar = st.button("📥 BAIXAR PDF", use_container_width=True)
        with col_b2:
            enviar = st.button("📧 ENVIAR POR E-MAIL", use_container_width=True)
        
        if baixar or enviar:
            start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_dt = datetime.combine(end, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            if sel == "-- TODOS --":
                all_entries = []
                for nome, eid in emp_map.items():
                    ent = get_time_entries(employee_id=eid, start_date=start_dt, end_date=end_dt)
                    if ent:
                        df_emp = pd.DataFrame(ent)
                        df_emp['timestamp'] = pd.to_datetime(df_emp['timestamp'], format='ISO8601', utc=True)
                        all_entries.append((nome, df_emp))
                if not all_entries:
                    st.warning("Nenhum registro no período.")
                else:
                    if baixar:
                        pdf_bytes = generate_all_employees_report(all_entries, start, end)
                        st.download_button(
                            label="Clique para salvar o PDF",
                            data=pdf_bytes,
                            file_name=f"relatorio_geral_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            key="download_geral"
                        )
                    if enviar:
                        if not destinatario:
                            st.error("Informe um e-mail de destino.")
                        else:
                            pdf_bytes = generate_all_employees_report(all_entries, start, end)
                            assunto = f"Relatório geral de ponto - {start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}"
                            corpo = f"""
                            Prezado administrador,

                            Segue em anexo o relatório geral de ponto do período de {start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}.

                            Atenciosamente,
                            Sistema Ponto Smart
                            """
                            nome_arquivo = f"relatorio_geral_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            sucesso, msg = send_email_with_attachment(destinatario, assunto, corpo, pdf_bytes, nome_arquivo)
                            if sucesso:
                                st.success(f"✅ Relatório enviado para {destinatario}")
                            else:
                                st.error(f"❌ Falha no envio: {msg}")
            else:
                eid = emp_map[sel]
                entries = get_time_entries(employee_id=eid, start_date=start_dt, end_date=end_dt)
                if entries:
                    df = pd.DataFrame(entries)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', utc=True)
                    total_horas = calculate_total_hours(df)
                    if baixar:
                        pdf_bytes = generate_pdf_report(sel, df, start, end)
                        st.download_button(
                            label="Clique para salvar o PDF",
                            data=pdf_bytes,
                            file_name=f"relatorio_{sel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            key="download_individual"
                        )
                        st.write(f"Total de horas trabalhadas no período: {total_horas}")
                    if enviar:
                        if not destinatario:
                            st.error("Informe um e-mail de destino.")
                        else:
                            pdf_bytes = generate_pdf_report(sel, df, start, end)
                            assunto = f"Relatório de ponto - {sel} - {start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}"
                            corpo = f"""
                            Prezado administrador,

                            Segue em anexo o relatório de ponto do funcionário {sel} para o período de {start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}.

                            Total de horas trabalhadas no período: {total_horas}

                            Atenciosamente,
                            Sistema Ponto Smart
                            """
                            nome_arquivo = f"relatorio_{sel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            sucesso, msg = send_email_with_attachment(destinatario, assunto, corpo, pdf_bytes, nome_arquivo)
                            if sucesso:
                                st.success(f"✅ Relatório enviado para {destinatario}")
                            else:
                                st.error(f"❌ Falha no envio: {msg}")
                else:
                    st.warning("Sem dados no período.")

    elif menu == "CONFIGURAÇÕES":
        st.subheader("CONFIGURAÇÕES DO ADMINISTRADOR")
        with st.form("change_admin_pwd"):
            current_pwd = st.text_input("Senha atual", type="password")
            new_pwd = st.text_input("Nova senha", type="password")
            confirm_pwd = st.text_input("Confirme nova senha", type="password")
            if st.form_submit_button("Alterar senha"):
                if current_pwd != get_admin_password():
                    st.error("Senha atual incorreta.")
                elif new_pwd != confirm_pwd:
                    st.error("Nova senha não confere.")
                elif len(new_pwd) < 4:
                    st.error("A senha deve ter pelo menos 4 caracteres.")
                else:
                    update_admin_password(new_pwd)
                    st.success("Senha alterada com sucesso! Use a nova senha no próximo login.")

    add_sidebar_footer()

# --- Main ---
def main():
    seed_initial_data()
    option = st.sidebar.radio("MODO", ["QUIOSQUE", "ADMINISTRADOR"])
    if option == "QUIOSQUE":
        kiosk_mode()
    else:
        admin_panel()

if __name__ == "__main__":
    main()