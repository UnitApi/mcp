"""
Uruchamia serwer TTS na zdalnym urządzeniu przez SSH.
Wymaga: paramiko (pip install paramiko)
"""
import paramiko
import argparse
import sys
import os

parser = argparse.ArgumentParser(description="Run TTS server on remote host via SSH")
parser.add_argument("host", help="SSH host (adres IP lub nazwa)")
parser.add_argument("-u", "--user", default=os.getenv("USER"), help="SSH user (domyślnie bieżący użytkownik)")
parser.add_argument("-p", "--path", default="~/UnitApi/mcp/examples/tts/tts_server.py", help="Ścieżka do tts_server.py na zdalnym urządzeniu")
parser.add_argument("--python", default="python3", help="Komenda do uruchomienia Pythona na zdalnym urządzeniu")
args = parser.parse_args()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(args.host, username=args.user)
    print(f"[RUNNER] Łączę się z {args.user}@{args.host} ...")
    # Uruchom serwer w tle (nohup)
    cmd = f"nohup {args.python} {args.path} > tts_server.log 2>&1 &"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    print(f"[RUNNER] Serwer TTS uruchomiony na {args.host}. Log: ~/tts_server.log")
except Exception as e:
    print(f"[RUNNER][ERROR] {e}")
    sys.exit(1)
finally:
    ssh.close()
