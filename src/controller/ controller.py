
class Controller:

  	def __init__(self, kwargs):
       self.repo_manager = repo_manager()
       self.job_runner = job_runner()
       self.artifact_store = artifact_store()
       self.logger = logger()
        

    def run_pipeline(self, kwargs):
    """
    Executes the job by coordinating the repository, runner, artifact store, and logger.
    """
    # Step 0: Clone the repo
    gitrepo = RepoManager()
    gitrepo.cloneRepo(kwargs)
    # Step 1: Initialize pipeline record
    mongoadapter = MongoAdapter()
    mongoadapter.insert_pipeline(dict)
    # Step 2: Run the job in a Docker container
    job_runner = DockerInterface()
    job_id, job_status = self.job_runner.run_job(job_script)
    self.logger.log_job_state(job_id, job_status)
    # Step 3: Store the generated artifact
    mysql = MySQLAdapter()
    mysql.store(artifact)
    # Step 4: Log job completion / failure status
    # ...
    



    def stop_job(self):
      pass

    def show_or_edit_config(self):
      pass