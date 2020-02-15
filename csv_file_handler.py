import csv

# Read CSV file and extract records in to a list of lists
def csv_extract(file_name):
    with open(file_name, mode='r', newline='') as file_object:
        csv_object = csv.reader(file_object)
        lines = []

        for line in csv_object:
            lines.append(line)

    return lines


# Write CSV file from list of lists/tuples and save with file name as provided in argument
def csv_export_list(lines, file_name):
    with open(file_name, mode='w', newline='') as file_object:
        csv_object = csv.writer(file_object)

        csv_object.writerows(lines)


# Write CSV file from list of dictionaries and save with file name as provided in argument
def csv_export_dict(lines, file_name, field_names):
    with open(file_name, mode='w', newline='') as file_object:
        csv_object = csv.DictWriter(file_object, fieldnames=field_names.keys())

        csv_object.writeheader()
        csv_object.writerows(lines)


if __name__ == "__main__":
    try:
        csv_file_name = input("Enter valid csv file name here (exclude '.csv'): ") + ".csv"
        records_list = csv_extract(csv_file_name)
    except FileNotFoundError:
        print('Sorry no file or directory found as referenced. Please check your entry and try again.')
    else:
        print(str(len(records_list)) + " records (including header row)")
        print(str(len(records_list[0])) + " fields")
        print(records_list[0])
        print(records_list[1])
        print([type(field) for field in records_list[1]])
