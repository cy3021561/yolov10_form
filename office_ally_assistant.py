import os
import platform
import time
from computer.control import Control
from template_alignment.template_alignment import TemplateAligner
from utils.generate_selection_list import load_dictionary



class OfficeAllyAssistant:
    def __init__(self, page="general", input_information=None):
        self.operating_system = platform.system()
        self.page = page # Use this to distinguish webpage categories
        self.template_img_dir, self.template_config_dir = self._initialize_template_dir()
        self.input_information = input_information
        self.modifier_key = self._initialize_modifier_key()
        self.scroll_amount_per_click = None
        self.scroll_total_clicks_current_page = None
        self.scroll_click_now = 0
        self.control = Control(modifier_key=self.modifier_key)
        self.aligner = TemplateAligner()
        self.page_elements_coors = {} # {NAME: (scrolling_clicks, coor_x, coor_y)}

    def _initialize_modifier_key(self):
        if self.operating_system.lower() == "darwin":
            return "command"
        else:
            return "ctrl"

    def _initialize_template_dir(self):
        base_dir = "./templates"
        page_dirs = {
            "general": (
                os.path.join(base_dir, "officeAlly_general", "images"),
                os.path.join(base_dir, "officeAlly_general", "configs"),
            ),
            "patient": (
                os.path.join(base_dir, "officeAlly_patient_input", "images"),
                os.path.join(base_dir, "officeAlly_patient_input", "configs"),
            ),
            "insurance": (
                os.path.join(base_dir, "officeAlly_insurance_input", "images"),
                os.path.join(base_dir, "officeAlly_insurance_input", "configs"),
            ),
        }
        if self.page not in page_dirs:
            raise ValueError(f"Invalid page type: {self.page}")
        return page_dirs[self.page]
    
    def _intialize_scrolling_parameters(self):
        first_y, second_y = None, None
        anchor_template = "anchor"
        footer_template = "footer"
        self.control.mouse_move(self.aligner.screen_width // 2, self.aligner.screen_height // 2)
        self.control.mouse_scroll(100)
        if self.get_coordinates(anchor_template):
            # self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            # self.control.mouse_click(clicks=1)
            first_y = self.aligner.current_y
            self.control.mouse_scroll(-1)
            time.sleep(0.5)
        if self.get_coordinates(anchor_template):
            second_y = self.aligner.current_y
            self.control.mouse_scroll(1)
        distance_per_click = int(abs(second_y - first_y))
        self.scroll_amount_per_click = distance_per_click

        total_scroll = 0
        while not self.get_coordinates(footer_template):
            self.control.mouse_scroll(-10)
            total_scroll += 10
        self.scroll_total_clicks_current_page = total_scroll

        # Back to top
        self.control.mouse_scroll(self.scroll_total_clicks_current_page)
        return
    
    # NEED MODIFY
    def change_page(self, page, input_information):
        column_name = "to_" + page + "_from_" + self.page # Need a more comprehensive method for this in the future
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
            self.control.mouse_click(clicks=2)
            self.page = page
            self.input_information = input_information
            self.template_img_dir, self.template_config_dir = self._initialize_template_dir()
        else:
            raise RuntimeError(
                f"An error occurred while changing page. "
            )
        return
        
    def scroll_and_get_coors(self, column_name):
        target_scroll_click, coor_x, coor_y = self.page_elements_coors[column_name]
        if target_scroll_click != self.scroll_click_now:
            self.control.mouse_scroll(self.scroll_click_now)
            self.control.mouse_scroll(-target_scroll_click)
            self.scroll_click_now = target_scroll_click
        return coor_x, coor_y

    def get_coordinates(self, column_name):
        img_pth = os.path.join(self.template_img_dir, column_name + ".png")
        if not self.aligner.align(img_pth):
            return False
        return True
    
    def get_all_coordinates_on_page(self):
        self.page_elements_coors = {}
        scrolling_count = 0
        # When you not reaching the end of the page and you haven't found every coors yet, keep searching
        while scrolling_count <= self.scroll_total_clicks_current_page and (len(self.page_elements_coors) < len(self.input_information)):
            for key in self.input_information.keys():
                if key not in self.page_elements_coors and self.get_coordinates(key):
                    self.page_elements_coors[key] = (scrolling_count, self.aligner.current_x, self.aligner.current_y)
            self.control.mouse_scroll(-5)
            scrolling_count += 5
        self.control.mouse_scroll(scrolling_count + 5)
        return

    def check_filled_content(self, columm_value):
        """
        Crop the section based on coordinates, and use ocr to check the content
        """
        pass

    # Need a more realiable logic
    # Command + up would go to the first item
    def fill_dropdown_column(self, column_name, column_value):
        if column_name in self.page_elements_coors:
            coor_x, coor_y = self.scroll_and_get_coors(column_name)
            config_pth = os.path.join(self.template_config_dir, column_name + ".json")
            config_dict = load_dictionary(config_pth)
            try:
                press_key, press_time = config_dict[column_value]
            except Exception as e:
                raise RuntimeError(
                    f"An error occurred while finding value in template dictionary: {e}"
                )
            self.control.mouse_move(coor_x, coor_y, smooth=True)
            self.control.mouse_click(clicks=1)
            # self.scroll_after_fill()
            self.control.keyboard_hotkey(self.modifier_key, 'up')
            self.control.keyboard_press('space')
            self.control.keyboard_release_all_keys() # Release all possible functional key to prevent from activate any hotkey
            self.control.keyboard_press(press_key, presses=press_time)
        return
            
    def fill_inputbox_column(self, column_name, column_value, can_paste=True):
        if column_name in self.page_elements_coors:
            coor_x, coor_y = self.scroll_and_get_coors(column_name)
            self.control.mouse_move(coor_x, coor_y, smooth=True)
            self.control.mouse_click(clicks=2) # The double clicking is to ensure we focus on the field
            # self.scroll_after_fill()
            self.control.keyboard_write(column_value, copy_paste=can_paste)
        return

    # Click popout -> type keyword + enter to search -> template alignment to click the select button
    def fill_popout_column(self, column_name, column_value):
        if column_name in self.page_elements_coors:
            coor_x, coor_y = self.scroll_and_get_coors(column_name)
            self.control.mouse_move(coor_x, coor_y, smooth=True)
            self.control.mouse_click(clicks=1)
            # self.scroll_after_fill()
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
        if column_name in self.page_elements_coors:
            coor_x, coor_y = self.scroll_and_get_coors(column_name)
            self.control.mouse_move(coor_x, coor_y, smooth=True)
            self.control.mouse_click(clicks=1)
            # self.scroll_after_fill()
            self.control.keyboard_write(column_value)
            self.control.keyboard_press(['enter', 'tab', 'space', 'esc'])
        return

    def fill_information(self):
        # Initialize the scroll amount per click if it's not set
        # if not self.scroll_amount_per_click and self.input_information:
        self._intialize_scrolling_parameters()
        
        self.get_all_coordinates_on_page()
        
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

        # Back to top
        self.control.mouse_scroll(self.scroll_click_now + 10)
        
        # Scrolling to top (NEED CHECK) -> something var to calculate how far have you scrooled
        # self.control.mouse_scroll(100)
        return







def test(patient_input, insurance_input):
    import time
    start = time.time()
    assistant = OfficeAllyAssistant(page="patient", input_information=patient_input)
    time.sleep(2)
    # Fill patient information
    assistant.fill_information()

    # Fill insurance information
    assistant.change_page(page="insurance", input_information=insurance_input)
    assistant.fill_information()
    end = time.time()
    print(f"Total process time: {end - start} secs")

if __name__ == "__main__":
    # Need a input validation method
    test_patient_input = {
        "last_name": "Patient",
        "first_name": "Jane",
        "birth_date": "05231986",
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