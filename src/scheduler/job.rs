use chrono::{DateTime, Utc};
use chrono_tz::Tz;
use cron::Schedule;
use pyo3::prelude::*;
use std::collections::HashSet;
use std::str::FromStr;
use std::time::Duration;
use uuid;

use super::retry::RetryPolicy;

#[derive(Clone)]
pub enum JobType {
    INTERVAL(Duration),
    CRON(String),
}


pub struct Job {
    id: String,
    job_type: JobType,
    last_run: Option<DateTime<Utc>>,
    last_success: Option<DateTime<Utc>>,
    task: PyObject,
    timezone: Tz,
    dependencies: HashSet<String>,
    retry_policy: Option<RetryPolicy>,
    next_retry: Option<DateTime<Utc>>,
    failed_dependencies: HashSet<String>,
}

impl Job {
    pub fn new(
        job_type: JobType,
        task: PyObject,
        timezone: Tz,
        dependencies: HashSet<String>,
        retry_policy: Option<RetryPolicy>,
    ) -> Self {
        Job {
            id: uuid::Uuid::new_v4().to_string(),
            job_type,
            last_run: None,
            last_success: None,
            task,
            timezone,
            dependencies,
            retry_policy,
            next_retry: None,
            failed_dependencies: HashSet::new(),
        }
    }

    pub fn get_id(&self) -> String {
        self.id.clone()
    }

    pub fn get_job_type(&self) -> JobType {
        self.job_type.clone()
    }

    pub fn get_task(&self) -> PyObject {
        self.task.clone()
    }

    pub fn get_last_run(&self) -> Option<DateTime<Utc>> {
        self.last_run
    }

    pub fn set_last_run(&mut self, last_run: DateTime<Utc>) {
        self.last_run = Some(last_run);
    }

    pub fn get_last_success(&self) -> Option<DateTime<Utc>> {
        self.last_success
    }
    pub fn set_last_success(&mut self, last_success: DateTime<Utc>) {
        self.last_success = Some(last_success);
    }

    pub fn get_next_retry(&self) -> Option<DateTime<Utc>> {
        self.next_retry
    }
    pub fn set_next_retry(&mut self, next_retry: Option<DateTime<Utc>>) {
        self.next_retry = next_retry;
    }

    pub fn get_retry_policy(&self) -> Option<RetryPolicy> {
        self.retry_policy.clone()
    }

    pub fn get_failed_dependencies(&self) -> HashSet<String> {
        self.failed_dependencies.clone()
    }

    pub fn get_timezone(&self) -> Tz {
        self.timezone
    }

    pub fn should_run(&self, now: DateTime<Utc>, completed_jobs: &HashSet<String>) -> bool {
        // Check dependencies
        if !self.dependencies.is_subset(completed_jobs) {
            return false;
        }

        // Check retry schedule
        if let Some(next_retry) = self.next_retry {
            if now < next_retry {
                return false;
            }
        }

        match &self.job_type {
            &JobType::INTERVAL(duration) => match self.last_run {
                None => true,
                Some(last_run) => {
                    now.signed_duration_since(last_run).to_std().unwrap() >= duration 
                }
            },
            &JobType::CRON(ref expression) =>  {
                let schedule = Schedule::from_str(expression).unwrap();
                let local_now = now.with_timezone(&self.timezone);

                match self.last_run {
                    None => true,
                    Some(last_run) => {
                        let local_last = last_run.with_timezone(&self.timezone);
                        schedule
                            .after(&local_last)
                            .take(1)
                            .next()
                            .map(|next_run| next_run <= local_now)
                            .unwrap_or(false)
                    }
                }
            }
        }
    }
}
