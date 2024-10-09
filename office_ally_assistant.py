import os
from computer.control import Control
from template_alignment.template_alignment import TemplateAligner
from utils.generate_selection_list import load_dictionary


class OfficeAllyAssistant:
    def __init__(self, page="patient"):
        self.control = Control()
        self.aligner = TemplateAligner()
        self.page = page # Use this to distinguish webpage categories
        self.template_img_dir, self.template_config_dir = self._initialize_template_dir()
        self.input_information = None

    def _initialize_template_dir(self):
        base_dir = "./templates"
        page_dirs = {
            "patient": (
                os.path.join(base_dir, "officeAlly_patient", "images"),
                os.path.join(base_dir, "officeAlly_patient", "configs"),
            ),
            # Other page types...
        }
        if self.page not in page_dirs:
            raise ValueError(f"Invalid page type: {self.page}")
        return page_dirs[self.page]
    
    def update_page(self, page):
        self.page = page
        self.template_img_dir, self.template_config_dir = self._initialize_template_dir()

    def get_coordinates(self, column_name):
        img_pth = os.path.join(self.template_img_dir, column_name + ".png")
        if not self.aligner.align(img_pth):
            print("No alignment.")
            return False
        return True


    def fill_dropdown_column(self, column_name, column_value):
        if self.get_coordinates(column_name):
            config_pth = os.path.join(self.template_config_dir, column_name + ".json")
            config_dict = load_dictionary(config_pth)
            try:
                press_key, press_time = config_dict[column_value]
            except Exception as e:
                raise RuntimeError(
                    f"An error occurred while finding value in template dictionary: {e}"
                )
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=False)
            self.control.mouse_click(clicks=2)
            self.control.keyboard_press(press_key, presses=press_time)

    def fill_inputbox_column(self, column_name, column_value):
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=False)
            self.control.mouse_click(clicks=2)
            self.control.keyboard_write(column_value)


    def fill_information(self):
        for column_name, column_value in self.input_information.items():
            print(column_name, column_value)
            if column_value == "DONE":
                print(f"Column {column_name} already filled.")
                continue
            if column_name in ["legal_sex", "state"]:
                self.fill_dropdown_column(column_name, column_value)   
            else:
                self.fill_inputbox_column(column_name, column_value)
            self.input_information[column_name] = "DONE"
        print(self.input_information)

def test(input_pairs):
    assistant = OfficeAllyAssistant()
    assistant.input_information = input_pairs
    assistant.fill_information()


if __name__ == "__main__":
    # Need a input validation method
    test_input = {
        "last_name": "Yang",
        "first_name": "Tom",
        "birth_date": "11011001",
        "legal_sex": "Male",
        "ssn": "123456789",
        "address1": "123 N Apple Ave",
        "address2": "Apt. C",
        "city": "Los Angeles",
        "state": "MH",
        "zip_code": "12345",
        "cell_phone": "2342345555",
        "email": "abc.ddd@gmail.com"
    }

    test(test_input)