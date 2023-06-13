import requests
import xml.etree.ElementTree as ET
import time
import os
from tqdm import tqdm

def get_new_session_id():
    with requests.Session() as s:
        s.get('http://192.168.8.1/html/home.html')  # A URL que define o SessionID
        cookies = s.cookies.get_dict()
        session_id = cookies.get('SessionID')
        
    if not session_id:
        raise Exception('Não foi possível obter o SessionID.')
    
    return session_id

def get_api_data(url):
    session_id = get_new_session_id()
    headers = {
        'Cookie': f'SessionID={session_id}'
    }

    while True:
        try:
            response = requests.get(url, headers=headers, timeout=3)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f'Ocorreu um erro HTTP: {http_err}')
        except requests.exceptions.Timeout:
            print('Ocorreu um erro de tempo limite. Tentando novamente...')
            time.sleep(1)
            continue
        except Exception as err:
            print(f'Ocorreu um outro erro: {err}')
        else:
            return response.content



def parse_xml(xml):
    root = ET.fromstring(xml)

    data = {}
    for child in root:
        data[child.tag] = child.text
    
    return data
    
def humanize_bytes_rate(byte_rate):
    bit_rate = byte_rate * 8  # Converte a taxa de bytes para a taxa de bits

    # Define as unidades e seus respectivos fatores de conversão
    byte_units = ["B/s", "KB/s", "MB/s", "GB/s"]
    bit_units = ["bps", "Kbps", "Mbps", "Gbps"]

    byte_unit = bit_unit = 0

    # Para as taxas em bytes por segundo
    while byte_rate > 1024 and byte_unit < len(byte_units) - 1:
        byte_rate /= 1024
        byte_unit += 1

    # Para as taxas em bits por segundo
    while bit_rate > 1024 and bit_unit < len(bit_units) - 1:
        bit_rate /= 1024
        bit_unit += 1

    return f"{byte_rate:.2f} {byte_units[byte_unit]} ({bit_rate:.2f} {bit_units[bit_unit]})"

        
def humanize_bytes(size):
    # Adaptado de https://stackoverflow.com/a/49361727/4842742
    # Define as unidades e seus respectivos fatores de conversão
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit = 0
    while size > 1024 and unit < len(units) - 1:
        # Enquanto o tamanho for maior que 1024, divide o tamanho por 1024 e incrementa a unidade
        size /= 1024
        unit += 1
    return f"{size:.2f} {units[unit]}"


def format_traffic_data(data):
    # Conversões de unidades
    for key in ['CurrentUpload', 'CurrentDownload', 'TotalUpload', 'TotalDownload']:
        if key in data:
            # Converte bytes para megabytes
            data[key] = humanize_bytes(int(data[key]))

    for key in ['CurrentUploadRate', 'CurrentDownloadRate']:
        if key in data:
            # Converte bytes por segundo para kilobytes por segundo
            data[key] = humanize_bytes_rate(int(data[key]))
    
    if 'CurrentConnectTime' in data:
        # Converte segundos para um formato mais legível
        mins, secs = divmod(int(data['CurrentConnectTime']), 60)
        hours, mins = divmod(mins, 60)
        data['CurrentConnectTime'] = f"{hours} horas, {mins} minutos e {secs} segundos"

    if 'TotalConnectTime' in data:
        # Converte segundos para um formato mais legível
        days, secs = divmod(int(data['TotalConnectTime']), 86400)
        hours, secs = divmod(secs, 3600)
        mins, secs = divmod(secs, 60)
        data['TotalConnectTime'] = f"{days} dias, {hours} horas, {mins} minutos e {secs} segundos"

    return data

import curses

def print_api_data_every_1_seconds(url1, url2):
    desired_keys = ['ConnectionStatus', 'SignalIcon', 'WanIPAddress', 'PrimaryDns', 'SecondaryDns', 'CurrentWifiUser', 'SimStatus', 'WifiStatus']
    
    stdscr = curses.initscr()  # Inicia o módulo curses
    curses.noecho()  # Desliga o eco automático de keys para a tela
    curses.curs_set(0)  # Esconde o cursor

    try:
        while True:
            # Redimensiona a janela para as novas dimensões do terminal
            curses.resize_term(0, 0)
            
            # Dados da primeira API
            xml_data1 = get_api_data(url1)
            data1 = parse_xml(xml_data1)
            h, w = stdscr.getmaxyx()  # Obtém as dimensões da tela
            count = 0
            for key, value in data1.items():
                if key in desired_keys and value is not None and count < h:
                    stdscr.addstr(count, 0, f"{key}: {value}" + ' ' * (w - len(f"{key}: {value}")))  # Adiciona uma string na posição especificada
                    count += 1
            
            # Dados da segunda API
            xml_data2 = get_api_data(url2)
            data2 = parse_xml(xml_data2)
            data2 = format_traffic_data(data2)
            for key, value in data2.items():
                if count < h:
                    stdscr.addstr(count, 0, f"{key}: {value}" + ' ' * (w - len(f"{key}: {value}")))
                    count += 1

            stdscr.refresh()  # Atualiza a tela com o novo conteúdo
            time.sleep(1)

    finally:
        curses.echo()
        curses.endwin()
        
url1 = "http://192.168.8.1/api/monitoring/status"
url2 = "http://192.168.8.1/api/monitoring/traffic-statistics"
os.system('cls' if os.name == 'nt' else 'clear')  # Limpa a tela
print_api_data_every_1_seconds(url1, url2)