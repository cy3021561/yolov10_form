import os
import json
import platform
import time
from computer.control import Control
from computer.screen_effect import ScreenOverlay, OverlayState
from template_alignment.template_alignment import TemplateAligner



class EMRAssistant:
    def __init__(self, page="general", config_path="./emr_templates/officeAlly/config.json", input_information=None, template_img_dir=None, template_config_dir=None):
        """
        Initialize the assistant with page type and optional custom template directories.
        """
        # Initialize basic attributes first
        self.operating_system = platform.system()
        self.page = page
        self.config_path = config_path
        self.input_information = input_information
        self.modifier_key = self._initialize_modifier_key()
        self.scroll_amount_per_click = None
        self.scroll_total_clicks_current_page = None
        self.scroll_click_now = 0
        self.control = Control(modifier_key=self.modifier_key)
        self.aligner = TemplateAligner()
        self.page_elements_coors = {}
        
        # Initialize overlay
        self.overlay = ScreenOverlay()
        self.overlay.set_state(OverlayState.READY)
        self.overlay.update_status("Initializing system...")
        
        try:
            # Load configurations
            self.config_data = self._load_config(self.config_path)
            self.general_img_dir = os.path.join(self.config_data["base_dir"], self.config_data["general_paths"]["images"])
            self.general_config_dir = os.path.join(self.config_data["base_dir"], self.config_data["general_paths"]["configs"])

            if template_img_dir and template_config_dir:
                self.template_img_dir = template_img_dir
                self.template_config_dir = template_config_dir
            else:
                self.template_img_dir, self.template_config_dir = self._initialize_template_dir_from_config(self.config_data)
                
            self.overlay.update_status("System initialized")
        except Exception as e:
            self.overlay.update_status(f"Initialization error: {str(e)}")
            self.overlay.set_state(OverlayState.RUNNING)  # Red to indicate error
            raise e

    def _initialize_modifier_key(self):
        if self.operating_system.lower() == "darwin":
            return "command"
        else:
            return "ctrl"

    def _load_config(self, config_path):
        """
        Loads the JSON configuration file.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
        with open(config_path, 'r') as f:
            return json.load(f)

    def _initialize_template_dir_from_config(self, config_data):
        """
        Initializes template directories from JSON config.
        """
        base_dir = config_data["base_dir"]
        page_dirs = config_data["pages"]

        if self.page not in page_dirs:
            raise ValueError(f"Invalid page type: {self.page}")
        
        page_info = page_dirs[self.page]
        img_dir = os.path.join(base_dir, page_info["images"])
        config_dir = os.path.join(base_dir, page_info["configs"])

        return img_dir, config_dir
    
    def get_scrolling_parameters(self):
        self.overlay.set_state(OverlayState.RUNNING)
        self.overlay.update_status("Initializing scrolling parameters...")
        
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
        self.overlay.update_status("Scrolling parameters initialized")
        return
    
    def assign_task(self, task_name):
        if task_name not in self.config_data["task_route"]:
            raise ValueError(f"Invalid task: {task_name}")
        route_items = self.config_data["task_route"][task_name]
        # Back to top
        self.control.mouse_move(self.aligner.screen_width // 2, self.aligner.screen_height // 2)
        self.control.mouse_scroll(100)

        # Back to home page first, need optimized for reading the homepage images
        for home_img_name in ["homepage_0", "homepage_1", "homepage_2"]:
            if self.get_coordinates(column_name=home_img_name, img_dir=self.general_img_dir):
                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
                self.control.mouse_click(clicks=2)
                time.sleep(3)
                break
            
        for img_name in route_items:
            if self.get_coordinates(column_name=img_name, img_dir=self.general_img_dir):
                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
                self.control.mouse_click(clicks=2)
                time.sleep(3)
            else:
                raise RuntimeError (f"Failed for assigning new task, step {img_name}")
        print(route_items)

    # NEED MODIFY
    def change_page_within_task(self, page, input_information):
        column_name = "to_" + page + "_from_" + self.page # Need a more comprehensive method for this in the future
        if self.get_coordinates(column_name):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
            self.control.mouse_click(clicks=2)
            self.page = page
            self.input_information = input_information
            self.template_img_dir, self.template_config_dir = self._initialize_template_dir_from_config(self.config_data)
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

    def get_coordinates(self, column_name, img_dir=None):
        if not img_dir:
            img_pth = os.path.join(self.template_img_dir, column_name + ".png")
        else:
            img_pth = os.path.join(img_dir, column_name + ".png")
        if not self.aligner.align(img_pth):
            return False
        return True
    
    # TODO: What if you can't find all matches
    def get_all_coordinates_on_page(self):
        self.overlay.update_status("Detecting page elements...")
        self.page_elements_coors = {}
        scrolling_count = 0
        # When you not reaching the end of the page and you haven't found every coors yet, keep searching
        while scrolling_count <= self.scroll_total_clicks_current_page and (len(self.page_elements_coors) < len(self.input_information)):
            for key in self.input_information.keys():
                if key not in self.page_elements_coors and self.get_coordinates(key):
                    self.page_elements_coors[key] = (scrolling_count, self.aligner.current_x, self.aligner.current_y)
            if len(self.page_elements_coors) == len(self.input_information):
                break
            self.control.mouse_scroll(-5)
            scrolling_count += 5
        self.control.mouse_scroll(scrolling_count + 5)
        self.overlay.update_status("Page elements detected")
        return
    
    # TODO
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
            config_dict = self._load_config(config_pth)
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
            time.sleep(1)

            self.control.keyboard_write(column_value)
            self.control.keyboard_press('enter')
            
            time.sleep(1)
            if self.get_coordinates("select_button"):
                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
                self.control.mouse_click(clicks=1)
                time.sleep(1)
        return
    
    # Click -> Fill in -> Enter -> Tab -> Space -> Esc
    def fill_searchbox_column(self, column_name, column_value):
        if column_name in self.page_elements_coors:
            coor_x, coor_y = self.scroll_and_get_coors(column_name)
            self.control.mouse_move(coor_x, coor_y, smooth=True)
            self.control.mouse_click(clicks=1)
            self.control.keyboard_write(column_value)
            self.control.keyboard_press(['enter', 'tab', 'space', 'esc'])
        return
    
    # TODO: NEED A BETTER LOGIC
    def fill_visit_patient_id(self, column_name, column_value):
        if column_name in self.page_elements_coors:
            coor_x, coor_y = self.scroll_and_get_coors(column_name)
            self.control.mouse_move(coor_x, coor_y, smooth=True)
            self.control.mouse_click(clicks=1)
            time.sleep(1)
            last_name_val = column_value["last_name"]
            birth_date_val = column_value["birth_date"]
            self.control.keyboard_write(last_name_val)
            self.control.keyboard_press('tab', presses=4)
            self.control.keyboard_write(birth_date_val, copy_paste=False)
            self.control.keyboard_press('tab', presses=4)
            self.control.keyboard_press('enter')

            # TODO: What if there's no search result?
            while not self.get_coordinates("select_button"):
                time.sleep(1)

            self.control.keyboard_press('tab', presses=16)
            self.control.keyboard_press('enter')

        return

    def fill_visit_provider_id(self, column_name, column_value):
        if column_name in self.page_elements_coors:
            coor_x, coor_y = self.scroll_and_get_coors(column_name)
            self.control.mouse_move(coor_x, coor_y, smooth=True)
            self.control.mouse_click(clicks=1)
            time.sleep(1)
            last_name_val = column_value["last_name"]
            self.control.keyboard_write(last_name_val)
            self.control.keyboard_press('enter')

            # TODO: What if there's no search result?
            while not self.get_coordinates("select_button"):
                time.sleep(1)

            self.control.keyboard_press('tab', presses=12)
            self.control.keyboard_press('enter')
            # self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
            # self.control.mouse_click(clicks=1)

        return

    def fill_ICD_10_codes(self, column_name, column_value):
        """
        Args: column_value: List of strings. e.g. ["CODE1", "CODE2", ...]
        """
        if column_name in self.page_elements_coors:
            coor_x, coor_y = self.scroll_and_get_coors(column_name)
            self.control.mouse_move(coor_x, coor_y, smooth=True)
            self.control.mouse_click(clicks=1)
            for i, code in enumerate(column_value):
                if i != 0:
                    self.control.keyboard_press('tab', presses=2)
                self.control.keyboard_write(code)
                # TODO: check the potential options are loaded
                time.sleep(1)
                # Select option
                self.control.keyboard_press(['down', 'enter'])

    def fill_CPT_codes(self, column_name, column_value):
        """
        Args: column_value: List of tuple. e.g. [("CODE1", "POINTER1"), ("CODE2", "POINTER2") ...]
        """
        if column_name in self.page_elements_coors:
            coor_x, coor_y = self.scroll_and_get_coors(column_name)
            self.control.mouse_move(coor_x, coor_y, smooth=True)
            self.control.mouse_click(clicks=1)
            time.sleep(1)
            for i, (code, pointer) in enumerate(column_value):
                if i != 0:
                    self.control.keyboard_press('tab', presses=11)
                    self.control.keyboard_press('enter')
                self.control.keyboard_write(code)
                self.control.keyboard_press('enter')

                # TODO: What if there's no search result?
                while not self.get_coordinates("select_button"):
                    time.sleep(1)

                self.control.mouse_move(self.aligner.current_x, self.aligner.current_y, smooth=True)
                self.control.mouse_click(clicks=1)
                time.sleep(1)
                
                # Pointer
                self.control.keyboard_press('tab', presses=5)
                self.control.keyboard_write(pointer, copy_paste=False)

    def cleanup(self):
        """
        Clean up resources
        """
        try:
            self.overlay.update_status("Cleaning up...")
            self.overlay.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

    
    def run(self):
        """
        Execute the task for the current page.
        """
        try:
            self.overlay.set_state(OverlayState.RUNNING)
            self.overlay.update_status("Starting task...")
            
            self.get_scrolling_parameters()
            self.get_all_coordinates_on_page()
            
            total_items = len(self.input_information)
            for idx, (column_name, column_value) in enumerate(self.input_information.items(), 1):
                self.overlay.update_status(f"Processing data ({idx}/{total_items})")
                
                try:
                    if column_name in ["legal_sex", "state", "patient_relationship_primary", "patient_relationship_second"]:
                        self.fill_dropdown_column(column_name, column_value)
                    elif column_name in ["insurance_co_primary", "insurance_co_second", "facility", "billing_provider"]:
                        self.fill_popout_column(column_name, column_value)
                    elif column_name in ["insurance_type_primary", "insurance_type_second"]:
                        self.fill_searchbox_column(column_name, column_value)
                    elif column_name in ["patient_id"]:
                        self.fill_visit_patient_id(column_name, column_value)
                    elif column_name in ["provider_id"]:
                        self.fill_visit_provider_id(column_name, column_value)
                    elif column_name in ["icd10_codes"]:
                        self.fill_ICD_10_codes(column_name, column_value)
                    elif column_name in ["cpt_codes"]:
                        self.fill_CPT_codes(column_name, column_value)
                    elif column_name in ["birth_date", "ssn", "zip_code", "cell_phone", "hospital_dates"]:
                        self.fill_inputbox_column(column_name, column_value, can_paste=False)
                    else:
                        self.fill_inputbox_column(column_name, column_value)
                except Exception as e:
                    self.overlay.update_status(f"Error processing {column_name}: {str(e)}")
                    raise e

            # Back to top
            self.control.mouse_scroll(self.scroll_click_now + 10)
            self.overlay.update_status("Page completed successfully")
            self.overlay.set_state(OverlayState.READY)
            
        except Exception as e:
            self.overlay.update_status(f"Page failed: {str(e)}")
            self.overlay.set_state(OverlayState.RUNNING)  # Red to indicate error
            raise e



def test_add_new_patient(task_name, patient_input, insurance_input):
    assistant = None
    try:
        assistant = EMRAssistant(page="patient", input_information=patient_input)
        time.sleep(2)  # Allow overlay to initialize

        # Go to the task page
        assistant.overlay.update_status(f"Task: ADD NEW PATIENT...")
        assistant.assign_task(task_name=task_name)
        
        # Fill patient information
        assistant.run()

        # Fill insurance information
        assistant.overlay.update_status("Switching to insurance page...")
        assistant.change_page_within_task(page="insurance", input_information=insurance_input)
        assistant.run()

        assistant.overlay.set_state(OverlayState.READY)
        assistant.overlay.update_status("Task done.")
        time.sleep(3)

    except Exception as e:
        if assistant and assistant.overlay:
            assistant.overlay.update_status(f"Process failed: {str(e)}")
            assistant.overlay.set_state(OverlayState.RUNNING)  # Red to indicate error
        raise e
    finally:
        if assistant:
            assistant.cleanup()

def test_add_new_visit(task_name, visit_info, billing_info, billing_options):
    assistant = None
    try:
        assistant = EMRAssistant(page="visit_info", input_information=visit_info)
        time.sleep(5)  # Allow overlay to initialize

        # Go to the task page
        assistant.overlay.update_status(f"Task: ADD NEW VISIT...")
        assistant.assign_task(task_name=task_name)
        
        # Fill visit info page
        assistant.run()

        # Fill billing info page
        assistant.overlay.update_status("Switching to billing info page...")
        assistant.change_page_within_task(page="billing_info", input_information=billing_info)
        
        if assistant.get_coordinates("ICD_type_9_to_10"):
            assistant.overlay.update_status("Switching to ICD-10...")
            assistant.control.mouse_move(assistant.aligner.current_x, assistant.aligner.current_y)
            assistant.control.mouse_click()
            
        assistant.run()

        # Fill billing options page
        assistant.overlay.update_status("Switching to billing options page...")
        assistant.change_page_within_task(page="billing_options", input_information=billing_options)
        assistant.run()

        assistant.overlay.set_state(OverlayState.READY)
        assistant.overlay.update_status("Task done.")
        time.sleep(3)
    except Exception as e:
        if assistant and assistant.overlay:
            assistant.overlay.update_status(f"Process failed: {str(e)}")
            assistant.overlay.set_state(OverlayState.RUNNING)  # Red to indicate error
        raise e
    finally:
        if assistant:
            assistant.cleanup()

    

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
        "email": "abc.ddd@gmail.com",
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

    test_visit_info = {
        "patient_id" : {
            "last_name": "Patient",
            "birth_date": "11011999",
        },
        "provider_id": {
            "last_name": "Doctor",
        },

    }

    test_billing_info = {
        "icd10_codes" : ["F200", "E119"],
        "cpt_codes": [("99232", "A"), ("99213", "B")],

    }

    test_billing_options = {
        "facility" : "SACF",
        "billing_provider": "",
        "hospital_dates": "10252024"

    }


    start = time.time()
    # test_add_new_patient("add_new_patient", test_patient_input, test_insurance_input)
    test_add_new_visit("add_new_visit", test_visit_info, test_billing_info, test_billing_options)
    end = time.time()
    print(f"Total process time: {end - start} secs")
    # Need a uniform checking methods for window loading, current too hard-coding
    # Need a field content checking method