import re


def is_valid_name(name):
    # Перевірка, чи є ім'я допустимим (починається з літери і складається з літер, цифр або підкреслення)
    return re.match(r"[a-zA-Z][a-zA-Z0-9_]*", name)


class Table:
    def __init__(self, name):
        # Ініціалізація таблиці з ім'ям
        if not is_valid_name(name):
            raise ValueError("Invalid table name")
        self.name = name
        self.columns = {}
        self.indexed_columns = []
        self.rows = []

    def add_column(self, column_name, column_type="INTEGER", indexed=False):
        # Додавання стовпця до таблиці
        if not is_valid_name(column_name):
            raise ValueError("Invalid column name")
        if column_type.upper() not in ["INTEGER", "FLOAT", "REAL"]:
            raise ValueError("Invalid column type, must be INTEGER, FLOAT, or REAL")
        self.columns[column_name] = column_type.upper()
        if indexed:
            self.indexed_columns.append(column_name)

    def insert_row(self, values):
        # Вставка рядка в таблицю
        if len(values) != len(self.columns):
            raise ValueError("Column count does not match value count")
        typed_values = []
        for (value, col_type) in zip(values, self.columns.values()):
            # Перетворення значень на відповідний тип
            if col_type == "INTEGER":
                typed_values.append(int(value))
            elif col_type == "FLOAT":
                typed_values.append(float(value))
            elif col_type == "REAL":
                typed_values.append(float(value))
        self.rows.append(typed_values)

    def select(self, columns, where_clause=None):
        # Виконання запиту SELECT для вибірки даних з таблиці
        if columns == ['*']:
            columns = list(self.columns.keys())

        selected_rows = []
        column_indices = []

        for col in columns:
            col_upper = col.upper()
            if col_upper.startswith("AVG(") and col.endswith(")"):
                # Обробка функції AVG
                col_name = col[4:-1].strip()
                if col_name not in self.columns:
                    raise ValueError(f"Column '{col_name}' does not exist")
                column_data = [row[list(self.columns.keys()).index(col_name)] for row in self.rows]
                avg_value = sum(column_data) / len(column_data) if column_data else 0
                selected_rows.append([avg_value])
                columns = ["AVG({})".format(col_name)]
            elif col_upper.startswith("MAX(") and col.endswith(")"):
                # Обробка функції MAX
                col_name = col[4:-1].strip()
                if col_name not in self.columns:
                    raise ValueError(f"Column '{col_name}' does not exist")
                column_data = [row[list(self.columns.keys()).index(col_name)] for row in self.rows]
                max_value = max(column_data) if column_data else None
                selected_rows.append([max_value])
                columns = ["MAX({})".format(col_name)]
            elif col_upper.startswith("COUNT(") and col.endswith(")"):
                # Обробка функції COUNT
                col_name = col[6:-1].strip()
                if col_name not in self.columns:
                    raise ValueError(f"Column '{col_name}' does not exist")
                count_value = len(self.rows)
                selected_rows.append([count_value])
                columns = ["COUNT({})".format(col_name)]
            else:
                column_indices.append(list(self.columns.keys()).index(col))

        if not column_indices:
            return columns, selected_rows

        for row in self.rows:
            if where_clause:
                where_col, where_val = where_clause
                where_col_idx = list(self.columns.keys()).index(where_col)
                if row[where_col_idx] != int(where_val):
                    continue
            selected_row = [row[idx] for idx in column_indices]
            selected_rows.append(selected_row)

        return columns, selected_rows

    def __repr__(self):
        # Повертає строкове представлення таблиці
        columns_repr = []
        for column in self.columns:
            col_type = self.columns[column]
            if column in self.indexed_columns:
                columns_repr.append(f"{column} ({col_type}) - is indexed")
            else:
                columns_repr.append(f"{column} ({col_type})")
        return f"Table(name={self.name}, columns={', '.join(columns_repr)}, rows={self.rows})"


class Database:
    def __init__(self):
        # Ініціалізація бази даних
        self.tables = {}

    def create_table(self, table_name, columns):
        # Створення таблиці в базі даних
        if table_name in self.tables:
            return f"Error: Table {table_name} already exists"
        if not is_valid_name(table_name):
            return "Error: Invalid table name"
        table = Table(table_name)
        for column_name, column_type, indexed in columns:
            if not is_valid_name(column_name):
                return "Error: Invalid column name"
            table.add_column(column_name, column_type, indexed)
        self.tables[table_name] = table
        return f"Table {table_name} has been created"

    def insert_into_table(self, table_name, values):
        # Вставка рядка в таблицю
        if table_name not in self.tables:
            return f"Error: Table {table_name} does not exist"
        table = self.tables[table_name]
        try:
            table.insert_row(values)
            inserted_row = table.rows[-1]
            column_names = list(table.columns.keys())
            values_str = ", ".join(f"{column}: {value}" for column, value in zip(column_names, inserted_row))

            all_values_str = "\n".join([", ".join(f"{column}: {row[i]}" for i, column in enumerate(column_names))
                                        for row in table.rows])

            return f"1 row has been inserted into {table_name}. Values: {values_str}\nAll values:\n{all_values_str}"
        except ValueError as e:
            return f"Error: {e}"


def parse_command(command):
    # Парсинг SQL команд
    command = re.sub(r"(--[^\n]*|/\*.*?\*/)", "", command, flags=re.DOTALL).strip()
    command = re.sub(r"[\t\r\n]+", " ", command.encode().decode('unicode-escape'))

    create_match = re.match(r"CREATE\s+\"?([^\"]+)\"?\s*\(\s*([^)]*)\s*\)\s*;", command, re.IGNORECASE)
    if create_match:
        table_name = create_match.group(1).strip()
        columns_str = create_match.group(2)
        columns = []

        for col in columns_str.split(","):
            parts = col.strip().split()
            column_name = parts[0]
            column_type = "INTEGER"
            indexed = False
            if len(parts) > 1:
                if parts[1].upper() in ["INTEGER", "FLOAT", "REAL"]:
                    column_type = parts[1].upper()
                if parts[-1].lower() == "indexed":
                    indexed = True
            columns.append((column_name, column_type, indexed))

        return "CREATE", table_name, columns

    insert_match = re.match(r"INSERT\s+(?:INTO\s+)?\"?([^\"]+)\"?\s*\(\s*([^)]*)\s*\)\s*;", command, re.IGNORECASE)
    if insert_match:
        table_name = insert_match.group(1).strip()
        values_str = insert_match.group(2)
        values = [v.strip() for v in values_str.split(",")]
        return "INSERT", table_name, values

    select_match = re.match(r"SELECT\s+(.*?)\s+FROM\s+\"?([^\"]+)\"?(?:\s+WHERE\s+(.+?)\s*;)?", command, re.IGNORECASE)
    if select_match:
        columns_str = select_match.group(1).strip()
        table_name = select_match.group(2).strip()
        columns = [col.strip() for col in columns_str.split(",")]
        where_clause = None
        if select_match.group(3):
            where_str = select_match.group(3).strip()
            where_col, where_val = where_str.split("=")
            where_clause = (where_col.strip(), where_val.strip())
        return "SELECT", table_name, columns, where_clause

    return None


def main():
    # Основна функція для роботи з базою даних
    db = Database()
    multi_line_input = ""
    first_input = True
    while True:
        try:
            if first_input:
                user_input = input("Enter command: ")
                first_input = False
            else:
                user_input = input()
            if user_input.strip().endswith(';'):
                multi_line_input += user_input
                parsed_command = parse_command(multi_line_input)
                if parsed_command:
                    command_type, table_name, *params = parsed_command
                    if command_type == "CREATE":
                        columns = params[0]
                        result = db.create_table(table_name, columns)
                        if "Error" not in result:
                            table = db.tables.get(table_name)
                            if table:
                                print(f"Table {table_name} has been created with columns:")
                                for column, column_type in table.columns.items():
                                    if column in table.indexed_columns:
                                        print(f"- {column} ({column_type}) - is indexed")
                                    else:
                                        print(f"- {column} ({column_type})")
                        else:
                            print(result)
                    elif command_type == "INSERT":
                        values = params[0]
                        result = db.insert_into_table(table_name, values)
                        print(result)
                    elif command_type == "SELECT":
                        columns, where_clause = params
                        if table_name not in db.tables:
                            print(f"Error: Table {table_name} does not exist")
                        else:
                            table = db.tables[table_name]
                            columns, selected_rows = table.select(columns, where_clause)
                            column_widths = [len(col) for col in columns]
                            for row in selected_rows:
                                for i, value in enumerate(row):
                                    column_widths[i] = max(column_widths[i], len(str(value)))

                            def print_row(row):
                                row_str = " | ".join(
                                    f"{str(value).ljust(width)}" for value, width in zip(row, column_widths))
                                print(f"| {row_str} |")

                            print_row(columns)
                            print(f"+{'-+-'.join('-' * width for width in column_widths)}+")
                            for row in selected_rows:
                                print_row(row)
                else:
                    print("Error: Invalid command. Please make sure your command follows the correct syntax.")
                multi_line_input = ""
                first_input = True
            else:
                multi_line_input += user_input + '\n'
            if user_input.upper() == "EXIT":
                break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()

