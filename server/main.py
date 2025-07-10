import subprocess
import sys
import os

if __name__ == '__main__':
    # 启动 server.py
    server_proc = subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'server.py')])
    # 启动 overlay.py
    overlay_proc = subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'overlay.py')])

    try:
        # 等待任一子进程退出
        server_exit = server_proc.wait()
        overlay_exit = overlay_proc.wait()
    except KeyboardInterrupt:
        print('Shutting down...')
        server_proc.terminate()
        overlay_proc.terminate()
    finally:
        server_proc.kill()
        overlay_proc.kill() 