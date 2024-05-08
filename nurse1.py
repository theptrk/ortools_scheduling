"""Example of a simple nurse scheduling problem."""

from ortools.sat.python import cp_model


def main() -> None:
    # Data.
    num_nurses = 4
    num_shifts = 3
    num_days = 3
    all_nurses = range(num_nurses)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    # Define all shift types in a given day
    all_shift_types = ["GEN", "ICU", "EVE-GEN"]

    # Code to identify evening shifts (unchanged)
    is_evening_for_shift_types: list[bool] = [
        st.startswith("EVE-") for st in all_shift_types
    ]

    # Shift coverage requirement for each day and shift.
    # 1 means the shift needs to be covered by exactly one nurse, 0 means no coverage needed.
    coverage_required = {
        # Day 0: GEN and EVE-GEN need coverage
        (0, 0): 1,
        (0, 1): 0,
        (0, 2): 1,
        # Day 1: Only ICU needs coverage
        (1, 0): 0,
        (1, 1): 1,
        (1, 2): 0,
        # Day 2: All shifts need coverage
        (2, 0): 1,
        (2, 1): 1,
        (2, 2): 1,
    }

    # Define nurse-specific shift restrictions.
    # Each nurse is mapped to a list of shift types they are allowed to work.
    nurse_certifications = {
        0: ["GEN", "ICU"],  # Nurse 0 can work general and ICU shifts
        1: ["EVE-GEN"],  # Nurse 1 can only work evening general shifts
        2: ["GEN", "EVE-GEN"],  # Nurse 2 can work general and evening general shifts
        3: ["ICU"],  # Nurse 3 can only work ICU shifts
    }

    assert num_nurses == len(nurse_certifications.keys())

    # Predefined shifts where the key is a tuple (nurse, day, shift) and the value is True
    # if that nurse is required to work that shift on that day.
    predefined_shifts = [
        # Nurse 0, day 1 is scheduled to work shift 1 ("ICU")
        (0, 1, 1),
        # Nurse 1, day 2 is scheduled to work shift 2 ("EVE-GEN")
        (1, 2, 2),
    ]

    evening_shift_allocation_data = [
        (1, 2),  # Min 1, max 2 evening shifts for nurse 0
        (3, 4),  # Min 3, max 4 evening shifts for nurse 1
        (3, 4),  # Min 3, max 4 evening shifts for nurse 2
        (2, 3),  # Min 2, max 3 evening shifts for nurse 3
    ]

    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(n, d, s)]: nurse 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.new_bool_var(f"shift_n{n}_d{d}_s{s}")

    # Enforce coverage requirements.
    # Not every shift needs to be filled every day.
    # If a shift needs to be covered, only one nurse should fill it
    # else: no nurse should fill it
    for d in all_days:
        for s in all_shifts:
            if coverage_required[(d, s)] == 1:
                # (n (varying), d, s) should be a single 1 in list
                # https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html#CpModel.add_exactly_one
                # - Adds ExactlyOne(literals): sum(literals) == 1.
                model.add_exactly_one(shifts[(n, d, s)] for n in all_nurses)
            else:
                # (n (varying), d, s) should sum to 0
                model.add(sum(shifts[(n, d, s)] for n in all_nurses) == 0)

    # Each nurse works at most one shift per day.
    for n in all_nurses:
        for d in all_days:
            model.add_at_most_one(shifts[(n, d, s)] for s in all_shifts)

    # Enforce nurse-specific restrictions by preventing nurses from being assigned to shifts
    # they are not allowed to work. If a shift type is not in a nurse's allowable list,
    # the corresponding shift variable is constrained to be 0 (nurse does not work that shift).
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                shift_type = all_shift_types[s]
                if shift_type not in nurse_certifications[n]:
                    # If the shift type is not in the nurse's allowed list, forbid this assignment
                    model.add(shifts[(n, d, s)] == 0)

    # Set predefined shifts
    for n, d, s in predefined_shifts:
        shift_type = all_shift_types[s]
        assert shift_type in nurse_certifications[n]
        # might need to change in future for "PROJ"
        assert coverage_required[(d, s)]
        model.add(shifts[(n, d, s)] == 1)

    # Constraint for preventing back-to-back evening then day shifts for any nurse
    for n in all_nurses:
        # Avoid the last day as it doesn't have a 'next day'
        for d in range(num_days - 1):
            for s in all_shifts:
                if all_shift_types[s].startswith("EVE-"):
                    tomorrows_day_shifts = [
                        shifts[(n, d + 1, s_next)]
                        for s_next in all_shifts
                        if not all_shift_types[s_next].startswith("EVE-")
                    ]
                    if tomorrows_day_shifts:
                        # BONUS
                        # Check if today is Sunday (d % 7 == 0) and tomorrow is Monday ((d + 1) % 7 == 1)
                        # if (d % 7 == 0) and ((d + 1) % 7 == 1):
                        #     # Allow evening to day transition from Sunday to Monday
                        #     continue

                        # tomorrows_day_shifts_1_count = sum(tomorrows_day_shifts)
                        model.add(sum(tomorrows_day_shifts) == 0).only_enforce_if(
                            shifts[(n, d, s)]
                        )

    # Add constraints to enforce minimum and maximum number of evening shifts
    for n in all_nurses:
        # assigned only should not exceed max
        assigned_evening_shifts = []
        # predefined + assigned should pass minimum
        total_evening_shifts = []

        for d in all_days:
            for s in all_shifts:
                if is_evening_for_shift_types[s]:
                    shift_var = shifts[(n, d, s)]
                    total_evening_shifts.append(shift_var)

        # Min and max shifts including predefined
        min_evening_shifts, max_evening_shifts = evening_shift_allocation_data[n]
        model.add(sum(total_evening_shifts) >= min_evening_shifts)

        if assigned_evening_shifts:
            model.add(sum(assigned_evening_shifts) <= max_evening_shifts)

    # Try to distribute the shifts evenly, so that each nurse works
    # min_shifts_per_nurse shifts. If this is not possible, because the total
    # number of shifts is not divisible by the number of nurses, some nurses will
    # be assigned one more shift.
    # min_shifts_per_nurse = (num_shifts * num_days) // num_nurses
    # if num_shifts * num_days % num_nurses == 0:
    #     max_shifts_per_nurse = min_shifts_per_nurse
    # else:
    #     max_shifts_per_nurse = min_shifts_per_nurse + 1
    # for n in all_nurses:
    #     shifts_worked = []
    #     for d in all_days:
    #         for s in all_shifts:
    #             shifts_worked.append(shifts[(n, d, s)])
    #     model.add(min_shifts_per_nurse <= sum(shifts_worked))
    #     model.add(sum(shifts_worked) <= max_shifts_per_nurse)
    #     model.add(sum(shifts_worked) <= 1)

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    # Enumerate all solutions.
    solver.parameters.enumerate_all_solutions = True

    class NursesPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
        """Print intermediate solutions."""

        def __init__(self, shifts, num_nurses, num_days, num_shifts, limit):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self._shifts = shifts
            self._num_nurses = num_nurses
            self._num_days = num_days
            self._num_shifts = num_shifts
            self._solution_count = 0
            self._solution_limit = limit

        def on_solution_callback(self):
            self._solution_count += 1
            print(f"Solution {self._solution_count}")
            for d in range(self._num_days):
                print(f"Day {d}")
                for n in range(self._num_nurses):
                    is_working = False
                    for s in range(self._num_shifts):
                        if self.value(self._shifts[(n, d, s)]):
                            is_working = True
                            print(f"  Nurse {n} works shift {s} ({all_shift_types[s]})")
                    if not is_working:
                        print(f"  Nurse {n} does not work")
            if self._solution_count >= self._solution_limit:
                print(f"Stop search after {self._solution_limit} solutions")
                self.stop_search()

        def solutionCount(self):
            return self._solution_count

    # Display the first five solutions.
    solution_limit = 5
    solution_printer = NursesPartialSolutionPrinter(
        shifts, num_nurses, num_days, num_shifts, solution_limit
    )

    solver.solve(model, solution_printer)

    # Statistics.
    print("\nStatistics")
    print(f"  - conflicts      : {solver.num_conflicts}")
    print(f"  - branches       : {solver.num_branches}")
    print(f"  - wall time      : {solver.wall_time} s")
    print(f"  - solutions found: {solution_printer.solutionCount()}")


if __name__ == "__main__":
    main()
