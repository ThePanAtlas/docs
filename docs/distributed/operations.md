# Operations

How the two panAtlas Cresco agents are supervised, what has gone wrong, and how to recover. Every guard on this page
exists because of a specific outage. Sources: `web/mesh/deploy/` (units, scripts, README) and the dated incident
records.

## Standing rules

- **Nothing heavy runs on the HPC cluster login node.** The cluster agent runs there under the user's own systemd,
  and so does the scheduling (`squeue`, `sacct`, `sbatch`). Everything else, including manifest walks, store builds
  and queries, runs in a Slurm job. CPU jobs go to a CPU partition so they never hold a GPU node.
- **One `filerepo` bundle per agent**: the system one. Never deploy a second.
- **Persistence off for managers.** The ensure timer brings managers back, not the agent.
- **Presence is not liveness.** A manager is up only if it answers `getgraphinventory`.
- **Verify, do not trust replies.** An empty add reply proves nothing either way. Re-list and probe.

## What runs where

### HPC cluster (login node, `systemd --user` with linger)

The cluster has no root access and cron there was unreliable, so supervision uses user systemd with linger enabled.

| Unit | Schedule | Does |
|---|---|---|
| `panatlas-agent.service` | always (`Restart=always`, `RestartSec=8`) | Runs the Cresco agent (`-Dis_agent=true -Dregionname=panatlas-global`). `ExecStartPre` deletes stale Derby `db.lck` and `dbex.lck` |
| `panatlas-agent-watchdog.timer` → `.service` | every 5 min | `dgx-agent-watchdog.sh`: restart the agent if its log gained Derby/`DBEngine` errors in the last 15 min and it was not restarted in the last 30 |
| `panatlas-refresh.timer` → `.service` | 15 min after boot, then hourly | Manifest re-audit (`dataset_manifest.py build --update-registry`) and report regeneration (`build_dataset_reports.py`) |
| `panatlas-ct-rewalk.timer` → `.service` | Sundays 03:00 | Submits the CT corpus full re-walk as a Slurm job (`ct_native_manifest.sbatch`) |

**JVM hardening** on the agent (also in `dgx-start.sh`, kept only as a manual-start reference):
`-Xss512k -XX:MaxMetaspaceSize=256m -XX:+UseG1GC`, `LimitSTACK=8388608` (8 MB) and `LimitNOFILE=65536`. The login
node uses strict memory overcommit. An inherited unlimited stack let a thread leak turn into a fatal native-thread
out-of-memory error, and capping per-thread stacks prevents that.

Enable once:

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user daemon-reload
systemctl --user enable --now panatlas-agent.service panatlas-agent-watchdog.timer \
                               panatlas-refresh.timer panatlas-ct-rewalk.timer
```

### Web host (system systemd)

| Unit | Schedule | Does |
|---|---|---|
| `cresco.service` + `override.conf` | always (`Restart=on-failure`) | The web host's Cresco agent with the wsapi enabled. The override adds the same `-Xss512k` and `LimitSTACK` hardening |
| `panatlas-mesh.service` | always | `mesh_daemon.py`: writes `mesh.json` for the Mesh view |
| `panatlas-ensure-managers.timer` → `.service` | 10 min after boot, then every 15 min | `ensure_managers.sh` → `deploy_managers.py`: probe, re-add, verify; self-heal on exit 3. Log: `ensure-managers.log` beside the script |

## Failure modes and their guards

Six federation outages are on record. Each one produced a guard that is still in place.

### A second `filerepo` bundle

**When:** 2026-07-31. **Symptom:** the cluster agent crash-looped and dropped off the mesh, leaving 1 of 22 managers
reachable.

**Cause:** reports were first shipped over a second, patched `io.cresco.filerepo` bundle beside the agent's system
`filerepo`. That put two Derby engines, in two OSGi class loaders, on the same database. They fought over the boot
about 2.7 times a second and leaked a `derby.rawStoreDaemon` thread each time, reaching about 32,000 threads and
`OutOfMemoryError: unable to create native thread`. The old watchdog, `pgrep -f "agentname=…"`, matched its own
shell wrapper, so it always "found" the dead agent.

**Guard:** reports moved to MsgEvent pull (`getgraphinventory`). `filerepo` is for large artifacts only, through
the single system bundle. Supervision moved from cron to systemd.

**Recovery if `rawStoreDaemon` threads climb:**

1. Confirm with `cat /proc/<pid>/task/*/comm | grep -c rawStoreD` (`comm` is truncated to `derby.rawStoreD`).
2. Remove any non-system `io.cresco.filerepo` instance or `panatlas-reports` pipeline.
3. Restart the agent. Orphaned Derby threads do not die when the plugin is removed.
4. Managers return through the ensure timer.

### Stale Derby locks (the wedge)

**When:** 2026-09-10 and overnight 2026-09-16/17. **Symptom:** the agent JVM stays alive and its health check
keeps printing `OK`, but the controller database will not boot ("Another instance of Derby may have already booted
the database"). The agent drops off the mesh and its managers are not restored (21 of 33 came back on 2026-09-17).

**Cause:** the controller's Derby database sits on a shared parallel filesystem. After an unclean JVM exit, the next
start finds `db.lck` and `dbex.lck` and refuses to boot.

**Guard:** `ExecStartPre` removes both lock files. systemd runs it only after the previous main process is gone, so
no live instance can hold them. The 5-minute watchdog restarts the agent once per 30-minute cooldown when Derby
errors reappear, and logs to `cresco/watchdog.log`.

### Persisted-plugin runaway

**When:** found 2026-09-17. **Symptom:** after a restart the agent began starting **4,971** panAtlas manager
instances (33 intended) at about three a second. Threads passed 4,300 and the Mesh view fell to 21 datasets.

**Cause:** with `persistence_code=10`, every controller re-initialisation inside the JVM (which happens when the
regional connection drops and Derby re-boots) persisted the manager instances again.

**Guard:** the poisoned database was set aside and the agent started fresh (79 threads, no plugin restore).
`deploy_managers.py` no longer sets `persistence_code` unless `PANATLAS_PERSIST=1`. The 15-minute ensure timer
re-adds missing managers instead, and it is idempotent by URN. Verified the same day: 33 datasets on the mesh,
threads stable at 116, 0 errors.

### Listed but not answering

**When:** 2026-09-20. **Symptom:** after a watchdog restart, the regional controller kept **listing** all 65 managers
while messaging to them was dead (`getgraphinventory` failed 6 of 6 probes). The Mesh view fell from 33 to 0
datasets, and the ensure timer reported "deployed 0" every 15 minutes, because its idempotency check asked only
whether the URN was listed.

**Guard:** `deploy_managers.py` probes every listed manager, removes the ones that do not answer, and re-adds them.
Verified: 65 re-added, mesh back to 65, zero connection failures.

### The silent refresh outage

**When:** 2026-09-20 17:01 to 2026-09-23. **Symptom:** none visible. The timer stayed `active`, but every hourly
refresh failed, and no registry manifest moved for three days.

**Cause:** six directories named like manifest files, written by a fold script on 2026-09-18, made the manifest
builder raise `IsADirectoryError`.

**Guard:** the builder now moves such directories aside and continues. Refresh is back to 95 manifests in 15 s.
Watch the refresh log's output, not just whether the timer is active.

### Adds that silently failed

**When:** 2026-09-24 to 09-26. **Symptom:** the site showed 0 datasets for two days while the ensure timer printed
"deployed 94" and exited 0 every 15 minutes.

**Cause:** under a "known connection failure" on the web host agent, every `add_plugin_agent` returned `{}`. An empty
reply had also accompanied successful adds on 09-23, so it could not be read either way.

**Guard:** `deploy_managers.py` ends by re-listing and probing every manager it is responsible for, and exits 3 if any
does not answer. On exit 3, `ensure_managers.sh` restarts the web host agent, retries once and restarts the mesh
daemon, with a one-hour cooldown.

## Runbook: the Mesh view shows 0 datasets

1. **Read `mesh.json`.** If it holds only the global node (`counts.agents = 0`), the daemon is running but sees no
   agents: check the agents first. If agents are present but `datasets = 0`, the managers are not answering.
2. **Cluster agent.** `systemctl --user status panatlas-agent.service`; look in `cresco/watchdog.log` and the agent
   log for `DBEngine` or `Derby` errors; count `rawStoreD` threads (see above).
3. **Restart it if needed:** `systemctl --user restart panatlas-agent.service`.
4. **Managers:** on the web host, run `deploy_managers.py` from the mesh virtual environment (or wait for the
   timer). It must end with `[verify] N of N managers answer`.
5. **View:** `systemctl restart panatlas-mesh.service`. The count rebuilds over the next 15 s pull cycles.

## Runbook: add a dataset to the mesh

1. Register the dataset in the cluster's `datasets.json` with its `host`, `locations` and `embedding_models`. See
   [Dataset registry](../metadata/dataset-registry.md).
2. Build its manifest (`dataset_manifest.py build`), or wait for the hourly refresh.
3. Regenerate the payloads (`build_dataset_reports.py --host <cluster host>`).
4. Copy the new `<slug>.{report,manifest,instance}.json` to the web host's reports directory, where
   `deploy_managers.py` reads instance files.
5. Run `deploy_managers.py <slug>`, or wait 15 minutes. Confirm the dataset in the Mesh view.
