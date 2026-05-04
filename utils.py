import pandas as pd
from fpdf import FPDF
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import streamlit as st

# --- Fuso horário padrão (Brasília) ---
try:
    LOCAL_TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    LOCAL_TZ = None

def _to_local_datetime(ts):
    """Converte timestamp (string, datetime naive ou aware) para datetime com fuso local (Brasília)."""
    if not isinstance(ts, datetime):
        ts = pd.to_datetime(ts, format='ISO8601', utc=True)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if LOCAL_TZ:
        return ts.astimezone(LOCAL_TZ)
    else:
        return ts

def calculate_total_hours(time_entries_df):
    """Calcula total de horas trabalhadas (entradas/saídas) a partir de um DataFrame."""
    total_seconds = 0
    current_entry_time = None
    time_entries_df = time_entries_df.sort_values(by='timestamp')
    for _, row in time_entries_df.iterrows():
        ts = pd.to_datetime(row['timestamp'], format='ISO8601', utc=True)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)  # remove timezone para cálculo
        if row['action'] == 'entrada':
            current_entry_time = ts
        elif row['action'] == 'saida' and current_entry_time is not None:
            duration = ts - current_entry_time
            total_seconds += duration.total_seconds()
            current_entry_time = None
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def generate_pdf_report(employee_name, time_entries_df, start_date, end_date):
    """Relatório individual com tabela Data | Entrada | Saída | Horas trabalhadas."""
    time_entries_df['timestamp_local'] = time_entries_df['timestamp'].apply(_to_local_datetime)
    time_entries_df = time_entries_df.sort_values('timestamp_local')
    
    daily_data = []
    current_day = None
    entry_time = None
    
    for _, row in time_entries_df.iterrows():
        ts = row['timestamp_local']
        day = ts.date()
        action = row['action']
        
        if day != current_day:
            if entry_time is not None:
                pass
            current_day = day
            entry_time = None
        
        if action == 'entrada':
            entry_time = ts
        elif action == 'saida' and entry_time is not None:
            duration = ts - entry_time
            hours_worked = duration.total_seconds() / 3600
            daily_data.append({
                'data': day,
                'entrada': entry_time.strftime('%H:%M:%S'),
                'saida': ts.strftime('%H:%M:%S'),
                'horas': hours_worked
            })
            entry_time = None
    
    total_hours = sum(item['horas'] for item in daily_data)
    total_hours_str = f"{int(total_hours)}:{int((total_hours % 1)*60):02d}"
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório de Ponto - {employee_name}", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", 0, 1, "C")
    pdf.ln(10)
    
    if not daily_data:
        pdf.cell(0, 10, "Nenhum registro completo (entrada+saída) no período.", 0, 1, "C")
    else:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 10, "Data", 1)
        pdf.cell(40, 10, "Entrada", 1)
        pdf.cell(40, 10, "Saída", 1)
        pdf.cell(40, 10, "Horas Trabalhadas", 1, 1)
        pdf.set_font("Arial", "", 10)
        for item in daily_data:
            pdf.cell(40, 10, item['data'].strftime('%d/%m/%Y'), 1)
            pdf.cell(40, 10, item['entrada'], 1)
            pdf.cell(40, 10, item['saida'], 1)
            horas = item['horas']
            h = int(horas)
            m = int((horas - h) * 60)
            pdf.cell(40, 10, f"{h:02d}:{m:02d}", 1, 1)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Total de horas no período: {total_hours_str}", 0, 1, "L")
    
    return bytes(pdf.output(dest='S'))

def generate_single_entry_pdf(employee, entry):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Comprovante de Registro", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Funcionário: {employee['name']}", 0, 1, "C")
    ts_local = _to_local_datetime(entry['timestamp'])
    pdf.cell(0, 10, f"Data: {ts_local.strftime('%d/%m/%Y')}   Hora: {ts_local.strftime('%H:%M:%S')}", 0, 1, "C")
    pdf.cell(0, 10, f"Ação: {entry['action'].capitalize()}", 0, 1, "C")
    pdf.ln(5)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Emitido pelo sistema Ponto Smart", 0, 1, "C")
    return bytes(pdf.output(dest='S'))

def generate_all_employees_report(employee_data_list, start_date, end_date):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Relatório Geral de Ponto", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", 0, 1, "C")
    pdf.ln(5)
    
    summary_data = []
    for nome, df in employee_data_list:
        df['timestamp_local'] = df['timestamp'].apply(_to_local_datetime)
        df = df.sort_values('timestamp_local')
        
        daily_data = []
        current_day = None
        entry_time = None
        
        for _, row in df.iterrows():
            ts = row['timestamp_local']
            day = ts.date()
            action = row['action']
            
            if day != current_day:
                if entry_time is not None:
                    pass
                current_day = day
                entry_time = None
            
            if action == 'entrada':
                entry_time = ts
            elif action == 'saida' and entry_time is not None:
                duration = ts - entry_time
                hours_worked = duration.total_seconds() / 3600
                daily_data.append({
                    'data': day,
                    'entrada': entry_time.strftime('%H:%M:%S'),
                    'saida': ts.strftime('%H:%M:%S'),
                    'horas': hours_worked
                })
                entry_time = None
        
        total_hours = sum(item['horas'] for item in daily_data)
        summary_data.append((nome, total_hours))
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Funcionário: {nome}", 0, 1, "L")
        if not daily_data:
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, "Nenhum registro completo no período.", 0, 1, "L")
        else:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(40, 10, "Data", 1)
            pdf.cell(40, 10, "Entrada", 1)
            pdf.cell(40, 10, "Saída", 1)
            pdf.cell(40, 10, "Horas Trabalhadas", 1, 1)
            pdf.set_font("Arial", "", 10)
            for item in daily_data:
                pdf.cell(40, 10, item['data'].strftime('%d/%m/%Y'), 1)
                pdf.cell(40, 10, item['entrada'], 1)
                pdf.cell(40, 10, item['saida'], 1)
                h = int(item['horas'])
                m = int((item['horas'] - h) * 60)
                pdf.cell(40, 10, f"{h:02d}:{m:02d}", 1, 1)
            pdf.set_font("Arial", "B", 10)
            total_horas_str = f"{int(total_hours)}:{int((total_hours % 1)*60):02d}"
            pdf.cell(0, 10, f"Total do funcionário: {total_horas_str}", 0, 1, "L")
        pdf.ln(5)
    
    if summary_data:
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Resumo de Horas por Funcionário", 0, 1, "C")
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(80, 10, "Funcionário", 1)
        pdf.cell(60, 10, "Total de Horas", 1, 1)
        pdf.set_font("Arial", "", 12)
        for nome, total in summary_data:
            total_str = f"{int(total)}:{int((total % 1)*60):02d}"
            pdf.cell(80, 10, nome, 1)
            pdf.cell(60, 10, total_str, 1, 1)
    
    return bytes(pdf.output(dest='S'))

def send_email_with_attachment(to_email, subject, body, pdf_bytes, filename):
    try:
        smtp_server = st.secrets["SMTP_SERVER"]
        smtp_port = st.secrets["SMTP_PORT"]
        smtp_user = st.secrets["SMTP_USER"]
        smtp_password = st.secrets["SMTP_PASSWORD"]

        if isinstance(pdf_bytes, bytearray):
            pdf_bytes = bytes(pdf_bytes)

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        part = MIMEApplication(pdf_bytes, _subtype='pdf')
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True, "E-mail enviado com sucesso!"
    except Exception as e:
        return False, str(e)