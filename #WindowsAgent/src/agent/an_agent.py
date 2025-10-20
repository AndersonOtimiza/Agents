#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main agent wrapper adapted from the user's #An_Agent.py
"""
import json
import sys
from datetime import datetime

# Tentativas de import em ordem (relativo -> absoluto)
try:
    from .system_manager import SystemManager
except ImportError:
    try:
        from src.agent.system_manager import SystemManager
    except ImportError:
        # fallback histórico
        from agent.system_manager import SystemManager


def write_log(entry):
    """Escreve um log da operação."""
    with open("agent.log", "a", encoding="utf-8") as f:
        timestamp = datetime.utcnow().isoformat() + "Z"
        f.write(f"{timestamp}: {entry}\n")


def process_system_command(command, system_manager):
    """Processa comandos relacionados ao sistema."""
    cmd_parts = command.lower().split()

    if 'procurar' in cmd_parts and 'mak' in cmd_parts:
        # Se um caminho foi fornecido no comando
        path_parts = [p for p in cmd_parts[cmd_parts.index(
            'mak')+1:] if p not in ['em', 'no', 'na', 'pasta', 'diretório']]
        search_path = ' '.join(path_parts) if path_parts else None

        if not search_path:
            prompt = (
                "Em qual local você deseja procurar a chave MAK? "
                "(Pressione Enter para buscar apenas no sistema)"
            )
            print(prompt)
            search_path = input().strip() or None

        result = system_manager.search_mak_keys(search_path)
        if result["status"] == "success" and result["data"]["found_keys"]:
            # Encontrou chaves, pergunta se deseja usar alguma delas
            print("\nChaves MAK encontradas:")
            for i, key_info in enumerate(result["data"]["found_keys"], 1):
                print(
                    f"{i}. {key_info['key']} "
                    f"(encontrada em {key_info['file']})"
                )

            print(
                "\nDeseja usar alguma dessas chaves para ativar o "
                "Windows? (Digite o número ou N para não)"
            )
            choice = input().strip().lower()

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(result["data"]["found_keys"]):
                    selected_key = result["data"]["found_keys"][idx]["key"]
                    activation_result = (
                        system_manager.activate_windows(selected_key)
                    )
                    return {"OUTPUT_EXECUTIVO": {
                        "status": "success",
                        "search_result": result,
                        "activation_result": activation_result
                    }}

        return {"OUTPUT_EXECUTIVO": result}

    if 'status' in cmd_parts:
        result = system_manager.get_system_info()
        return {"OUTPUT_EXECUTIVO": result}

    elif 'ativar' in cmd_parts and 'windows' in cmd_parts:
        # Procura por uma chave no comando
        key_parts = [p for p in cmd_parts if len(p) == 29 and '-' in p]
        if key_parts:
            result = system_manager.activate_windows(key_parts[0])
            return {"OUTPUT_EXECUTIVO": result}
        else:
            return {"OUTPUT_EXECUTIVO": {
                "status": "error",
                "message": "Chave de ativação não fornecida ou inválida"
            }}

    elif 'executar' in cmd_parts:
        # Remove a palavra 'executar' do comando
        actual_command = ' '.join(cmd_parts[cmd_parts.index('executar')+1:])
        if actual_command:
            result = system_manager.execute_command(actual_command)
            return {"OUTPUT_EXECUTIVO": result}
        else:
            return {"OUTPUT_EXECUTIVO": {
                "status": "error",
                "message": "Comando não especificado"
            }}

    return {"OUTPUT_EXECUTIVO": {
        "status": "error",
        "message": "Comando do sistema não reconhecido",
        "comando_original": command
    }}


def main():
    system_manager = SystemManager()  # Inicializa o gerenciador do sistema

    if len(sys.argv) == 1:
        print(
            "Aguardando entrada de texto via stdin.\n"
            "Digite seu comando e pressione Ctrl+D (Linux/Mac)\n"
            "ou Ctrl+Z e depois Enter (Windows) para finalizar.",
            file=sys.stderr
        )
        try:
            text = sys.stdin.read().strip()
        except KeyboardInterrupt:
            print("\nInterrupção pelo usuário. Encerrando.", file=sys.stderr)
            return
    else:
        text = " ".join(sys.argv[1:])

    if not text:
        print("Por favor, forneça um comando.")
        return

    write_log(f"Comando recebido: {text}")

    result = process_system_command(text, system_manager)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
