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
    """Relatório individual otimizado para caber em uma página A4 (até 31 dias)."""
    time_entries_df['timestamp_local'] = time_entries_df['timestamp'].apply(_to_local_datetime)
    time_entries_df = time_entries_df.sort_values('timestamp_local')
    
    daily_data = {}
    current_entry_time = None
    
    for _, row in time_entries_df.iterrows():
        ts = row['timestamp_local']
        day = ts.date()
        action = row['action']
        
        if day not in daily_data:
            daily_data[day] = {'entrada': None, 'saida': None, 'horas': 0}
        
        if action == 'entrada':
            if daily_data[day]['entrada'] is None:
                daily_data[day]['entrada'] = ts
            current_entry_time = ts
        elif action == 'saida':
            if daily_data[day]['saida'] is None:
                daily_data[day]['saida'] = ts
            if current_entry_time is not None:
                duration = ts - current_entry_time
                hours_worked = duration.total_seconds() / 3600
                daily_data[day]['horas'] += hours_worked
                current_entry_time = None
    
    daily_list = []
    for day in sorted(daily_data.keys()):
        data = daily_data[day]
        entrada = data['entrada'].strftime('%H:%M') if data['entrada'] else "---"
        saida = data['saida'].strftime('%H:%M') if data['saida'] else "---"
        horas = data['horas']
        daily_list.append({
            'data': day,
            'entrada': entrada,
            'saida': saida,
            'horas': horas
        })
    
    total_hours = sum(item['horas'] for item in daily_list)
    total_hours_str = f"{int(total_hours)}:{int((total_hours % 1)*60):02d}"
    
    # Layout otimizado para ocupar toda a página
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # CABEÇALHO PRINCIPAL
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RELATÓRIO DE PONTO", 0, 1, "C")
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, f"Funcionário: {employee_name}", 0, 1, "L")
    
    # Período
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", 0, 1, "L")
    
    pdf.ln(3)
    
    if not daily_list:
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, "Nenhum registro no período.", 0, 1, "C")
    else:
        # TABELA COM FONTE AUMENTADA
        pdf.set_font("Arial", "B", 10)
        col_width = 47.5  # A4 com margens: ~190mm / 4 colunas
        pdf.cell(col_width, 8, "Data", 1, 0, "C")
        pdf.cell(col_width, 8, "Entrada", 1, 0, "C")
        pdf.cell(col_width, 8, "Saída", 1, 0, "C")
        pdf.cell(col_width, 8, "Horas", 1, 1, "C")
        
        pdf.set_font("Arial", "", 9)
        for item in daily_list:
            horas = item['horas']
            h = int(horas)
            m = int((horas - h) * 60)
            pdf.cell(col_width, 7, item['data'].strftime('%d/%m/%Y'), 1, 0, "C")
            pdf.cell(col_width, 7, item['entrada'], 1, 0, "C")
            pdf.cell(col_width, 7, item['saida'], 1, 0, "C")
            pdf.cell(col_width, 7, f"{h:02d}:{m:02d}", 1, 1, "C")
        
        pdf.ln(3)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"Total de horas no período: {total_hours_str}", 0, 1, "L")
    
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
    """Relatório geral com 1 funcionário por página, máximo 31 registros por página. Inclui TODOS os funcionários."""
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    
    summary_data = []
    
    for nome, df in employee_data_list:
        # Se o DataFrame está vazio, cria uma página indicando nenhum registro
        if df.empty:
            pdf.add_page()
            
            # CABEÇALHO PRINCIPAL
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "RELATÓRIO DE PONTO", 0, 1, "C")
            
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 8, f"Funcionário: {nome}", 0, 1, "L")
            
            # Período
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 6, f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", 0, 1, "L")
            
            pdf.ln(5)
            
            # Mensagem de nenhum registro
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 8, "Nenhum registro de ponto neste período", 0, 1, "C")
            
            summary_data.append((nome, 0))
            continue
        
        df['timestamp_local'] = df['timestamp'].apply(_to_local_datetime)
        df = df.sort_values('timestamp_local')
        
        daily_data = {}
        current_entry_time = None
        
        for _, row in df.iterrows():
            ts = row['timestamp_local']
            day = ts.date()
            action = row['action']
            
            if day not in daily_data:
                daily_data[day] = {'entrada': None, 'saida': None, 'horas': 0}
            
            if action == 'entrada':
                if daily_data[day]['entrada'] is None:
                    daily_data[day]['entrada'] = ts
                current_entry_time = ts
            elif action == 'saida':
                if daily_data[day]['saida'] is None:
                    daily_data[day]['saida'] = ts
                if current_entry_time is not None:
                    duration = ts - current_entry_time
                    hours_worked = duration.total_seconds() / 3600
                    daily_data[day]['horas'] += hours_worked
                    current_entry_time = None
        
        daily_list = []
        for day in sorted(daily_data.keys()):
            data = daily_data[day]
            entrada = data['entrada'].strftime('%H:%M') if data['entrada'] else "---"
            saida = data['saida'].strftime('%H:%M') if data['saida'] else "---"
            horas = data['horas']
            daily_list.append({
                'data': day,
                'entrada': entrada,
                'saida': saida,
                'horas': horas
            })
        
        total_hours = sum(item['horas'] for item in daily_list)
        summary_data.append((nome, total_hours))
        
        # Divide em páginas se tiver mais de 31 registros
        records_per_page = 31
        for page_num, i in enumerate(range(0, len(daily_list), records_per_page)):
            pdf.add_page()
            
            page_daily_list = daily_list[i:i + records_per_page]
            page_total = sum(item['horas'] for item in page_daily_list)
            
            # CABEÇALHO PRINCIPAL
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "RELATÓRIO DE PONTO", 0, 1, "C")
            
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 8, f"Funcionário: {nome}", 0, 1, "L")
            
            # Período
            pdf.set_font("Arial", "", 11)
            if len(daily_list) > records_per_page:
                start_day = page_daily_list[0]['data'].strftime('%d/%m/%Y')
                end_day = page_daily_list[-1]['data'].strftime('%d/%m/%Y')
                pdf.cell(0, 6, f"Período: {start_day} a {end_day}", 0, 1, "L")
            else:
                pdf.cell(0, 6, f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", 0, 1, "L")
            
            pdf.ln(3)
            
            if not page_daily_list:
                pdf.set_font("Arial", "", 11)
                pdf.cell(0, 6, "Nenhum registro no período.", 0, 1, "C")
            else:
                # TABELA COM FONTE AUMENTADA
                pdf.set_font("Arial", "B", 10)
                col_width = 47.5  # A4 com margens: ~190mm / 4 colunas
                pdf.cell(col_width, 8, "Data", 1, 0, "C")
                pdf.cell(col_width, 8, "Entrada", 1, 0, "C")
                pdf.cell(col_width, 8, "Saída", 1, 0, "C")
                pdf.cell(col_width, 8, "Horas", 1, 1, "C")
                
                pdf.set_font("Arial", "", 9)
                for item in page_daily_list:
                    h = int(item['horas'])
                    m = int((item['horas'] - h) * 60)
                    pdf.cell(col_width, 7, item['data'].strftime('%d/%m/%Y'), 1, 0, "C")
                    pdf.cell(col_width, 7, item['entrada'], 1, 0, "C")
                    pdf.cell(col_width, 7, item['saida'], 1, 0, "C")
                    pdf.cell(col_width, 7, f"{h:02d}:{m:02d}", 1, 1, "C")
                
                pdf.ln(2)
                pdf.set_font("Arial", "B", 11)
                page_total_str = f"{int(page_total)}:{int((page_total % 1)*60):02d}"
                pdf.cell(0, 7, f"Total nesta página: {page_total_str}", 0, 1, "L")
                
                # Se for a última página deste funcionário, mostra total geral
                if i + records_per_page >= len(daily_list) and total_hours != page_total:
                    pdf.set_font("Arial", "B", 12)
                    total_hours_str = f"{int(total_hours)}:{int((total_hours % 1)*60):02d}"
                    pdf.cell(0, 7, f"TOTAL GERAL: {total_hours_str}", 0, 1, "L")
    
    # PÁGINA DE RESUMO GERAL
    if summary_data:
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "RESUMO GERAL DE HORAS", 0, 1, "C")
        
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}", 0, 1, "C")
        pdf.ln(4)
        
        pdf.set_font("Arial", "B", 10)
        col1_width = 100
        col2_width = 90
        pdf.cell(col1_width, 8, "Funcionário", 1, 0, "C")
        pdf.cell(col2_width, 8, "Total de Horas", 1, 1, "C")
        
        pdf.set_font("Arial", "", 9)
        for nome, total in sorted(summary_data):
            total_str = f"{int(total)}:{int((total % 1)*60):02d}"
            pdf.cell(col1_width, 7, nome, 1, 0, "L")
            pdf.cell(col2_width, 7, total_str, 1, 1, "C")
    
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