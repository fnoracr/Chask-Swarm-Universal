import psutil
for p in psutil.process_iter(['name', 'cmdline']):
    try:
        if 'python' in p.info['name'].lower() and p.info['cmdline'] and 'nora_queue_watcher' in ' '.join(p.info['cmdline']):
            p.kill()
            print("Killed watcher")
    except Exception as e:
        pass
