import random
import csv_file_handler


# Assumptions
current_fund_value = 1000000.00
number_of_months = 12
number_of_trials = 6000
fixed_recovery_period = 6
fixed_pd_buffer = 0.0
fixed_risk_rate_buffer = 0.0
frequency_interval = 100000
frequency_bound = 6000000
fund_values = [i * 100000 + current_fund_value for i in range(10)]

min_frequency = []
final_frequency = []
simulation_results = []


# Create user defined Borrower class
class Borrower:
    exposure_at_default = 2.0

    def __init__(self, borrower_name, principal_outstanding, facility_limit, loss_given_default,
                 probability_of_default, risk_rate, pd_buffer=fixed_pd_buffer, risk_rate_buffer=fixed_risk_rate_buffer, recovery_period=fixed_recovery_period):

        self.borrower_name = borrower_name
        self.principal_outstanding = float(principal_outstanding)
        self.facility_limit = float(facility_limit)
        self.loss_given_default = float(loss_given_default)
        self.pd_buffer = pd_buffer
        self.probability_of_default = float(probability_of_default)
        self.risk_rate = float(risk_rate)
        self.risk_rate_buffer = risk_rate_buffer
        self.recovery_period = recovery_period
        self.annual_risk_rate_income = self.principal_outstanding * self.risk_rate
        self.gross_write_off = max(float(self.principal_outstanding), float(self.facility_limit))
        self.has_defaulted = False
        self.default_month = None

    def __repr__(self):

        return self.borrower_name


# Create list of Borrower objects (skip first record): list of B items
def list_borrowers(records):
    return [Borrower(record[0], record[1], record[2], record[3], record[4], record[5]) for record in records[1:]]


# generate random default outcome for each borrower, set defaulted borrowers to True, all else to False
def trial_borrower_default(borrowers):
    for borrower in borrowers:
        trial = random.randint(1, 10000) / 10000
        if trial <= borrower.probability_of_default * (1 + borrower.pd_buffer):
            borrower.has_defaulted = True
        else:
            borrower.has_defaulted = False


# generate random default month for defaulted borrowers, all else to None
def trial_borrower_default_month(borrowers, horizon):
    for borrower in borrowers:
        if borrower.has_defaulted:
            borrower.default_month = random.randint(1, horizon)
        else:
            borrower.default_month = None


# run monte carlo trial
def monte_carlo_trial(borrowers, horizon):
    trial_borrower_default(borrowers)
    trial_borrower_default_month(borrowers, horizon)


# calculate monthly risk rate income across all non-defaulted borrowers
def total_income_in_month(borrowers, month):
    total_income = 0

    for borrower in borrowers:
        if not borrower.has_defaulted or month <= borrower.default_month:
            total_income += borrower.annual_risk_rate_income * (1 + borrower.risk_rate_buffer) / 12

    return total_income


# calculate monthly write off across all defaulted borrowers
def total_write_off_in_month(borrowers, month):
    total_write_off = 0

    for borrower in borrowers:
        if borrower.has_defaulted and month == borrower.default_month:
            total_write_off += borrower.gross_write_off

    return total_write_off


# calculate monthly recovery across all defaulted borrowers within their recovery period
def total_recovery_in_month(borrowers, month):
    total_recovery = 0

    for borrower in borrowers:
        if borrower.has_defaulted and borrower.default_month < month <= borrower.default_month + borrower.recovery_period:
            total_recovery += borrower.gross_write_off * (1 - borrower.loss_given_default) / borrower.recovery_period

    return total_recovery


# calculate total monthly result over the H horizon: list of H items
def total_result_by_month(total_function, borrowers, horizon):
    return [total_function(borrowers, i + 1) for i in range(horizon)]


# calculate total monthly net of risk rate income, write off and recoveries across all borrowers: list of H items
def trial_result_by_month(borrowers, horizon):
    income_by_month = total_result_by_month(total_income_in_month, borrowers, horizon)
    write_off_by_month = total_result_by_month(total_write_off_in_month, borrowers, horizon)
    recovery_by_month = total_result_by_month(total_recovery_in_month, borrowers, horizon)

    return [income_by_month[i] + recovery_by_month[i] - write_off_by_month[i] for i in range(horizon)]


# calculate cumulative total monthly net result across all borrowers: list of H items
def trial_cumulative_result_by_month(trial_results):
    cumulative_result_by_month = []
    cumulative_result = 0

    for trial_result in trial_results:
        cumulative_result += trial_result
        cumulative_result_by_month.append(cumulative_result)

    return cumulative_result_by_month


# Add one to trial counter based on min fund value and final month fund value signs
def trial_results_counter(fund_value_results, index, min_frequency, final_frequency):
    if min(fund_value_results) < 0:
        min_frequency[index]["<0"] += 1
    else:
        min_frequency[index][str(int(min(fund_value_results) // frequency_interval))] += 1

    if fund_value_results[-1] < 0:
        final_frequency[index]["<0"] += 1
    else:
        final_frequency[index][str(int(fund_value_results[-1] // frequency_interval))] += 1


def output_summary(min_frequency, final_frequency, fund_values):
    with open("simulation_summary.txt", mode="w", newline="") as file_object:

        file_object.write("{trials:,} trials completed in simulation".format(trials=number_of_trials))

        for fund_value in zip(min_frequency, final_frequency, fund_values):
            file_object.write("\n\n" + "Starting fund value ${fund:,}".format(fund=fund_value[2]))
            file_object.write(
                "\n" + "Minimum value returned: positive {positive:,} times and negative {negative:,} times -- 1 in {odds} odds".format(
                    positive=number_of_trials-fund_value[0]["<0"], negative=fund_value[0]["<0"],
                    odds=int(1/(fund_value[0]["<0"]/number_of_trials))))
            file_object.write(
                "\n" + "Final value returned: positive {positive:,} times and negative {negative:,} times -- 1 in {odds} odds".format(
                    positive=number_of_trials-fund_value[1]["<0"], negative=fund_value[1]["<0"],
                    odds=int(1/(fund_value[1]["<0"]/number_of_trials))))


# run M trials and calculate min fund value and final month fund value for range of fund values: list of V by M by 2
def monte_carlo_simulation(total_trials, borrowers, horizon, fund_values):
    for i in range(len(fund_values)):
        min_frequency.append({
        **{"<0": 0}, **{str(i): 0 for i in range(frequency_bound//frequency_interval)}
    })
        final_frequency.append({
        **{"<0": 0}, **{str(i): 0 for i in range(frequency_bound//frequency_interval)}
    })
        simulation_results.append([])

    for trial in range(total_trials):
        monte_carlo_trial(borrowers, horizon)
        results = trial_result_by_month(borrowers, horizon)
        cumulative_results = trial_cumulative_result_by_month(results)
        for index, fund_value in enumerate(fund_values):
            # calculate monthly fund value over horizon: list of H items
            fund_value_results = [cumulative_result + fund_value for cumulative_result in cumulative_results]
            # # Add minimum and final fund values to list of trial results for fund value: list of V by M by 2 items
            # simulation_results[index].append((min(fund_value_results), fund_value_results[-1]))
            trial_results_counter(fund_value_results, index, min_frequency, final_frequency)

    return simulation_results, min_frequency, final_frequency


if __name__ == "__main__":
    try:
        file_name = input("Enter valid csv file name (exclude '.csv'): ") + ".csv"
        # Extract data from CSV file and create list of Borrower objects
        borrowers_list = list_borrowers(csv_file_handler.csv_extract('trial_raw_data/' + file_name))
    except FileNotFoundError:
        print('File not found as referenced. Please check your entry and try again.')
    else:
        # Monte Carlo simulation with (i) odds of fund default and (ii) final and min fund values for all trials
        simulation_result = monte_carlo_simulation(number_of_trials, borrowers_list, number_of_months, fund_values)
        # Write the odds of minimum and final fund values for all starting fund values to txt file
        output_summary(simulation_result[1], simulation_result[2], fund_values)
        # # Export list of final and min fund values for all trials to CSV file
        # csv_file_handler.csv_export_list(simulation_result[0][0], "simulation trials results.csv")
        # Export dictionary of final and min fund value frequencies for all trials for each starting fund value to CSV
        csv_file_handler.csv_export_dict(simulation_result[1], "simulation_min_frequency.csv", simulation_result[1][0])
        csv_file_handler.csv_export_dict(simulation_result[2], "simulation_final_frequency.csv", simulation_result[2][0])
