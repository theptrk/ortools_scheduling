"""Example of a simple nurse scheduling problem."""

from ortools.sat.python import cp_model


def main() -> None:
    # Data.

    # Name, Certifications, Days Available
    ALL_NURSES = [
        ("Alice", set(["S1", "EVE-S1", "S2"]), set([0, 1, 4])),
        ("Bobby", set(["S1", "EVE-S1", "S2"]), set([1, 2, 3])),
        ("Cindy", set(["S1", "EVE-S1"]), set([0, 1, 2, 3, 4])),
    ]

    ALL_SHIFT_TYPES = ["S1", "EVE-S1", "S2"]

    ALL_DAYS = [0, 1, 2, 3, 4]

    shift_coverage_days = {
        "S1": set([0, 1, 3, 4]),
        "EVE-S1": set([1, 2, 3]),
        "S2": set([0, 2, 4]),
    }

    num_days = len(ALL_DAYS)

    # Creates the model.
    model = cp_model.CpModel()

    def valid_n_d_s(nurse_certs, nurse_av, d, shift_name):
        is_shift_needs_coverage = d in shift_coverage_days[shift_name]
        if not is_shift_needs_coverage:
            return False

        is_emp_cert_for_shift = shift_name in nurse_certs
        if not is_emp_cert_for_shift:
            return False

        is_nurse_av = d in nurse_av
        if not is_nurse_av:
            return False

        return True

    # Creates shift variables.
    shifts = {}
    for nurse_name, nurse_certs, nurse_av in ALL_NURSES:
        for d in ALL_DAYS:
            for shift_name in ALL_SHIFT_TYPES:
                if not valid_n_d_s(nurse_certs, nurse_av, d, shift_name):
                    continue

                shifts[(nurse_name, d, shift_name)] = model.new_bool_var(
                    f"shift_n{nurse_name}_d{d}_s{shift_name}"
                )

    # Each shift is assigned to exactly one nurse in the schedule period.
    for d in ALL_DAYS:
        for shift_name in ALL_SHIFT_TYPES:
            exactly_one_nurse = [
                shifts[(nurse_name, d, shift_name)]
                for nurse_name, nurse_certs, nurse_av in ALL_NURSES
                if valid_n_d_s(nurse_certs, nurse_av, d, shift_name)
            ]
            # examples: note shifts are the same in each list
            # [shift_nAlice_d0_sS1(0..1), shift_nBobby_d0_sS1(0..1), shift_nCindy_d0_sS1(0..1)]
            # [shift_nAlice_d0_sEVE-S1(0..1), shift_nBobby_d0_sEVE-S1(0..1), shift_nCindy_d0_sEVE-S1(0..1)]
            # [shift_nAlice_d0_sS2(0..1), shift_nBobby_d0_sS2(0..1)]
            if len(exactly_one_nurse) > 0:
                model.add_exactly_one(exactly_one_nurse)

    # Each nurse works at most one shift per day.
    for nurse_name, nurse_certs, nurse_av in ALL_NURSES:
        for d in ALL_DAYS:
            # examples: note days are the same in each list
            # [shift_nAlice_d0_sS1(0..1), shift_nAlice_d0_sEVE-S1(0..1), shift_nAlice_d0_sS2(0..1)]
            # [shift_nAlice_d1_sS1(0..1), shift_nAlice_d1_sEVE-S1(0..1), shift_nAlice_d1_sS2(0..1)]
            # [shift_nAlice_d2_sS1(0..1), shift_nAlice_d2_sEVE-S1(0..1), shift_nAlice_d2_sS2(0..1)]
            one_shift_per_day = [
                shifts[(nurse_name, d, shift_name)]
                for shift_name in ALL_SHIFT_TYPES
                if valid_n_d_s(nurse_certs, nurse_av, d, shift_name)
            ]
            if len(one_shift_per_day) > 0:
                model.add_at_most_one(one_shift_per_day)

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    # Enumerate all solutions.
    solver.parameters.enumerate_all_solutions = True

    class NursesPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
        """Print intermediate solutions."""

        def __init__(self, shifts, all_nurses, num_days, all_shift_types, limit):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self._shifts = shifts
            self._all_nurses = all_nurses
            self._num_days = num_days
            self._all_shift_types = all_shift_types
            self._solution_count = 0
            self._solution_limit = limit

        def on_solution_callback(self):
            self._solution_count += 1
            print(f"Solution {self._solution_count}")
            for d in range(self._num_days):
                print(f"Day {d}")
                for nurse_name, nurse_certs, nurse_av in self._all_nurses:
                    is_working = False
                    for shift_name in self._all_shift_types:
                        if valid_n_d_s(nurse_certs, nurse_av, d, shift_name):
                            if self.value(self._shifts[(nurse_name, d, shift_name)]):
                                is_working = True
                                print(f"  Nurse {nurse_name} works shift {shift_name}")
                    if not is_working:
                        if valid_n_d_s(nurse_certs, nurse_av, d, shift_name):
                            print(f"  Nurse {nurse_name} does not work")
                        else:
                            print(f"  Nurse {nurse_name} not available")
            if self._solution_count >= self._solution_limit:
                print(f"Stop search after {self._solution_limit} solutions")
                self.stop_search()

        def solutionCount(self):
            return self._solution_count

    # Display the first five solutions.
    solution_limit = 5
    solution_printer = NursesPartialSolutionPrinter(
        shifts, ALL_NURSES, num_days, ALL_SHIFT_TYPES, solution_limit
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
