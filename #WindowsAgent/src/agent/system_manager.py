#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SystemManager adapted and cleaned from user's system_manager.py
"""
import subprocess
import logging
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


class SystemManager:
    def __init__(self, config_path=None):
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        # Comandos permitidos por padrão
        self.allowed_commands = {
            'systeminfo': True,
            'slmgr': True,
            'dir': True,
            'whoami': True,
            'op': True  # 1Password CLI
        }
        # Verifica se o 1Password CLI está instalado
        self._check_1password_cli()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('system_manager.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('SystemManager')

    def _load_config(self, config_path):
        if not config_path:
            return {}
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            return {}

    def _validate_command(self, command):
        """Valida se o comando é permitido e seguro."""
        command_type = command.split()[0].lower()
        if command_type not in self.allowed_commands:
            self.logger.warning(f"Comando não permitido: {command_type}")
            return False
        return True

    def execute_command(self, command, capture_output=True):
        """Executa um comando do sistema de forma segura."""
        if not self._validate_command(command):
            return {
                "status": "error",
                "message": "Comando não permitido",
                "command": command
            }

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True
            )

            output = {
                "status": "success" if result.returncode == 0 else "error",
                "returncode": result.returncode,
                "command": command,
                "timestamp": datetime.now().isoformat()
            }

            if capture_output:
                output.update({
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })

            self.logger.info(f"Comando executado: {command}")
            return output

        except Exception as e:
            self.logger.error(f"Erro ao executar comando: {e}")
            return {
                "status": "error",
                "message": str(e),
                "command": command
            }

    def get_system_info(self):
        """Obtém informações do sistema."""
        try:
            info = {}

            # Informações do Windows
            windows_info = self.execute_command('systeminfo')
            if windows_info["status"] == "success":
                info["windows"] = windows_info["stdout"]

            # Status de ativação
            activation = self.execute_command('slmgr /dlv')
            if activation["status"] == "success":
                info["activation"] = activation["stdout"]

            return {
                "status": "success",
                "data": info,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Erro ao obter informações do sistema: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def search_mak_keys(self, search_path=None):
        """Procura por possíveis chaves MAK no sistema ou em um diretório específico."""
        try:
            results = {
                "system_info": {},
                "found_keys": [],
                "search_locations": []
            }

            # Verifica informações do sistema
            result = self.execute_command('slmgr /dlv')
            if result["status"] == "success":
                results["system_info"] = self._parse_license_info(
                    result["stdout"])

            # Se um caminho de busca foi fornecido
            if search_path:
                path = Path(search_path)
                if not path.exists():
                    return {
                        "status": "error",
                        "message": f"Caminho não encontrado: {search_path}"
                    }

                results["search_locations"].append(str(path))
                self._search_keys_in_path(path, results)

            return {
                "status": "success",
                "data": results,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error("Erro ao procurar chaves MAK: %s", str(e))
            return {
                "status": "error",
                "message": str(e)
            }

    def _parse_license_info(self, output):
        """Analisa as informações de licença do output do slmgr."""
        info = {
            "product_key": None,
            "license_status": None
        }

        for line in output.split('\n'):
            if "chave do produto:" in line.lower():
                info["product_key"] = line.split(":")[-1].strip()
            elif "status da licença:" in line.lower():
                info["license_status"] = line.split(":")[-1].strip()

        return info

    def _search_keys_in_path(self, path, results):
        """Procura por chaves MAK em arquivos de texto em um diretório."""
        # Padrão para chaves do Windows (5 grupos de 5 caracteres separados por hífen)
        key_pattern = re.compile(r'([A-Z0-9]{5}-){4}[A-Z0-9]{5}')

        try:
            if path.is_file():
                self._search_keys_in_file(path, key_pattern, results)
            else:
                for item in path.rglob("*"):
                    if item.is_file() and item.suffix.lower() in ['.txt', '.log', '.csv', '.ini']:
                        self._search_keys_in_file(item, key_pattern, results)

        except Exception as e:
            self.logger.error("Erro ao procurar em %s: %s", path, str(e))

    def _search_keys_in_file(self, file_path, key_pattern, results):
        """Procura por chaves MAK em um arquivo específico."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                matches = key_pattern.finditer(content)

                for match in matches:
                    key = match.group()
                    if key not in [k["key"] for k in results["found_keys"]]:
                        results["found_keys"].append({
                            "key": key,
                            "file": str(file_path),
                            "found_at": datetime.now().isoformat()
                        })

        except Exception as e:
            self.logger.error("Erro ao ler arquivo %s: %s", file_path, str(e))

    def _check_1password_cli(self):
        """Verifica se o 1Password CLI está instalado e configurado."""
        try:
            result = subprocess.run(
                ['op', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("1Password CLI encontrado: %s",
                                 result.stdout.strip())
                self.op_available = True
            else:
                self.logger.warning("1Password CLI não está disponível")
                self.op_available = False
        except FileNotFoundError:
            self.logger.warning("1Password CLI não está instalado")
            self.op_available = False
        except Exception as e:
            self.logger.error("Erro ao verificar 1Password CLI: %s", str(e))
            self.op_available = False

    def get_mak_from_1password(self, item_name: str = "Windows MAK") -> Optional[str]:
        """Recupera uma chave MAK do 1Password."""
        if not self.op_available:
            return None

        try:
            # Tenta obter o item do 1Password
            result = subprocess.run(
                ['op', 'item', 'get', item_name, '--format', 'json'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                item_data = json.loads(result.stdout)
                # Procura pela chave MAK nos campos
                for field in item_data.get('fields', []):
                    if field.get('label', '').lower() in ['mak', 'key', 'chave']:
                        return field.get('value')

                # Se não encontrou nos campos, tenta no campo de senha
                if 'password' in item_data:
                    return item_data['password']

            return None

        except Exception as e:
            self.logger.error("Erro ao acessar 1Password: %s", str(e))
            return None

    def save_mak_to_1password(self, key: str, title: str = "Windows MAK") -> bool:
        """Salva uma chave MAK no 1Password."""
        if not self.op_available:
            return False

        try:
            # Cria um novo item no 1Password
            template = {
                'title': title,
                'category': 'PASSWORD',
                'fields': [
                    {
                        'id': 'mak',
                        'type': 'STRING',
                        'label': 'MAK',
                        'value': key,
                        'purpose': 'PASSWORD'
                    }
                ]
            }

            # Salva o item
            result = subprocess.run(
                ['op', 'item', 'create', '--template', json.dumps(template)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.logger.info("Chave MAK salva com sucesso no 1Password")
                return True
            else:
                self.logger.error(
                    "Erro ao salvar chave no 1Password: %s", result.stderr)
                return False

        except Exception as e:
            self.logger.error("Erro ao salvar no 1Password: %s", str(e))
            return False

    def activate_windows(self, key):
        """Ativa o Windows usando uma chave fornecida."""
        if not key or len(key) != 29:  # Chaves do Windows têm 29 caracteres
            return {
                "status": "error",
                "message": "Chave inválida"
            }

        try:
            # Instala a chave
            install_key = self.execute_command(f'slmgr /ipk {key}')
            if install_key["status"] != "success":
                return install_key

            # Ativa o Windows
            activate = self.execute_command('slmgr /ato')
            if activate["status"] != "success":
                return activate

            # Verifica o status da ativação
            verify = self.execute_command('slmgr /dlv')

            return {
                "status": "success",
                "message": "Windows ativado com sucesso",
                "verification": verify.get("stdout", "")
            }

        except Exception as e:
            self.logger.error(f"Erro durante a ativação do Windows: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
