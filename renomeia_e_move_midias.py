import obspython as obs
from datetime import datetime, timedelta
import logging
import os
import shutil
from pathlib import Path
import easygui

# CONFIGURACOES:
# CAMINHOS DE ACORDO COM O PERFIL
profile_paths = {
    "RECEPCAO": {
        "pasta_origem": "C:\\teste\\LOCAL\\RECEPCAO",
        "pasta_destino": "C:\\teste\\RECEPCAO",
        "pasta_cache": "C:\\teste\\CACHE\\RECEPCAO",
    },
    "JORNAL": {
        "pasta_origem": "C:\\teste\\LOCAL\\JORNAL",
        "pasta_destino": "C:\\teste\\JORNAL",
        "pasta_cache": "C:\\teste\\CACHE\\JORNAL",
    },
    "JORNAL LIMPO": {
        "pasta_origem": "C:\\teste\\LOCAL\\JORNAL LIMPO",
        "pasta_destino": "C:\\teste\\JORNAL LIMPO",
        "pasta_cache": "C:\\teste\\CACHE\\JORNAL LIMPO",
    },
}

def diadasemana(dias_pra_frente: int = 0) -> str:
    """Retorna o dia da semana no formato do nome das pastas."""
    data = (datetime.today() + timedelta(days=dias_pra_frente)).weekday()
    dias_semana = [
        '1-Segunda-feira', '2-Terca-feira', '3-Quarta-feira',
        '4-Quinta-feira', '5-Sexta-feira', '6-Sabado', 'Domingo'
    ]
    return dias_semana[data]

# INICIALIZANDO O SCRIPT
class Data:
    _template_ = "[name]"  # Template padrao
    _name_ = None

if __name__ == "__main__":
    script_load(None)  # Chama o script_load para inicializar

def script_load(settings):
    """Carrega o script e adiciona o callback para eventos."""
    configure_logging()
    obs.obs_frontend_add_event_callback(on_event)
    logging.info("Script de OBS iniciado.")

def configure_logging():
    """Configura o sistema de logging."""
    if not os.path.isdir('logs'):
        os.mkdir('logs')
    logging.basicConfig(
        filename="logs\\log.log",
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO,
        force=True
    )

def fill_template(template, name, num):
    """Substitui placeholders no template pelo nome e numero."""
    template = template.replace("[name]", name)
    template = template.replace("[date]", datetime.now().strftime("%m-%d"))
    template = template.replace("[time]", datetime.now().strftime("%H-%M"))
    template = template.replace("[num]", str(num))
    return template

# FUNCAO QUE E ATIVADA QUANDO PARAR A GRAVACAO
def on_event(event):
    """Callback para eventos do OBS."""
    if event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        current_profile = get_current_profile()
        logging.info(f"Perfil ativo: {current_profile}")

        if current_profile == "RECEPCAO":
            ask_for_name_and_move_file()
        elif current_profile in ["JORNAL", "JORNAL LIMPO"]:
            move_files_without_prompt()
        else:
            logging.info(f"Perfil '{current_profile}' nao configurado para acoes automaticas.")

# FUNCOES AUXILIARES
def get_current_profile():
    """Retorna o nome do perfil atualmente selecionado no OBS."""
    return obs.obs_frontend_get_current_profile()

def get_paths_for_current_profile():
    """Obtem os caminhos das pastas para o perfil atualmente selecionado."""
    current_profile = get_current_profile()
    if current_profile in profile_paths:
        return profile_paths[current_profile]
    else:
        logging.error(f"Perfil '{current_profile}' nao encontrado. Usando caminho padrao.")
        # Retorne valores padrao ou uma estrutura de erro
        return profile_paths["JORNAL LIMPO"]  # Ou um caminho padrao

def get_recorded_file():
    """Retorna o arquivo gravado pelo OBS."""
    output = obs.obs_frontend_get_recording_output()
    output_settings = obs.obs_output_get_settings(output)
    path = obs.obs_data_get_string(output_settings, 'path')
    file_path = Path(path)
    obs.obs_data_release(output_settings)
    obs.obs_output_release(output)
    return file_path

# MOVIMENTACAO DAS MIDIAS
def ask_for_name_and_move_file():
    """Pergunta o nome ao usuario e move o arquivo gravado."""
    file = get_recorded_file()
    input_name = easygui.enterbox("Título da gravacao", "OBS", Data._name_)

    if input_name:
        Data._name_ = input_name
        new_name = fill_template(Data._template_, Data._name_, 0)
        file_rename(file, new_name)
        logging.info(f"Arquivo renomeado para: {new_name}")

    paths = get_paths_for_current_profile()
    pasta_origem = paths["pasta_origem"]
    pasta_destino = paths["pasta_destino"]
    pasta_cache = paths["pasta_cache"]
    dds = diadasemana(0)
    # Forma a pasta com o dia da semana (ex: \\pasta_fonte vira \\pasta_fonte\1-Segunda-feira)
    pasta_destino_dds = os.path.join(pasta_destino, dds)

    if not os.path.isdir(pasta_destino_dds):
        os.mkdir(pasta_destino_dds)

    for arquivo in os.listdir(pasta_origem):
        copia = 1
        nome_arquivo, extensao = os.path.splitext(arquivo)
        arquivo_destino = os.path.join(pasta_destino_dds, arquivo)
        arquivo_origem = os.path.join(pasta_origem,arquivo)
        arquivo_cache = os.path.join(pasta_cache,arquivo)

        while(os.path.exists(arquivo_cache)):
            copia+=1
            arquivo_cache = os.path.join(pasta_cache, f"{nome_arquivo} {copia}{extensao}")
            arquivo_destino = os.path.join(pasta_destino_dds, f"{nome_arquivo} {copia}{extensao}")

        try:
           shutil.move(arquivo_origem,arquivo_cache)
        except Exception as e:
            print(e)
            break
        else:
            shutil.copy(arquivo_cache,arquivo_destino)

def move_files_without_prompt():
    """Realiza a movimentacao dos arquivos sem perguntar por um nome, de acordo com o perfil."""
    logging.info("Iniciando movimentacao de arquivos sem prompt de nome.")
    current_profile = get_current_profile()  # Obtem o perfil atual
    paths = get_paths_for_current_profile()  # Obtem os caminhos das pastas
    pasta_origem = paths["pasta_origem"]
    pasta_destino = paths["pasta_destino"]
    pasta_cache = paths["pasta_cache"]

    dds = diadasemana(0)
    pasta_destino_dds = os.path.join(pasta_destino, dds)

    os.makedirs(pasta_destino_dds, exist_ok=True)
    logging.info(f"Criou pasta: {pasta_destino_dds}")

    data_atual = datetime.now()
    dia_atual = data_atual.day
    mes_atual = data_atual.month
    ano_atual = data_atual.year

    for arquivo in os.listdir(pasta_origem):
        bloco = 1
        nome_arquivo, extensao = os.path.splitext(arquivo)
        arquivo_origem = os.path.join(pasta_origem, arquivo)

        # Define o nome de destino com base no perfil
        if current_profile == "JORNAL":
            # Para o perfil JORNAL, renomeia o arquivo
            arquivo_destino = os.path.join(
                pasta_destino_dds, 
                f"MDPR {dia_atual} {mes_atual} {ano_atual} BL{bloco}{extensao}"
            )
            # Garante que o nome de destino nao exista
            while os.path.exists(arquivo_destino):
                bloco += 1
                arquivo_destino = os.path.join(
                    pasta_destino_dds, 
                    f"MDPR {dia_atual} {mes_atual} {ano_atual} BL{bloco}{extensao}"
                )
        elif current_profile == "JORNAL LIMPO":
            # Para o perfil JORNAL LIMPO, renomeia com o formato especificado
            arquivo_destino = os.path.join(
                pasta_destino_dds, 
                f"MDPR LIMPO {dia_atual} {mes_atual} {ano_atual} BL{bloco}{extensao}"
            )
            # Garante que o nome de destino nao exista
            while os.path.exists(arquivo_destino):
                bloco += 1
                arquivo_destino = os.path.join(
                    pasta_destino_dds, 
                    f"MDPR LIMPO {dia_atual} {mes_atual} {ano_atual} BL{bloco}{extensao}"
                )
        else:
            logging.info(f"Perfil '{current_profile}' nao configurado para movimentacao.")
            return

        try:
            shutil.move(arquivo_origem, arquivo_destino)
            logging.info(f"Movido: {arquivo_origem} -> {arquivo_destino}")
            # Copia para o cache apos mover
            shutil.copy(arquivo_destino, os.path.join(pasta_cache, arquivo))
            logging.info(f"Copiado para cache: {arquivo_destino} -> {pasta_cache}")
        except Exception as e:
            logging.error(f"Erro ao mover/copiar {arquivo_origem}: {e}")

def file_rename(file, new_name):
    """Renomeia o arquivo para o novo nome."""
    try:
        file.rename(Path(file.parent, new_name + file.suffix))
    except FileExistsError:
        copia = 1
        while os.path.exists(Path(file.parent, new_name + " " + str(copia) + file.suffix)):
            copia += 1
        file.rename(Path(file.parent, new_name + " " + str(copia) + file.suffix))