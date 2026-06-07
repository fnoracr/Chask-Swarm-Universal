import psutil

def kill_duplicates():
    print("Buscando duplicados de daemons...")
    # Group by script name
    script_pids = {}
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            if p.info['name'] in ('python.exe', 'pythonw.exe') and p.info['cmdline']:
                cmd = " ".join(p.info['cmdline']).lower()
                for arg in p.info['cmdline']:
                    if arg.endswith('.py'):
                        # exclude this script itself
                        if 'cleanup_duplicates.py' in arg:
                            continue
                        script_name = arg.split('\\')[-1].lower()
                        if script_name not in script_pids:
                            script_pids[script_name] = []
                        script_pids[script_name].append(p)
                        break
        except:
            pass

    killed = 0
    for script, procs in script_pids.items():
        if len(procs) > 1:
            print(f"Duplicados detectados: {script} ({len(procs)} instancias)")
            # Sort by create_time
            procs.sort(key=lambda x: x.info['create_time'])
            # Kill all but the last one
            for p in procs[:-1]:
                print(f"-> Matando PID {p.info['pid']}")
                try:
                    p.kill()
                    killed += 1
                except Exception as e:
                    print(f"Error matando {p.info['pid']}: {e}")
                    
    print(f"Limpieza completada. {killed} procesos antiguos terminados.")

if __name__ == "__main__":
    kill_duplicates()
