use std::time::Duration;


#[derive(Clone)]
pub struct RetryPolicy {
    max_retries: u32,
    retry_delay: Duration,
    exponential_backoff: bool,
    current_retry: u32,
}

impl RetryPolicy {
    pub fn new(max_retries: u32, retry_delay_secs: u64, exponential_backoff: bool) -> Self {
        RetryPolicy {
            max_retries,
            retry_delay: Duration::from_secs(retry_delay_secs),
            exponential_backoff,
            current_retry: 0,
        }
    }

    pub fn get_next_retry_delay(&self) -> Duration {
        if self.exponential_backoff {
            self.retry_delay * 2u32.pow(self.current_retry)
        } else {
            self.retry_delay
        }
    }

    pub fn get_current_retry(&self) -> u32 {
        self.current_retry
    }

    pub fn set_current_retry(&mut self, retry: u32) {
        self.current_retry = retry;
    }

    pub fn get_max_retries(&self) -> u32 {
        self.max_retries
    }
    
    pub fn increase_current_retry(&mut self) {
        self.current_retry += 1;
    }

}