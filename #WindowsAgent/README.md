# WindowsAgent

Agent para auxiliar operações no Windows, incluindo busca de chaves MAK e ativação via slmgr.

Como usar

1. Instale dependências:

```powershell
python -m pip install -r requirements.txt
```

2. Execute o agente:

```powershell
python -m src.agent.an_agent "procurar mak"
```

3. Testes:

```powershell
pytest -q
```
