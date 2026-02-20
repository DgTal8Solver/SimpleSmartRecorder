import os
import logging
from enum import Enum, auto
from typing import Optional
import subprocess
import win_handler

import time
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RecordState(Enum):
    IDLE = auto()
    PREPARING = auto()
    RECORDING = auto()
    FINISHING = auto()

class ProcessManager:
    """Управление внешним процессом OBS"""
    def __init__(self, exe_path : str, work_dir : str):
        self.exe_path = exe_path
        self.work_dir = work_dir
        self.process : Optional[subprocess.Popen] = None

    def start(self) -> None:
        """Запускает процесс OBS"""
        try:
            self.process = subprocess.Popen(
                [self.exe_path],
                cwd=self.work_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell = False
            )
            time.sleep(5)
            logger.info(f"Процесс запущен, PID: {self.process.pid}")
        except Exception as e:
            logger.error(f"Не удалось запустить OBS (>~<) |> {e}")
            raise

    def stop(self) -> None:
        """Корректно завершает процесс (отправляет WM_CLOSE, затем при необходимости убивает)"""
        if not self.is_running():
            logger.warning("Процесс уже завершён (O.O)")
            return
        # Безопасно пытаемся завершить процесс
        win_handler.send_key(self.process.pid, "alt+F4")
        try:
            self.process.wait(timeout=5)
            logger.info("Процесс завершён")
        except subprocess.TimeoutExpired:
            logger.warning("Процесс не ответил, принудительно убиваем \\(>o<)/")
            self.process.kill()
            self.process.wait()

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None


class RecordScheduler:
    """
    Планировщик записи на основе временных меток.
    """
    def __init__(
        self, 
        start_time : datetime.time, 
        kill_time : datetime.time, 
        prepare_duration : datetime.timedelta,
        key_for_init : str, 
        exe_path : str, 
        work_dir : str
    ) -> None:
        current_date = datetime.datetime.now().date()

        self.start_time = datetime.datetime.combine(current_date, start_time)
        self.kill_time = datetime.datetime.combine(current_date, kill_time)
        self.prepare_duration = prepare_duration   # например, timedelta(minutes=2)
        self.key_for_init = key_for_init
        self.process_manager = ProcessManager(exe_path, work_dir)
        self.state = RecordState.IDLE
        self.is_recording = False

    def _get_prepare_start(self) -> datetime:
        """Момент начала подготовки (за prepare_duration до start_time)"""
        return self.start_time - self.prepare_duration

    def run(self) -> None:
        """
        Основной цикл планировщика. Завершается после окончания записи и закрытия процесса.
        """
        logger.info(f"Планировщик запущен. Старт записи: {self.start_time}, окончание: {self.kill_time}")
        self.state = RecordState.IDLE

        while self.state != RecordState.FINISHING:
            now = datetime.datetime.now()
            self._update_state(now)
            self._execute_state_actions()
            # Небольшая задержка для снижения нагрузки
            time.sleep(0.1)

        logger.info("Планировщик завершил работу (~^b^)~")

    def _update_state(self, now : datetime.datetime) -> None:
        """Определяет новое состояние на основе текущего времени"""
        prepare_start = self._get_prepare_start()
        
        if now >= self.kill_time or (self.is_recording and not self.process_manager.is_running()):
            self.state = RecordState.FINISHING
        elif now >= self.start_time:
            if self.state != RecordState.RECORDING:
                self.state = RecordState.RECORDING
        elif now >= prepare_start:
            if self.state != RecordState.PREPARING:
                self.state = RecordState.PREPARING
        else:
            self.state = RecordState.IDLE

    def _execute_state_actions(self) -> None:
        """Выполняет действия, соответствующие текущему состоянию"""
        match self.state:
            case RecordState.IDLE:
                return
            case RecordState.PREPARING:
                if self.process_manager.process is not None:
                    return
                
                logger.info("Начало подготовки. Запускаем OBS (~o.o)~")
                self.process_manager.start()
                # Можно также активировать окно для удобства
                if self.process_manager.process:
                    win_handler.activate(self.process_manager.process.pid)
            
            case RecordState.RECORDING:
                if self.is_recording:
                    return
                # Убедимся, что процесс запущен (на случай, если подготовка была пропущена)
                if self.process_manager.process is None:
                    self.process_manager.start()
                
                if not self.process_manager.is_running():
                    logger.error("Процесс OBS не запущен, невозможно начать запись (;-;)")
                    return
                # Активируем окно и отправляем клавишу старта
                win_handler.send_key(self.process_manager.process.pid, self.key_for_init)
                self.is_recording = True
                logger.info("Запись началась (*v*)")
                
            case RecordState.FINISHING:
                if not self.is_recording:
                    return
                
                self.is_recording = False
                if not self.process_manager.is_running():
                    logger.warning("Процесс уже не работает (;-;)")
                    return
                
                win_handler.send_key(self.process_manager.process.pid, self.key_for_init)
                logger.info("Запись остановлена (~^b^)~")
                # Даём время на сохранение
                time.sleep(5)
                # Завершаем процесс OBS
                self.process_manager.stop()