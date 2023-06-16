import requests
import xml.etree.ElementTree as ET
import time
import os
import tkinter as tk
from tkinter import ttk

def add_message(message):
    global tree
    # Limpa o Treeview
    for i in tree.get_children():
        tree.delete(i)
    num_children = len(tree.get_children())
    tree.insert('', 'end', values=('Message', message), tags=('evenrow' if num_children % 2 == 0 else 'oddrow'))

def show_critical_message(message):
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal
    messagebox.showwarning("Alerta:", message)  # Exibe a caixa de mensagem
    root.destroy()  # Destrói o objeto Tk após fechar a caixa de mensagem
    
def get_new_session_id():
    while True:
        try:
            with requests.Session() as s:
                s.get('http://192.168.8.1/html/home.html')  # A URL que define o SessionID
                cookies = s.cookies.get_dict()
                session_id = cookies.get('SessionID')

            if not session_id:
                raise Exception('Não foi possível obter o SessionID.')
            
            return session_id
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout, Exception):
            add_message('Ocorreu um erro ao obter o SessionID. Tentando novamente...')
            time.sleep(1)

def is_online(url):
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()  # Verifica se a resposta foi bem-sucedida
        add_message('O HOST está online.')
        return True
    except requests.exceptions.HTTPError as http_err:
        add_message(f'Ocorreu um erro HTTP: {http_err}')
        return False
    except requests.exceptions.Timeout:
        add_message(f'Erro de tempo limite. URL {url} pode estar offline.')
        return False
    except Exception as err:
        add_message(f'Ocorreu um erro: {err}')
        return False


session_id = None
headers = {}

def get_api_data(url):
    global session_id
    global headers

    # Try to get a new session_id only if it's not set yet
    if not session_id and not is_online('http://192.168.8.1/html/home.html'):
        add_message('O HOST está offline. Tentando novamente...')
        time.sleep(1)
    elif not session_id:
        session_id = get_new_session_id()
        headers = {'Cookie': f'SessionID={session_id}'}

    try:
        response = requests.get(url, headers=headers, timeout=3)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        add_message(f'Ocorreu um erro HTTP: {http_err}')
        session_id = None  # Force the acquisition of a new session_id on the next attempt
    except requests.exceptions.Timeout:
        add_message('Ocorreu um erro de tempo limite. Tentando novamente...')
        time.sleep(1)
        session_id = None
    except Exception as err:
        add_message(f'Ocorreu um erro: {err}')
        session_id = None
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

previous_upload_rate = None
last_upload_rate_arrow = "\u2192"
previous_download_rate = None
last_download_rate_arrow = "\u2192"

def format_traffic_data(data):
    global previous_upload_rate, last_upload_rate_arrow, previous_download_rate, last_download_rate_arrow

    # Conversões de unidades
    for key in ['CurrentUpload', 'CurrentDownload', 'TotalUpload', 'TotalDownload']:
        if key in data:
            # Converte bytes para megabytes e adiciona a taxa média se aplicável
            if key in ['CurrentUpload', 'CurrentDownload'] and 'CurrentConnectTime' in data:
                mins, secs = divmod(int(data['CurrentConnectTime']), 60)
                hours, mins = divmod(mins, 60)
                connect_time_seconds = hours * 3600 + mins * 60 + secs # Convertendo o tempo de conexão atual para segundos
                average_rate = humanize_bytes_rate(int(data[key]) / connect_time_seconds) if connect_time_seconds > 0 else "0"
                data[key] = f"{humanize_bytes(int(data[key]))}. {average_rate}"
            else:
                data[key] = humanize_bytes(int(data[key]))

    for key in ['CurrentUploadRate', 'CurrentDownloadRate']:
        if key in data:
            # Converte bytes por segundo para kilobytes por segundo
            new_rate = humanize_bytes_rate(int(data[key]))

            # Adiciona seta ao final do valor
            if key == 'CurrentUploadRate':
                if previous_upload_rate is not None:
                    if new_rate > previous_upload_rate:
                        last_upload_rate_arrow = "\u2191"  # seta para cima
                    elif new_rate < previous_upload_rate:
                        last_upload_rate_arrow = "\u2193"  # seta para baixo
                    else:
                        last_upload_rate_arrow = "\u2192"  # seta direita
                previous_upload_rate = new_rate
                data[key] = f"{new_rate} {last_upload_rate_arrow}"

            elif key == 'CurrentDownloadRate':
                if previous_download_rate is not None:
                    if new_rate > previous_download_rate:
                        last_download_rate_arrow = "\u2191"  # seta para cima
                    elif new_rate < previous_download_rate:
                        last_download_rate_arrow = "\u2193"  # seta para baixo
                    else:
                        last_download_rate_arrow = "\u2192"  # seta direita
                previous_download_rate = new_rate
                data[key] = f"{new_rate} {last_download_rate_arrow}"

    # Conversão de tempo restante
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

previous_level = None
last_arrow = ""

def get_signal_level(level):
    global previous_level
    global last_arrow

    symbols = {
        '1': u'\u2581',
        '2': u'\u2581' + u'\u2583',
        '3': u'\u2581' + u'\u2583' + u'\u2584',
        '4': u'\u2581' + u'\u2583' + u'\u2584' + u'\u2586',
        '5': u'\u2581' + u'\u2583' + u'\u2584' + u'\u2586' + u'\u2588'
    }

    signal = level + " " + symbols.get(level, '-')

    if previous_level is not None and level != previous_level:
        if int(level) > int(previous_level):
            last_arrow = "\u2191" # seta para cima
        elif int(level) < int(previous_level):
            last_arrow = "\u2193" # seta para baixo
            
    previous_level = level

    signal += " " + last_arrow
    return signal


def get_data():
    info = {}  # Definimos 'info' fora do bloco try para que possamos acessá-lo no bloco except
    try:
        url1 = "http://192.168.8.1/api/monitoring/status"
        url2 = "http://192.168.8.1/api/monitoring/traffic-statistics"

        desired_keys = ['ConnectionStatus', 'SignalIcon', 'WanIPAddress', 'PrimaryDns', 'SecondaryDns', 'CurrentWifiUser', 'SimStatus', 'WifiStatus']

        # Dados da primeira API
        xml_data1 = get_api_data(url1)
        data1 = parse_xml(xml_data1)
        for key, value in data1.items():
            if key in desired_keys and value is not None:
                info[key] = value

        # Se 'ConnectionStatus' estiver em info, substitua seu valor
        if 'ConnectionStatus' in info:
            info['ConnectionStatus'] = get_connection_status(info['ConnectionStatus'])

        # Se 'SignalIcon' estiver em info, substitua seu valor
        if 'SignalIcon' in info:
            info['SignalIcon'] = get_signal_level(info['SignalIcon'])

        # Dados da segunda API
        xml_data2 = get_api_data(url2)
        data2 = parse_xml(xml_data2)
        data2 = format_traffic_data(data2)
        for key, value in data2.items():
            info[key] = value

        return info
    except Exception as e:
        print(f"Ocorreu um erro durante a execução: {e}")
        info['Erro'] = str(e)  # Adiciona a mensagem de erro à chave 'Erro'
        return info

def get_connection_status(status):
    estados = {
        '2': 'Falha na conexão, o perfil é inválido',
        '3': 'Falha na conexão, o perfil é inválido',
        '5': 'Falha na conexão, o perfil é inválido',
        '8': 'Falha na conexão, o perfil é inválido',
        '20': 'Falha na conexão, o perfil é inválido',
        '21': 'Falha na conexão, o perfil é inválido',
        '23': 'Falha na conexão, o perfil é inválido',
        '27': 'Falha na conexão, o perfil é inválido',
        '28': 'Falha na conexão, o perfil é inválido',
        '29': 'Falha na conexão, o perfil é inválido',
        '30': 'Falha na conexão, o perfil é inválido',
        '31': 'Falha na conexão, o perfil é inválido',
        '32': 'Falha na conexão, o perfil é inválido',
        '33': 'Falha na conexão, o perfil é inválido',
        '7': 'Acesso à rede não permitido',
        '11': 'Acesso à rede não permitido',
        '14': 'Acesso à rede não permitido',
        '37': 'Acesso à rede não permitido',
        '12': 'Falha na conexão, roaming não permitido',
        '13': 'Falha na conexão, roaming não permitido',
        '201': 'Falha na conexão, largura de banda excedida',
        '900': 'Conectando',
        '901': 'Conectado',
        '902': 'Desconectado',
        '903': 'Desconectando',
        '904': 'Falha na conexão ou desativada',
    }
    return estados.get(status, status)  # retorna o status se não encontrar uma correspondência no dicionário
    
def action_button():
    # Desativar o botão "Atualizar" enquanto a função está sendo executada
    button2.config(state='disabled')

    # Limpa o Treeview
    for i in tree.get_children():
        tree.delete(i)

    info = get_data()
    for i, (key, value) in enumerate(info.items()):
        tree.insert('', 'end', values=(key, value), tags=('oddrow' if i % 2 else 'evenrow',))

    # Reativar o botão "Atualizar" e agendar a próxima execução da função
    button2.config(state='normal')
    root.after(2000, action_button)

def exit_app():
    # Função para fechar a aplicação
    root.destroy()

def copy_to_clipboard(event):
    # Obtém o item selecionado
    selected_item = tree.selection()[0]
    # Obtém o valor do item selecionado
    selected_value = tree.item(selected_item)["values"][1]
    # Copia o valor para a área de transferência
    root.clipboard_clear()
    root.clipboard_append(selected_value)

root = tk.Tk()
root.geometry('600x400')
root.title("Huawei E8372h-608")


# Definir o estilo para o Treeview
style = ttk.Style()
style.configure("mystyle.Treeview", highlightthickness=0, bd=0, font=('Calibri', 11)) # Modify font size
style.configure("mystyle.Treeview.Heading", font=('Calibri', 13,'bold')) # Modify font size for headings
style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})]) # Remove borders

# Criação do Treeview com o estilo personalizado
tree = ttk.Treeview(root, style="mystyle.Treeview", columns=('Key', 'Value'), show='headings')
tree.heading('Key', text='Key')
tree.heading('Value', text='Value')

# Inserindo os dados no Treeview
info = get_data()
for i, (key, value) in enumerate(info.items()):
    tree.insert('', 'end', values=(key, value), tags=('oddrow' if i % 2 else 'evenrow',))


# Configurando a cor de fundo para as linhas ímpares e pares
tree.tag_configure('oddrow', background='#F0F0F0')
tree.tag_configure('evenrow', background='#FFFFFF')

# Adiciona um evento de clique do mouse ao Treeview
tree.bind("<Double-1>", copy_to_clipboard)

tree.grid(row=0, column=0, sticky='nsew')

# Permitir que o Treeview expanda com a janela
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Adicione botões no rodapé
button_frame = ttk.Frame(root)
button_frame.grid(row=1, column=0, padx=10, pady=10, sticky='ew')

button1 = ttk.Button(button_frame, text="Sair", command=exit_app)
button1.pack(side="right", padx=5)

button2 = ttk.Button(button_frame, text="Atualizar", command=action_button)
button2.pack(side="right", padx=5)

root.after(2000, action_button)
root.mainloop()
