# The GPU cooler, used on its own

[`common/adt/gpucooler.py`](../common/adt/gpucooler.py) keeps a long run of local-model calls from running an NVIDIA card hot, and keeps the pauses from corrupting the timings you measure. It is one file of about 200 lines. It imports only the standard library (`shutil`, `subprocess`, `threading`, `time`) and reads the temperature by calling `nvidia-smi`. You can copy it into another project and use it without anything else from this repository.

## What it does

Before each model call it reads the GPU temperature and acts on three levels:

| Temperature | What happens |
| --- | --- |
| Up to 66 C (`soft_c`) | The call goes ahead at once |
| Above 66 C, up to 72 C (`max_c`) | The call goes ahead after a short rest (2 seconds by default), so a run slows down before it reaches the limit |
| Above 72 C | The call waits, polling every 3 seconds, until the card is at 60 C (`resume_c`) or lower. After 30 minutes of waiting it raises an error rather than stall forever |

`settle()` waits for the card to reach 60 C before a run starts and between one model and the next, so each begins cool. It never raises: if the card has not cooled after 15 minutes it says so and goes on, since the per-call limit still applies.

The point of the measurement side is that a pause is not part of a model's speed. The cooler counts every second it spends checking, resting or waiting, and tells you, so you can take it out of a latency figure and stamp it on a result. It also records the peak temperature, the number of pauses and eased calls, the seconds spent paused, and a timeline of temperature samples with the pauses marked.

## Using it

Copy `gpucooler.py` next to your script and install a cooler once:

```python
import time
import gpucooler

cooler = gpucooler.install(gpucooler.GpuCooler(max_c=72))   # resumes at 60, eases off from 66
gpucooler.settle()                                          # begin with a cool card

for prompt in prompts:
    t0, b0 = time.perf_counter(), gpucooler.busy_ms()
    gpucooler.before_call()                                 # waits if hot, rests a little if warm
    reply = ask_model(prompt)                               # your own call
    ms = (time.perf_counter() - t0) * 1000 - (gpucooler.busy_ms() - b0)   # the model's time, with the cooler's time taken out
    record = {"ms": ms, **gpucooler.snapshot()}             # snapshot() adds gpu_temp_c and thermal_wait_ms (waits since the last record)

print(cooler.stats())                                       # max_c, resume_c, soft_c, peak_c, pauses, paused_s, eased, eased_s, settled_s
gpucooler.uninstall()
```

Without `install()`, `before_call()` and `settle()` do nothing and `snapshot()` returns an empty dict, so the same code runs on a machine with no NVIDIA card. If `nvidia-smi` is not found the cooler says so once and stops limiting.

To run a sampler in the background that tracks the true peak between calls, `install(cooler)` already starts one. Pass `sampler=False` to turn it off. `cooler.timeline()` returns the samples and pauses as plain data, which this project draws as a chart.

Every threshold is a constructor argument (`max_c`, `resume_c`, `soft_c`, `poll_s`, `give_up_s`, `ease_s`). `read`, `sleep`, `clock` and `say` can be replaced, which is how the tests drive it without a GPU.

## Limits

- **It checks between calls.** One long generation can still push the card past the limit before the next check. The background sampler records the real peak, so the report is honest about it.
- **It reads temperature only.** It does not set fan curves, clocks or power limits. On some cards, notably laptop GPUs, the power limit cannot be changed from software at all.
- **Pausing keeps the model loaded.** The card goes idle but video memory stays in use.
- **NVIDIA only**, through `nvidia-smi`, and the hottest GPU is the one it watches.
- **The defaults suit one machine.** They were chosen for a 150 W RTX 2080 Super. Runs there with a 68 C resume point peaked at 74 to 77 C, and runs since moving to the 60 C resume point and the ease-off peaked at 65 to 67 C. Choose your own limit from your card's throttle point and how loud you will tolerate the fans.

## Prior art

The basic idea, pause at a high temperature and resume at a lower one so the card does not flap, is common. It appears in the [FrankenStein GPU Temperature Guard](https://frankenstein-transformer.readthedocs.io/en/latest/api/utils/gpu_temp_guard.html) for training jobs, in two ComfyUI nodes ([GPU temperature protection](https://comfyonline.app/comfyui-nodes/GPU-temperature-protection) and [Smart Cooldown & Pause](https://comfy.icu/node/SmartCooldownNode)), in NVIDIA's own [Nsight Python thermovision](https://docs.nvidia.com/nsight-python/thermovision.html), and in scripts that pause a local model process with a signal, such as [this write-up](https://www.autodidacts.io/pause-resume-resource-intensive-llm-inference-process-on-linux-with-sigstop-sigcont.md). This was checked with two searches, not a full survey.

What this one adds is the accounting: it stamps each result with the temperature and the wait, takes the waits out of the latency figures, keeps a timeline for the report, eases off before the limit and settles before a run. If you only want to protect a card, one of the others may suit you better.

## Where it is tested

[`common/tests/test_gpucooler.py`](../common/tests/test_gpucooler.py) covers the limits, the resume point, the ease-off, settling, the give-up timeout and a lost sensor, and [`common/tests/test_latency.py`](../common/tests/test_latency.py) covers the timeline and the time accounting. Both run without a GPU.
