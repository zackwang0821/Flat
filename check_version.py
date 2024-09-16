import argparse
import ctypes
import os
import struct
import re

def get_file_properties(file_path):
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(file_path, None)
        if not size:
            raise ValueError("File does not contain version info")

        res = ctypes.create_string_buffer(size)
        ctypes.windll.version.GetFileVersionInfoW(file_path, None, size, res)

        translation_block = ctypes.c_void_p()
        length = ctypes.c_uint()

        success = ctypes.windll.version.VerQueryValueW(res, r'\\VarFileInfo\\Translation', ctypes.byref(translation_block), ctypes.byref(length))
        if not success or length.value < 4:
            raise ValueError("Invalid translation block")

        lang, codepage = struct.unpack('<HH', ctypes.string_at(translation_block, 4))

        def query_value(name):
            value_pointer = ctypes.c_wchar_p()
            length = ctypes.c_uint()
            sub_block = f'\\StringFileInfo\\{lang:04x}{codepage:04x}\\{name}'
            success = ctypes.windll.version.VerQueryValueW(res, sub_block, ctypes.byref(value_pointer), ctypes.byref(length))
            return value_pointer.value if success else None

        file_info = {
            'FileVersion': query_value('FileVersion'),
        }

        return file_info

    except Exception as e:
        print(f"Error getting file properties: {e}")
        return None

def find_largest_table_and_pv_value(file_path, output_file):
    table_pattern = re.compile(r'TABLE_(\d+)')
    pv_pattern = re.compile(r'PV=([\d.]+)')

    largest_table = 0
    pv_value = None

    with open(file_path, 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        match_table = table_pattern.search(line)
        if match_table:
            table_number = int(match_table.group(1))
            if table_number > largest_table:
                largest_table = table_number
                for j in range(i + 1, len(lines)):
                    match_pv = pv_pattern.search(lines[j])
                    if match_pv:
                        pv_value = match_pv.group(1)
                        break

    if pv_value:
        with open(output_file, 'w') as output:
            output.write(pv_value)
        print(f"PV value '{pv_value}' from TABLE_{largest_table}.")
    else:
        print("No PV value found.")

def compare_files(file1, file2):
    if not os.path.exists(file1):
        print(f"File {file1} does not exist.")
        return

    if not os.path.exists(file2):
        print(f"File {file2} does not exist.")
        return

    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        content1 = f1.read().strip()
        content2 = f2.read().strip()

    print(f"config.ini version: {content1}")
    print(f"DockFWInfo.dll version: {content2}")

    if content1 == content2:
        print('\033[92mVersion the same!\033[0m')
    else:
        print('\033[91mVersion doesn\'t match! Please check your "config.ini" or "DockFWInfo.dll"\033[0m')

def main():
    parser = argparse.ArgumentParser(description='Check version information.')
    parser.add_argument('-a', action='store_true', help='Retrieve file properties from DockFWInfo.dll')
    parser.add_argument('-b', action='store_true', help='Extract the largest table number and PV value from config.ini')
    parser.add_argument('-c', action='store_true', help='Compare the extracted version values')

    args = parser.parse_args()

    if args.a:
        file_path = r'DockFWInfo.dll'
        if os.path.exists(file_path):
            properties = get_file_properties(file_path)
            if properties:
                file_version = properties['FileVersion']
                with open("dllVersion.txt", "w") as f:
                    f.write(f"{file_version}")
                for key, value in properties.items():
                    print(f"{key}: {value}")
            else:
                print("No properties found.")
        else:
            print("File does not exist.")

    if args.b:
        file_path = 'config.ini'
        output_file = 'configVersion.txt'
        find_largest_table_and_pv_value(file_path, output_file)

    if args.c:
        compare_files('configVersion.txt', 'dllVersion.txt')

if __name__ == "__main__":
    main()
