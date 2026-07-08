"""
PrintQueue: cola de impresion en memoria.

Garantiza que las impresiones se procesen de a una por vez (FIFO),
evitando que dos trabajos escriban al mismo tiempo sobre una impresora.
Un unico worker asincrono consume la cola en background.
"""
import asyncio
import uuid
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.logger import get_logger
from app.drivers.base import PrinterDriver, PrinterDriverError
from app.schemas.print_schemas import JobStatus

logger = get_logger(__name__)


@dataclass
class PrintJob:
    job_id: str
    printer: str
    content: str
    driver: PrinterDriver
    status: JobStatus = JobStatus.QUEUED
    detail: str | None = None


class PrintQueue:
    """Cola FIFO de trabajos de impresion con un unico worker en background."""

    def __init__(self, max_size: int = 100) -> None:
        self._queue: asyncio.Queue[PrintJob] = asyncio.Queue(maxsize=max_size)
        self._jobs: dict[str, PrintJob] = {}
        self._worker_task: asyncio.Task | None = None

    def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("Worker de la cola de impresion iniciado")

    async def stop(self) -> None:
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
            logger.info("Worker de la cola de impresion detenido")

    async def enqueue(self, printer: str, content: str, driver: PrinterDriver) -> PrintJob:
        job = PrintJob(job_id=str(uuid.uuid4()), printer=printer, content=content, driver=driver)
        self._jobs[job.job_id] = job
        await self._queue.put(job)
        logger.info("Trabajo %s encolado para impresora '%s'", job.job_id, printer)
        return job

    def get_job(self, job_id: str) -> PrintJob | None:
        return self._jobs.get(job_id)

    async def _worker(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            job = await self._queue.get()
            job.status = JobStatus.PRINTING
            logger.info("Imprimiendo trabajo %s en '%s'", job.job_id, job.printer)
            try:
                # print_raw es bloqueante (llamadas win32print), se corre en un thread
                await loop.run_in_executor(None, job.driver.print_raw, job.printer, job.content)
                job.status = JobStatus.DONE
                logger.info("Trabajo %s finalizado correctamente", job.job_id)
            except PrinterDriverError as exc:
                job.status = JobStatus.FAILED
                job.detail = str(exc)
                logger.error("Trabajo %s fallo: %s", job.job_id, exc)
            except Exception as exc:  # salvaguarda: nunca tumbar el worker
                job.status = JobStatus.FAILED
                job.detail = f"Error inesperado: {exc}"
                logger.exception("Error inesperado procesando trabajo %s", job.job_id)
            finally:
                self._queue.task_done()


print_queue = PrintQueue(max_size=settings.queue_max_size)
