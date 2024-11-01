import os
import json
import platform
import time
from computer.control import Control
from computer.screen_effect import ScreenOverlay, OverlayState
from template_alignment.template_alignment import TemplateAligner
from data.emr_data import EMRData



class EMRAssistant:
    def __init__(self, page="general", config_path="./emr_templates/officeAlly/config.json", input_data=None, template_img_dir=None, template_config_dir=None):
        """
        Initialize the assistant with page type and optional custom template directories.
        """
        self.operating_system = platform.system()
        self.page = page
        self.config_path = config_path
        self.emr_data = EMRData()
        self.modifier_key = self._initialize_modifier_key()
        self.scroll_total_clicks_current_page = None
        self.scroll_click_now = 0
        self.control = Control(modifier_key=self.modifier_key)
        self.aligner = TemplateAligner()
        self.page_elements_coors = {}
        
        # Initialize overlay
        self.overlay = ScreenOverlay()
        self.overlay.set_state(OverlayState.READY)
        self.overlay.update_status("Initializing system...")

        # Update with input_information if provided
        if input_data is not None:
            self.emr_data.update(input_data)
        
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
    
    def _handle_array_loop(self, steps, skip_in_last_loop, array_values):
        """Handle iteration over simple arrays"""
        values_length = len(array_values)
        steps_length = len(steps)
        for i, value in enumerate(array_values):
            for j, step in enumerate(steps):
                # Skip redundent actions for the last loop
                if i + 1 == values_length and (steps_length - skip_in_last_loop) == j:
                    break
                action_name, action_params = step
                # Set text directly for keyboard_write actions
                if action_name == "keyboard_write":
                    action_params = action_params.copy()  # Create a copy to avoid modifying original
                    action_params["text"] = value
                self.execute_action(action_name, action_params, value)

    def _handle_tuple_array_loop(self, steps, skip_in_last_loop, tuple_array):
        """Handle iteration over arrays of tuples"""
        values_length = len(tuple_array)
        steps_length = len(steps)
        for i, tuple_value in enumerate(tuple_array):
            for j, step in enumerate(steps):
                # Skip redundent actions for the last loop
                if i + 1 == values_length and (steps_length - skip_in_last_loop) == j:
                    break
                action_name, action_params = step
                # For keyboard_write, use tuple_index to get the right value
                if action_name == "keyboard_write":
                    action_params = action_params.copy()  # Create a copy to avoid modifying original
                    index = action_params.get("tuple_index", 0)
                    action_params["text"] = tuple_value[index]
                self.execute_action(action_name, action_params, tuple_value)
    
    def get_all_fields_name(self):
        """
        Returns a list of all PNG file names in the specified folder.
        """
        folder_path = self.template_img_dir
            
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Get all files in the folder and filter for .png extension
        png_names = [
            os.path.splitext(file)[0]  # splitext splits filename and extension
            for file in os.listdir(folder_path)
            if file.lower().endswith('.png')
        ]
        
        return png_names

    def get_scrolling_parameters(self):
        """Try to reach the end of the page"""
        self.overlay.set_state(OverlayState.RUNNING)
        self.overlay.update_status("Initializing scrolling parameters...")
        footer_template = "footer"
        self.control.mouse_move(self.aligner.screen_width // 2, self.aligner.screen_height // 2)
        self.control.mouse_scroll(100)

        # Start find a footer at the page
        total_scroll = 0
        while not self.get_coordinates(footer_template, img_dir=self.general_img_dir):
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

    # NEED MODIFY
    def change_page_within_task(self, target_page):
        column_name = "to_" + target_page + "_from_" + self.page # Need a more comprehensive method for this in the future
        if self.get_coordinates(column_name, img_dir=self.general_img_dir):
            self.control.mouse_move(self.aligner.current_x, self.aligner.current_y)
            self.control.mouse_click(clicks=2)
            self.page = target_page
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
        template_names = self.get_all_fields_name()

        # When you not reaching the end of the page and you haven't found every coors yet, keep searching
        while scrolling_count <= self.scroll_total_clicks_current_page and (len(self.page_elements_coors) < len(template_names)):
            for template in template_names:
                if template not in self.page_elements_coors and self.get_coordinates(template):
                    self.page_elements_coors[template] = (scrolling_count, self.aligner.current_x, self.aligner.current_y)
            if len(self.page_elements_coors) == len(template_names):
                break
            self.control.mouse_scroll(-5)
            scrolling_count += 5
        self.control.mouse_scroll(scrolling_count + 5)
        self.overlay.update_status("Page elements detected")
        return template_names
    
    # TODO
    def check_filled_content(self, columm_value):
        """
        Crop the section based on coordinates, and use ocr to check the content
        """
        pass

    def check_selection_options(self, column_name):
        config_pth = os.path.join(self.template_config_dir, column_name + ".json")
        try:
            selection_options = self._load_config(config_pth)
            return selection_options
        
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while finding value in template dictionary: {e}"
            )

    def execute_action(self, action_name, params, field_value=None):
        """
        Execute a single action based on the action name and parameters.
        """
        def process_text_value(params, field_value):
            if isinstance(field_value, dict):
                return field_value.get(params.get("text_key", ""))
            elif isinstance(field_value, (list, tuple)):
                if "tuple_index" in params:
                    return field_value[params.get("tuple_index")]
                return field_value
            return field_value
        
        action_map = {
            "mouse_move": lambda p: self.control.mouse_move(
                coor_x=p.get("x"),
                coor_y=p.get("y"),
                smooth=p.get("smooth", True)
            ),
            
            "mouse_click": lambda p: self.control.mouse_click(
                button=p.get("button", "left"),
                clicks=p.get("clicks", 1),
                interval=p.get("interval", 0.1)
            ),
            
            "keyboard_write": lambda p: self.control.keyboard_write(
                text=p.get("text") if "text" in p else process_text_value(p, field_value),
                interval=p.get("interval", 0.01),
                copy_paste=p.get("can_paste", True)
            ),
            
            "keyboard_press": lambda p: self.control.keyboard_press(
                button=p.get("key"),
                presses=p.get("presses", 1),
                interval=p.get("interval", 0.1)
            ),
            
            "keyboard_hotkey": lambda p: self.control.keyboard_hotkey(
                *(self.modifier_key if key == "<MODIFIER_KEY>" else key 
                for key in p.get("keys", [])),
                interval=p.get("interval", 0.1)
            ),
            
            "keyboard_release_all_keys": lambda p: self.control.keyboard_release_all_keys(),
            
            "mouse_scroll": lambda p: self.control.mouse_scroll(
                clicks=p.get("clicks", 0)
            ),

            "wait_for_template": lambda p: self.get_coordinates(p.get("template_name"), img_dir=self.general_img_dir),

            "loop_array": lambda p: self._handle_array_loop(p.get("steps", []), p.get("skip_in_last_loop", 0), field_value),

            "loop_tuple_array": lambda p: self._handle_tuple_array_loop(p.get("steps", []), p.get("skip_in_last_loop", 0), field_value),
            
            "wait": lambda p: time.sleep(p.get("seconds", 1))
        }

        if action_name not in action_map:
            raise ValueError(f"Unknown action: {action_name}")

        result = action_map[action_name](params)
    
        # Special handling for template waiting
        if action_name == "wait_for_template":
            if not result:
                return False
            # Update coordinates for next mouse move
            return True
        
        return True

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
        Execute the task for the current page using the configuration file.
        """
        try:
            self.overlay.set_state(OverlayState.RUNNING)
            self.overlay.update_status("Starting task...")
            
            # Initialize scrolling and get coordinates
            self.get_scrolling_parameters()
            self.get_all_coordinates_on_page()

            # Load step configuration file
            step_config = self._load_config(os.path.join(self.template_config_dir, "steps.json"))
            
            total_items = len(self.page_elements_coors)
            for i, field_name in enumerate(self.page_elements_coors.keys(), 1):
                self.overlay.update_status(f"Processing field ({i}/{total_items}): {field_name}")
                
                try:
                    # Get the steps for this field
                    if field_name not in step_config:
                        raise ValueError(f"No configuration found for field: {field_name}")

                    steps = step_config[field_name]
                    field_value = ""
                    
                    # Get the final coordinates after right scrolling
                    x, y = self.scroll_and_get_coors(field_name)

                    # Check if it's a selection button
                    selection_options = None
                    
                    # Execute each step in the configuration
                    total_steps = len(steps)
                    for j, step in enumerate(steps, 1):
                        action_name, action_params = step

                        # Find corresponding data value in the emr data instance:
                        if "data_name" in action_params:
                            data_name = action_params["data_name"]
                            field_value = self.emr_data.get_value(data_name)
                        
                        if action_name == "check_selection_options":
                            selection_options = self.check_selection_options(field_name)
                            continue
                        
                        if action_name == "wait_for_template":
                            success = self.execute_action(action_name, action_params)
                            if success:
                                # Update coordinates for next mouse move
                                x, y = self.aligner.current_x, self.aligner.current_y
                            else:
                                raise RuntimeError(f"Could not find template: {action_params.get('template_name')}")
                            continue

                        if action_name == "mouse_move" and x is not None and y is not None:
                            action_params = {"x": x, "y": y, "smooth": action_params.get("smooth", True)}

                        if action_name == "keyboard_write":
                            if isinstance(field_value, dict):
                                action_params["text_key"] = action_params.get("text_key", "")
                            else:
                                action_params["text"] = field_value
                            action_params["can_paste"] = action_params.get("can_paste", True)

                        if action_name == "keyboard_press" and selection_options and j == total_steps:
                            press_key, press_time = selection_options[field_value]
                            action_params = {"key": press_key, "presses": press_time}
                            selection_options = None

                        # Execute the action
                        self.execute_action(action_name, action_params, field_value)

                except Exception as e:
                    self.overlay.update_status(f"Error processing field {field_name}: {str(e)}")
                    raise e

            # Back to top when done
            self.control.mouse_scroll(self.scroll_click_now + 10)
            self.overlay.update_status("Page completed successfully")
            self.overlay.set_state(OverlayState.READY)
            
        except Exception as e:
            self.overlay.update_status(f"Page failed: {str(e)}")
            self.overlay.set_state(OverlayState.RUNNING)
            raise e



def test_add_new_patient(task_name, test_data):
    assistant = None
    try:
        assistant = EMRAssistant(page="patient", input_data=test_data)
        time.sleep(2)  # Allow overlay to initialize

        # Go to the task page
        assistant.overlay.update_status(f"Task: ADD NEW PATIENT...")
        assistant.assign_task(task_name=task_name)
        
        # Fill patient information
        assistant.run()

        # Fill insurance information
        assistant.overlay.update_status("Switching to insurance page...")
        assistant.change_page_within_task(target_page="insurance")
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

def test_add_new_visit(task_name, test_data):
    assistant = None
    try:
        assistant = EMRAssistant(page="visit_info", input_data=test_data)
        time.sleep(5)  # Allow overlay to initialize

        # Go to the task page
        assistant.overlay.update_status(f"Task: ADD NEW VISIT...")
        assistant.assign_task(task_name=task_name)
        
        # Fill visit info page
        assistant.run()

        # Fill billing info page
        assistant.overlay.update_status("Switching to billing info page...")
        assistant.change_page_within_task(target_page="billing_info")
        
        if assistant.get_coordinates("ICD_type_9_to_10", img_dir=assistant.general_img_dir):
            assistant.overlay.update_status("Switching to ICD-10...")
            assistant.control.mouse_move(assistant.aligner.current_x, assistant.aligner.current_y)
            assistant.control.mouse_click()
            
        assistant.run()

        # # Fill billing options page
        assistant.overlay.update_status("Switching to billing options page...")
        assistant.change_page_within_task(target_page="billing_options")
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
    test_data = {
        # From test_patient_input
        "person_last_name": "Patient",
        "person_first_name": "Jane",
        "person_birth_date": "11011999",
        "person_sex": "Female",
        "person_ssn": "123456789",
        "contact_address_line1": "123 N Apple Ave",
        "contact_address_line2": "Apt C",
        "contact_city": "Los Angeles",
        "contact_state": "CA",
        "contact_zip": "90045",
        "contact_phone": "2342345555",
        "contact_email": "abc.ddd@gmail.com",

        # From test_insurance_input
        "insurance_primary_type": "Medicare",
        "insurance_primary_company": "NORIDIAN HEALTHCARE SOLUTIONS",
        "insurance_primary_relationship": "Self",
        "insurance_primary_subscriber_id": "11EG4TE5MK73",
        "insurance_secondary_type": "Medicaid",
        "insurance_secondary_company": "MEDICAL CONTRACTED",
        "insurance_secondary_relationship": "Self",
        "insurance_secondary_subscriber_id": "99999999A",

        # From test_visit_info
        # Note: patient_id info is redundant with person info
        # but if needed can be accessed separately
        "provider_last_name": "Doctor",  # from provider_id

        # From test_billing_info
        "clinical_icd10_codes": ["F200", "E119"],
        "clinical_cpt_codes": [("99232", "A"), ("99213", "B")],

        # From test_billing_options
        "billing_facility": "SACF",
        "billing_provider": "",  # empty string preserved
        "billing_service_date": ""
    }

    start = time.time()
    test_add_new_patient("add_new_patient", test_data)
    test_add_new_visit("add_new_visit", test_data)
    end = time.time()
    print(f"Total process time: {end - start} secs")
    # Need a uniform checking methods for window loading, current too hard-coding
    # Need a field content checking method