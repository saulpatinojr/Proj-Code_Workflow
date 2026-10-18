# State Model

```text
queued -> dispatching -> running -> completed
                         |        -> partial
                         |        -> failed_retryable -> running
                         |        -> failed_terminal
                         |        -> blocked
queued -> blocked
queued -> skipped_optional
```

The workflow is `completed` only when every required node is `completed` and the post-validation check passes. It is `partial` when an optional node failed or was skipped but the requested outcome remains useful. It is `blocked` when a required agent, dependency, authorization, or external prerequisite is unavailable. It is `failed_terminal` when a required node failed and retry is not safe or exhausted.
