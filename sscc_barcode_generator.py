import flet as ft
from flet import (
    ElevatedButton,
    FilePicker,
    FilePickerResultEvent,
    Row,
    Text,
    icons,
)
import random
from pyepc import SSCC
from os import mkdir
from barcode import Gs1_128
from barcode.writer import ImageWriter
import pandas as pd


def main(page: ft.Page):
    main_object = {
        'csv_file': '',
        'save_dir': '',
    }

    # Pick files dialog
    def pick_files_result(e: FilePickerResultEvent):
        selected_files.value = (
            ", ".join(map(lambda f: f.path, e.files)) if e.files else "Cancelled!"
        )
        main_object['csv_file'] = e.files[0].path
        selected_files.update()

    pick_files_dialog = FilePicker(on_result=pick_files_result)
    selected_files = Text()

    # Open directory dialog
    def get_directory_result(e: FilePickerResultEvent):
        directory_path.value = e.path if e.path else "Cancelled!"
        main_object['save_dir'] = e.path
        directory_path.update()

    get_directory_dialog = FilePicker(on_result=get_directory_result)
    directory_path = Text()

    # hide all dialogs in overlay
    page.overlay.extend([pick_files_dialog, get_directory_dialog])

    gcpCode = ft.TextField(label="Enter GCP prefix")
    packCount = ft.TextField(label="Quantity per box")

    dlg = ft.AlertDialog(
        title=ft.Text("Generation completed"), on_dismiss=lambda e: print("Dialog dismissed!")
    )

    def randomnumber():
        minimum = pow(10, 7 - 1)
        maximum = pow(10, 7) - 1
        return random.randint(minimum, maximum)

    def generateSscc():
        company_prefix = gcpCode.value
        extension_digit = random.randint(0, 9)
        serial_ref = randomnumber()
        sscc = SSCC(company_prefix, extension_digit, serial_ref)
        return (sscc.gs1_element_string)

    def button_run_callback(e):
        with open(selected_files.value) as file:
            orders = file.readlines()
        chunksize = int(packCount.value)
        count = round(len(orders) / chunksize)
        code_list = []
        code_list_raw = []
        for i, chunk in enumerate(pd.read_csv(selected_files.value, chunksize=chunksize, header=None), 1):
            sscc_code_raw = generateSscc()
            code_list_raw.append(sscc_code_raw)
            sscc_code = sscc_code_raw.replace('(', '').replace(')', '')
            code_list.append(sscc_code)
            chunk.to_csv(f'{directory_path.value}/order_{i}_{count}_{sscc_code}.csv', index=False, header=False)

        with open(directory_path.value + '/sscc_codes.txt', 'x') as file:
            file.write("\n".join(map(str, code_list)))

        mkdir(directory_path.value + '/barcodes/')

        for code in code_list_raw:
            num = code.strip()
            book_barcode = Gs1_128(num, writer=ImageWriter())
            book_barcode.save(directory_path.value + '/barcodes/' + num,
                              {'font_size': 8, 'font_path': "C:\\Windows\\Fonts\\Arial\\arial.ttf"})

        page.dialog = dlg
        dlg.open = True
        page.update()

    generate_btn = ElevatedButton("Generate", on_click=button_run_callback)

    page.title = 'sscc and barcode generator'
    page.add(
        Row([
            ElevatedButton(
                "Select csv file with barcodes",
                icon=icons.UPLOAD_FILE,
                data=main_object,
                on_click=lambda _: pick_files_dialog.pick_files(),
            ),
        ]),
        Row([
            selected_files,
        ]),
        Row([
            ElevatedButton(
                "Select the directory where to save",
                icon=icons.FOLDER_OPEN,
                on_click=lambda _: get_directory_dialog.get_directory_path(),
                data=main_object,
                disabled=page.web,
            ),
        ]),
        Row([
            directory_path,
        ]),
        Row([
            gcpCode,
        ]),
        Row([
            packCount,
        ]),
        Row([
            generate_btn
        ]),
        dlg
    )
    page.window_width = 400
    page.window_height = 400
    page.update()


ft.app(target=main)
