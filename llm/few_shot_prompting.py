import base64
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI


def format_example(example):
    """Format a single example that includes base64-encoded images following the specified syntax."""
    # Process input content blocks
    input_content = []
    for block in example['input']:
        if block['type'] == 'image_url':
            # Read the local image file and encode it in base64
            with open(block['image_path'], 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            # Create the content block with the base64-encoded image using the specified syntax
            image_content = {
                'type': 'image_url',
                'image_url': {'url': f"data:image/jpeg;base64,{image_data}"}
            }
            input_content.append(image_content)
        else:
            # For text content blocks
            input_content.append(block)
    # Create HumanMessage with the processed input content
    human_message = HumanMessage(content=input_content)
    # Create AIMessage with the output content
    ai_message = AIMessage(content=example['output'])
    return [human_message, ai_message]


def format_examples(examples):
    """Format all examples into messages."""
    messages = []
    for example in examples:
        messages.extend(format_example(example))
    return messages


def process_input_content(input_blocks):
    """Process input content blocks to encode images in base64."""
    processed_content = []
    for block in input_blocks:
        if block['type'] == 'image_url':
            # Read and encode the image
            with open(block['image_path'], 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            image_content = {
                'type': 'image_url',
                'image_url': {'url': f"data:image/jpeg;base64,{image_data}"}
            }
            processed_content.append(image_content)
        else:
            # For text content blocks
            processed_content.append(block)
    return processed_content



if __name__ == "__main__":
    from dotenv import load_dotenv

    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)

    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    
    # Local image files path
    image_path1 = "output_image_1.png"
    image_path2 = "output_image_2.png"
    image_path3 = "image3.jpg"

    # Define few-shot examples that include base64-encoded images
    examples = [
        {
            "input": [
                {"type": "image_url", "image_path": image_path1},
                {"type": "text", "text": "Match the blue bounding boxes to it's corresponding label name for the web form page image, \
                                          you should format your result in a jason format."},
            ],
            "output": """{
                        "Patient Demographics":{
                            "Pat. Acct No": 20,
                            "Primary Care Provider": 28,
                            "Referring Provider": 34,
                            "Last Name": 26,
                            "First Name": 36,
                            "Middle Name/ MI": 29,
                            "DOB": 30,
                            "DOB(Calendar)": 13,
                            "Sex": 27,
                            "SSN": 5,
                            "Weight": 19,
                            "Height": 22,
                            "Name Suffix": 4,
                            "Professional Title": 31,
                            "Preferred Language": 25,
                            "Religion": 23,
                            "Sexual Orientation": 12,
                            "Gender Identity": 0,
                            "Ethnicity": 10,
                            "Race": 3,
                            "Mother's Maiden Name(Last)": 18,
                            "Mother's Maiden Name(First)": 24,
                            "Advance Directive Type": 9,
                            "Advance Directive Reviewed": 2,
                            "Advance Directive Reviewed(Calendar)": 33,
                        },
                        "Patient Contact Information":{
                            "Address Line 1": 1,
                            "Address Line 2": 7,
                            "City": 17,
                            "State": 14,
                            "Zip": 35,
                            "Home Phone": 15,
                            "Work Phone": 8,
                            "Work Phone ex": 21,
                            "Preferred Phone": 11,
                            "Fax": 32,
                            "Email": 6,
                            "Communication Preference": 16,
                        },
                    }"""
        },
    ]

    # Format the few-shot examples into messages
    few_shot_messages = format_examples(examples)

    # Assemble the final prompt template
    final_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an form filling assistant, your job is to match the indexed bounding box field to its cooresponding label on a image."),
        ] + few_shot_messages + [
            ("human", "{input}"),
        ]
    )

    # Define the input with a base64-encoded image
    input_content = [
        {"type": "image_url", "image_path": image_path2},
        {"type": "text", "text": "Match the blue bounding boxes to it's relative label name for the web form page image, you should format your result in a jason format."},
    ]

    processed_input_img = process_input_content(input_content)
    # messages = final_prompt.format_messages(input=processed_input_img)

    # Initialize the chat model
    model = ChatOpenAI(model="gpt-4o", temperature=0)
    chain = final_prompt | model

    # Invoke the model with the formatted messages
    response = chain.invoke({"input": processed_input_img})

    # Print the AI's response
    print(response)
