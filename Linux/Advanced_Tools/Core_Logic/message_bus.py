import zmq
import threading
import time

def start_message_bus():
    """
    Inicia un proxy ZeroMQ (XSUB/XPUB) para permitir la comunicación
    publicación/suscripción entre agentes del enjambre sin depender de Redis.
    - PUB port (donde publican los agentes): 5555
    - SUB port (donde escuchan los agentes): 5556
    """
    context = zmq.Context()

    # Frontend donde los publicadores mandan mensajes
    frontend = context.socket(zmq.XSUB)
    frontend.bind("tcp://127.0.0.1:5555")

    # Backend donde los suscriptores reciben mensajes
    backend = context.socket(zmq.XPUB)
    backend.bind("tcp://127.0.0.1:5556")

    print("[MessageBus] Iniciando Mente Colmena v2.0...")
    print("[MessageBus] Escuchando PUBs en puerto 5555")
    print("[MessageBus] Despachando a SUBs en puerto 5556")

    try:
        # zmq.proxy enruta automáticamente entre XSUB y XPUB
        zmq.proxy(frontend, backend)
    except Exception as e:
        print(f"[MessageBus] Error fatal: {e}")
    finally:
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    start_message_bus()
