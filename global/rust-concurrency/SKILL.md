---
name: rust-concurrency
description: Audit async/await and lock discipline in Rust for blocking-in-async, guards held across await, lost task panics, and unbounded channels, then restructure for correctness. Use when asked to fix deadlocks, audit async code, remove blocking calls from async fns, stop holding mutex guards across .await, bound channels, or recover lost task panics. Part of the rust-ultra Rust improvement arsenal.
---

# Rust: Async & Lock-Discipline Audit

Audit concurrency correctness and fix it by restructuring, never by sprinkling more locks. Do not change observable behavior.

1. Find every blocking or synchronous call inside an `async fn` or async block — synchronous filesystem/network I/O, heavy CPU work, `std::thread::sleep`, `Mutex::lock` on a contended std lock — and move it off the executor: hand blocking work to a blocking-thread pool, or use the runtime's async equivalent. A blocked async task starves every other task on that worker thread.
2. For each lock acquisition, trace the guard's lifetime: if a `std::sync::Mutex`/`RwLock` guard is still alive across an `.await`, fix it. Drop the guard before awaiting — scope the critical section in its own block so the guard is gone before the await point, or copy/clone out the value you need. Switch to an async-aware lock only when the lock genuinely must stay held across the await; that is the exception, not the default.
3. Check that futures required to be `Send` (anything handed to a multi-threaded `spawn`) do not capture non-`Send` state across an await; restructure so the non-`Send` value is dropped before the await rather than reaching for a manual marker.
4. Audit `Arc<Mutex<_>>` usage. When the access pattern is really "hand a value from producer to consumer", replace it with a channel; when it is a single counter or flag, replace it with an atomic; when only one task ever needs the value, replace it with plain ownership. Keep shared mutable state behind a lock only when sharing is truly required.
5. Inspect every channel for boundedness — an unbounded channel whose producer outpaces its consumer will grow until it exhausts memory. Bound channels so backpressure propagates; pick the capacity from the real producer/consumer rates.
6. For each spawned task, confirm its `JoinHandle` is kept and eventually awaited or explicitly detached. A dropped handle silently discards the task's panic and its result; surface panics by awaiting handles or aggregating them.
7. Replace busy-wait loops (spin loops polling a flag) with the proper async primitive — a notification, a channel receive, or a timer — so the executor can park the task instead of burning a core.
8. Find `.await` inside a loop that serializes independent work. If the iterations do not depend on each other, restructure to issue them concurrently and join the results, rather than awaiting each one in turn.
9. Leave correct, intentional serialization alone — ordering that the logic actually requires, locks held only across synchronous code, and bounded channels already sized for their workload. Do not parallelize work that has real data dependencies, and do not introduce concurrency where the sequential version is correct and clear.

Commit with a summary of which blocking calls were moved off the executor, which guards stopped crossing awaits, which `Arc<Mutex<_>>` were replaced, and which channels were bounded.

## Rust specifics

Drop a `MutexGuard` before `.await` by scoping it in its own `{ ... }` block, or clone the needed value out before awaiting; reach for `tokio::sync::Mutex` only when the lock must be held across an await. Offload blocking or CPU-heavy work with `tokio::task::spawn_blocking`. Prefer bounded `tokio::sync::mpsc::channel` over `unbounded_channel`. Keep `JoinHandle`s and propagate panics by awaiting them; parallelize independent futures with `tokio::join!`, `try_join!`, or `FuturesUnordered` instead of awaiting in a loop. Run `cargo check --all-targets`. If clippy is available, run `cargo clippy --all-targets` and enable `clippy::await_holding_lock` to catch std guards held across awaits.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **8** as "relevant":

| Pattern | Weight |
|---|---|
| `.await` | 1 |
| `Mutex` | 2 |
| `RwLock` | 2 |
| `tokio::spawn` | 2 |
| `block_on` | 3 |
| `Arc<` | 1 |
