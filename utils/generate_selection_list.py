import json

def generate_dictionary(keys):
    result = {}
    letter_counts = {}
    
    for key in keys:
        first_letter = key[0]
        
        # Initialize the count for new letters
        if first_letter not in letter_counts:
            letter_counts[first_letter] = 1
        else:
            letter_counts[first_letter] += 1
        
        # Assign the tuple to the result dictionary
        result[key] = [first_letter, letter_counts[first_letter]]  # Use list instead of tuple
    
    return result

def load_dictionary(file_path):
    with open(file_path, 'r') as file:
        loaded_dictionary = json.load(file)
    return loaded_dictionary


if __name__ == "__main__":
    # keys = [
    # 'AA', 'AE', 'AP', 'AK', 'AL', 'AR', 'AS', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE',
    # 'FL', 'FM', 'GA', 'GU', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA',
    # 'MD', 'ME', 'MH', 'MI', 'MN', 'MO', 'MP', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH',
    # 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'PW', 'RI', 'SC', 'SD',
    # 'TN', 'TX', 'UT', 'VA', 'VI', 'VT', 'WA', 'WI', 'WV', 'WY'
    # ]
    keys = ['Self', 'Spouse', 'Child', 'Other Relationship']


    dictionary = generate_dictionary(keys)
    print(dictionary)

    # Save the dictionary to a file
    with open('state_dict.json', 'w') as file:
        json.dump(dictionary, file)

    print("Dictionary has been saved to 'state_dict.pkl'.")
