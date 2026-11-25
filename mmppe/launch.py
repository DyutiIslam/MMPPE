from __future__ import annotations
import socket, threading, time, urllib.request, os
import uvicorn

def choose_port(start=8100, end=8110):
    for port in range(start,end+1):
        with socket.socket() as s:
            try: s.bind(("127.0.0.1",port)); return port
            except OSError: pass
    raise RuntimeError("No free local port found in 8100-8110")

def open_when_ready(url):
    for _ in range(80):
        try:
            urllib.request.urlopen(url.split("showcase")[0]+"api/health",timeout=.5).close(); os.startfile(url); return
        except Exception: time.sleep(.25)

def main():
    port=choose_port(); url=f"http://127.0.0.1:{port}/"
    print("="*60); print(f"MMPPE is starting at {url}"); print(f"API documentation: {url}docs"); print("="*60)
    threading.Thread(target=open_when_ready,args=(url+"showcase",),daemon=True).start()
    uvicorn.run("mmppe.api.app:app",host="0.0.0.0",port=port,log_level="info")
if __name__ == "__main__": main()
