# Async and Concurrency Profile

Inspect every `async fn`, async block, lock, channel, and spawned task.

- Move synchronous filesystem/network I/O, heavy CPU work, thread sleeps, and
  blocking locks off the executor or use the runtime equivalent.
- Ensure `Mutex`/`RwLock` guards do not live across `.await`; scope or copy the
  required value before awaiting.
- Check that futures passed to multithreaded spawn are `Send` without unsafe
  marker implementations.
- Replace unnecessary `Arc<Mutex<_>>` with ownership, atomics, or channels.
- Bound channels and choose capacity from producer/consumer behavior.
- Retain and await `JoinHandle`s, or explicitly document detached tasks and
  their panic/result handling.
- Replace busy waits with notifications, receives, or timers. Parallelize
  independent loop iterations only when ordering is not a real dependency.

Leave intentional serialization and correctly scoped locks alone. Run
`cargo check --all-targets` and `cargo test` after changes.

Useful signals: `.await`, `Mutex`, `RwLock`, `tokio::spawn`, `block_on`, and
`Arc<`.
