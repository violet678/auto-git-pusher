# --bibliotecas--
import threading
import logging

log = logging.getLogger(__name__) # --cria/obtem um log com o nome do modulo--

# --classificando o debouncer--
class Debouncer:
    def __init__(self, delay: float, action, *args, **kwargs):
        self.delay = delay # --segundos de espera antes de disparar a ação--
        self.action = action 
        self.args = args
        self.kwargs = kwargs
        self._timer: threading.Timer | None = None  # --cria um novo timer que chamará _fire após delay segundos
        self._lock = threading.Lock() # --evita que duas threads mecham no timer ao mesmo tempo--

# -- defininido o trigger: se chamado várias vezes, só dispara a ação uma vez depois do delay --
    def trigger(self):
        with self._lock:  # -- executa a ação trancada, porem apenas com o with --
            if self._timer is not None:
                self._timer.cancel() # -- se haver um timer armado, cancela a ação--
            self._timer = threading.Timer(self.delay, self._fire) # -- cria um delay novo --
            self._timer.daemon = True 
            self._timer.start()
            log.debug("debounce armado (%.1fs)", self.delay)

# -- classificando  o fire --
    def _fire(self):
        with self._lock:
            self._timer = None
        try:
            self.action(*self.args, **self.kwargs)
        except Exception:
            log.exception("erro na ação do debouncer")

# --o timer não vai impedir a saída e nada vai disparar depois se o programa fechar--
    def cancel(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None