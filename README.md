# ortools_scheduling

**Goal**

Fill an employees shift schedule

Optimize for

- shifts filled
- fair evening shift allocation
- consecutive shifts of same type

**Terms**

- Nurses:
  - nurses may be full or part time
- Shifts:
  - shifts require certifications
  - shifts may be day or evening
  - day shift cannot come after evening shifts
  - evening shifts must be fairly allocated based on a formula
    - full time employees 100% of distribution
    - part time employees 70% of what full time would get
  - the saturday shift must match the sunday shift

**Example Shift Types**

- "GEN"
- "ICU"
- "EVE-GEN"

**Example Nurse starting schedule**

| Name  | Days Available | Certifications    | Pre-defined shifts   |
| ----- | -------------- | ----------------- | -------------------- |
| Alice | 1,2,4          | GEN, EVE-GEN      | (3, GEN)             |
| Bobby | 3,4            | GEN, EVE-GEN      | (2, PEDI), (3, PEDI) |
| Cindy | 1,4,5          | GEN, EVE-GEN, ICU |                      |

| Shifts      | Days Needed Coverage |
| ----------- | -------------------- |
| GEN         | 1,2,3,4              |
| ICU         | 1,2,3,4              |
| EVENING-GEN | 1,2,3,4              |
