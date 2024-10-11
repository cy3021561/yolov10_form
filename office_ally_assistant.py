import os
import platform
import time
from computer.control import Control
from template_alignment.template_alignment import TemplateAligner
from utils.generate_selection_list import load_dictionary



class OfficeAllyAssistant:
    def __init__(self, page="patient", input_information=None):
        self.control = Control()
        self.aligner = TemplateAligner()
        self.operating_system = platform.system()
        self.page = page # Use this to distinguish webpage categories
        self.template_img_dir, self.template_config_dir = self._initialize_template_dir()
        self.input_information = input_information
        self.control_key = self._initialize_control_key()

    def _initialize_control_key(self):
        if self.operating_system.lower() == "darwin":
            return "command"
        else:
            return "ctrl"

    def _initialize_template_dir(self):
        base_dir = "./templates"
        page_dirs = {
            "patient": (
                os.path.join(base_dir, "officeAlly_patient", "images"),
                os.path.join(base_dir, "officeAlly_patient", "configs"),
            ),
            "insurance": (
                os.path.join(base_dir, "officeAlly_insurance", "images"),
                os.path.join(base_dir, "officeAlly_insurance", "configs"),
            ),
        }
        if self.page not in page_dirs:
            raise ValueError(f"Invalid page type: {self.page}")
        return page_dirs[self.page]
    
    def change_page(self, page, input_dict):
        column_name = "to_" + page + "_from_" + self.page # Need a more comprehensive method for this in the future
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
            self.control.mouse_click(clicks=2)
            self.page = page
            self.input_information = input_dict
            self.template_img_dir, self.template_config_dir = self._initialize_template_dir()
        else:
            print("Change page failed.")
        

    def get_coordinates(self, column_name):
        img_pth = os.path.join(self.template_img_dir, column_name + ".png")
        if not self.aligner.align(img_pth):
            print("No alignment.")
            return False
        return True

    # Need a more realiable logic
    # Command + up would go to the first item
    def fill_dropdown_column(self, column_name, column_value):
        if self.get_coordinates(column_name):
            config_pth = os.path.join(self.template_config_dir, column_name + ".json")
            config_dict = load_dictionary(config_pth)
            try:
                press_key, press_time = config_dict[column_value]
                print(press_key, press_time)
            except Exception as e:
                raise RuntimeError(
                    f"An error occurred while finding value in template dictionary: {e}"
                )
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            self.control.mouse_click(clicks=1)
            self.control.keyboard_hotkey(self.control_key, 'up')
            self.control.keyboard_press('space')
            self.control.keyboard_release_all_keys() # Release all possible functional key to prevent from activate any hotkey
            self.control.keyboard_press(press_key, presses=press_time)
            
    def fill_inputbox_column(self, column_name, column_value):
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            self.control.mouse_click(clicks=2) # The double clicking is to ensure we focus on the field
            self.control.keyboard_release_all_keys()
            self.control.keyboard_write(column_value)

    # Click popout -> type in + enter to search -> template to click select
    def fill_popout_column(self, column_name, column_value):
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            self.control.mouse_click(clicks=1)
            time.sleep(3) # Wait for popout window show up, here also need a checking logic in the future
            self.control.keyboard_release_all_keys()
            self.control.keyboard_write(column_value)
            self.control.keyboard_press('enter')
            
            if self.get_coordinates("select_button"):
                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
                self.control.mouse_click(clicks=1)
            else: # Here we need another logic to handle when user input can't be found, and close the popout window
                pass

    def fill_information(self):
        for column_name, column_value in self.input_information.items():
            print(column_name, column_value)
            if column_name in ["legal_sex", "state", "patient_relationship_primary", "patient_relationship_second"]:
                self.fill_dropdown_column(column_name, column_value)
            elif column_name in ["insurance_co_primary", "insurance_co_second"]:
                self.fill_popout_column(column_name, column_value)
            else:
                self.fill_inputbox_column(column_name, column_value)

def test(patient_input, insurance_input):
    assistant = OfficeAllyAssistant(input_information=patient_input)

    # Fill patient information
    assistant.fill_information()

    # Change to insurance page
    assistant.change_page(page="insurance", input_dict=insurance_input)

    # Fill insurance information
    assistant.fill_information()

if __name__ == "__main__":
    # Need a input validation method
    test_patient_input = {
        "last_name": "Yang",
        "first_name": "Tom",
        "birth_date": "11011001",
        "legal_sex": "Male",
        "ssn": "123456789",
        "address1": "123 N Apple Ave",
        "address2": "Apt C",
        "city": "Los Angeles",
        "state": "MH",
        "zip_code": "12345",
        "cell_phone": "2342345555",
        "email": "abc.ddd@gmail.com"
    }
    test_insurance_input = {
        "insurance_co_primary": "apple abc",
        "patient_relationship_primary": "Self",
        "subscriber_id_primary": "778133h!ss",
        "group_no_primary": "0101",
        "insurance_co_second": "bamboo",
        "patient_relationship_second": "Child"
    }
    test(test_patient_input, test_insurance_input)
    # Need a field content checking method
    # Need a scrolling logic, something like when it finish filling one section, scroll down for the next one