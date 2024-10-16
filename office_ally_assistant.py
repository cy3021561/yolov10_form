import os
import platform
import time
from computer.control import Control
from template_alignment.template_alignment import TemplateAligner
from utils.generate_selection_list import load_dictionary



class OfficeAllyAssistant:
    def __init__(self, page="patient", input_information=None):
        self.operating_system = platform.system()
        self.page = page # Use this to distinguish webpage categories
        self.template_img_dir, self.template_config_dir = self._initialize_template_dir()
        self.input_information = input_information
        self.modifier_key = self._initialize_modifier_key()
        self.scroll_amount_per_click = None
        self.control = Control(modifier_key=self.modifier_key)
        self.aligner = TemplateAligner()

    def _initialize_modifier_key(self):
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
    
    def _intialize_scrolling_amount_per_click(self):
        first_y, second_y = None, None
        column_name = list(self.input_information.keys())[0]
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            self.control.mouse_click(clicks=1)
            first_y = self.aligner.current_y
            self.control.mouse_scroll(-1)
            time.sleep(0.5)
        if self.get_coordinates(column_name):
            second_y = self.aligner.current_y
            self.control.mouse_scroll(1)
        distance_per_click = int(abs(second_y - first_y))
        self.scroll_amount_per_click = distance_per_click
        print(self.scroll_amount_per_click)
        return
    
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
        return
        
    def get_coordinates(self, column_name):
        img_pth = os.path.join(self.template_img_dir, column_name + ".png")
        if not self.aligner.align(img_pth):
            return False
        return True

    def check_filled_content(self, columm_value):
        """
        Crop the section based on aligner's current coordinates, and use ocr to check the content
        """
        pass

    # Need a more realiable logic
    # Command + up would go to the first item
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
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            self.control.mouse_click(clicks=1)
            self.control.keyboard_hotkey(self.modifier_key, 'up')
            self.control.keyboard_press('space')
            self.control.keyboard_release_all_keys() # Release all possible functional key to prevent from activate any hotkey
            self.control.keyboard_press(press_key, presses=press_time)
        return
            
    def fill_inputbox_column(self, column_name, column_value, can_paste=True):
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            self.control.mouse_click(clicks=2) # The double clicking is to ensure we focus on the field
            # self.control.keyboard_release_all_keys()
            self.control.keyboard_write(column_value, copy_paste=can_paste)
        return

    # Click popout -> type keyword + enter to search -> template alignment to click the select button
    def fill_popout_column(self, column_name, column_value):
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            self.control.mouse_click(clicks=1)
            # Wait popout window loading
            while not self.get_coordinates('loadcheck_insurance_list'):
                time.sleep(1)
                print("Still loading...")
            self.control.keyboard_write(column_value)
            self.control.keyboard_press('enter')
            
            if self.get_coordinates("no_results"):
                self.control.keyboard_hotkey(self.modifier_key, 'w')
            elif self.get_coordinates("select_button"):
                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
                self.control.mouse_click(clicks=1)
        return
    
    # Click -> Fill in -> Enter -> Tab -> Space -> Esc
    def fill_searchbox_column(self, column_name, column_value):
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            self.control.mouse_click(clicks=1)
            self.control.keyboard_write(column_value)
            self.control.keyboard_press(['enter', 'tab', 'space', 'esc'])
        return

    def fill_information(self):
        # Initialize the scroll amount per click if it's not set
        if not self.scroll_amount_per_click and self.input_information:
            self._intialize_scrolling_amount_per_click()
            exit()
        
        for column_name, column_value in self.input_information.items():
            print(column_name, column_value)
            if column_name in ["legal_sex", "state", "patient_relationship_primary", "patient_relationship_second"]:
                self.fill_dropdown_column(column_name, column_value)
            elif column_name in ["insurance_co_primary", "insurance_co_second"]:
                self.fill_popout_column(column_name, column_value)
            elif column_name in ["insurance_type_primary", "insurance_type_second"]:
                self.fill_searchbox_column(column_name, column_value)
            # Numerical columns NOT allow paste action
            elif column_name in ["birth_date", "ssn", "zip_code", "cell_phone"]:
                self.fill_inputbox_column(column_name, column_value, can_paste=False)
            else:
                self.fill_inputbox_column(column_name, column_value)
        return


def test(patient_input, insurance_input):
    import time
    start = time.time()
    assistant = OfficeAllyAssistant(input_information=patient_input)

    # Fill patient information
    assistant.fill_information()

    # Change to insurance page
    assistant.change_page(page="insurance", input_dict=insurance_input)

    # Fill insurance information
    assistant.fill_information()
    end = time.time()
    print(f"Total process time: {end - start} secs")

if __name__ == "__main__":
    # Need a input validation method
    test_patient_input = {
        "last_name": "Patient",
        "first_name": "Jane",
        "birth_date": "11011999",
        "legal_sex": "Female",
        "ssn": "123456789",
        "address1": "123 N Apple Ave",
        "address2": "Apt C",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90045",
        "cell_phone": "2342345555",
        "email": "abc.ddd@gmail.com"
    }
    test_insurance_input = {
        "insurance_type_primary": "Medicare",
        "insurance_co_primary": "NORIDIAN HEALTHCARE SOLUTIONS",
        "patient_relationship_primary": "Self",
        "subscriber_id_primary": "11EG4TE5MK73",
        "group_no_primary": "",
        "insurance_type_second": "Medicaid",
        "insurance_co_second": "MEDICAL CONTRACTED",
        "patient_relationship_second": "Self",
        "subscriber_id_second": "99999999A",
    }
    test(test_patient_input, test_insurance_input)
    # Need a uniform checking methods for window loading, current too hard-code
    # Need a field content checking method
    # Need a scrolling logic, something like when it finish filling one section, scroll down for the next one
    ### Follow the top-down filling logic, each time after filling, check the column content