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

**Example Shift Types**

- "GEN"
- "ICU"
- "PEDI"
- "ER"
- "EVE-GEN"
- "EVE-ICU"

**Example Nurse starting schedule**

| Name  | Days Available | Certifications             | Pre-defined shifts   |
| ----- | -------------- | -------------------------- | -------------------- |
| Alice | 1,2,6,7,8      | GEN, EVE-GEN, ICU, EVE-ICU | (3, GEN)             |
| Bobby | 4,8,9          | GEN, EVE-GEN, PEDI         | (2, PEDI), (3, PEDI) |
| Cindy | 0,1,3,4,9      | GEN, EVE-GEN, ER           |                      |
| Danny | 4,5,7,8,9      | GEN, EVE-GEN, PEDI         | (3, GEN)             |
| Ellie | 0,1,4,5,8,9    | OR, ICU, EVE-ICU PEDI      |                      |

| Shifts      | Days Needed Coverage |
| ----------- | -------------------- |
| GEN         | 1,2,3,4,5,6,7,8,9    |
| ICU         | 1,2,3,4,5,6,7,8,9    |
| PEDI        | 1,2,5,6,9            |
| ER          | 1,2,5,6,9            |
| EVENING-GEN | 1,2,3,4,5,6,9        |
| EVENING-ICU | 1,2,3,4,5,6,9        |
