from datetime import datetime
import time
import threading
from typing import Union

from singleton_decorator import singleton

from socaity_router.core.Job import InternalJob, JOB_STATUS


@singleton
class JobQueue:
    def __init__(self):
        self.queue = []
        self.in_progress = []  # a list of {"job_id": job.id, "thread": t_job, "job": job}
        self.results = []
        self.worker_thread = threading.Thread(target=self.do_work, daemon=True)

        # used to store the queue size for each function.
        # Limits the number of jobs that can be created for a specific path / function
        self.queue_sizes = {}  # a dictionary of {path: queue_size}

    def set_queue_size(self, job_function: callable, queue_size: int):
        self.queue_sizes[job_function.__name__] = queue_size

    def add_job(
        self,
        job_function: callable,
        job_params: dict = None
    ):
        job = InternalJob(
            job_function=job_function,
            job_params=job_params
        )
        # check if queue size is reached
        if self.queue_sizes.get(job_function.__name__, 1) <= len([j for j in self.queue if j.job_function == job_function]):
            job.status = JOB_STATUS.FAILED
            job.result = f"Queue size for function {job_function.__name__} reached."
            self.results.append(job)
            return job

        # add job to queue
        job.status = JOB_STATUS.QUEUED
        self.queue.append(job)

        # start worker thread if not already done so
        if not self.worker_thread.is_alive():
            self.worker_thread.start()

        return job

    def process_job(self, job: InternalJob):
        job.execution_started_at = datetime.utcnow()
        job.status = JOB_STATUS.PROCESSING
        job.result = job.job_function(**job.job_params)
        job.execution_finished_at = datetime.utcnow()
        job.status = JOB_STATUS.FINISHED
        # store result in results. Necessary in threading because thread itself cannot easily return values
        self.results.append(job)

    def do_work(self):
        while True:
            if len(self.queue) == 0 and len(self.in_progress) == 0:
                time.sleep(2)

            # create new jobs from queue
            for job in self.queue:
                t_job = threading.Thread(target=self.process_job, args=(job,), daemon=True)
                t_job.start()

                self.in_progress.append({"job_id": job.id, "thread": t_job, "job": job})
                self.queue.remove(job)

            # check if jobs are finished
            for job_thread in self.in_progress:
                # remove finished jobs
                if not job_thread["thread"].is_alive():
                    self.in_progress.remove(job_thread)

                # remove timeout jobs
                if job_thread["job"].time_out_at < datetime.utcnow():
                    # set status to failed
                    j = job_thread["job"]
                    j.status = JOB_STATUS.TIMEOUT
                    # kill thread
                    job_thread["thread"].kill()
                    self.in_progress.remove(job_thread)

                    self.results.append(j)

    def get_job(self, job_id: str) -> Union[InternalJob, None]:
        """
        Get a job by its id. Returns None if the job does not exist.
        """
        # check if in results
        job = next((job for job in self.results if job.id == job_id), None)
        if job:
            return job

        # check if in progress
        job = next((th['job'] for th in self.in_progress if th["job_id"] == job_id), None)
        if job:
            return job

        # return if in queue
        return next((job for job in self.queue if job.id == job_id), None)

    async def wait_for_job_to_finish(self, job_id: str) -> Union[InternalJob, None]:
        job = self.get_job(job_id)
        if job is None:
            return None

        while job.status != JOB_STATUS.FINISHED:
            time.sleep(1)

        return job