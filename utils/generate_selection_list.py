import pickle

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
        result[key] = (first_letter, letter_counts[first_letter])
    
    return result

if __name__ == "__main__":
    keys = [
        'Male', 'Female', 'Unknown'
    ]

    dictionary = generate_dictionary(keys)
    print(dictionary)

    # Save the dictionary to a file using pickle
    with open('sex_dict.pkl', 'wb') as file:
        pickle.dump(dictionary, file)

    print("Dictionary has been saved to 'sex_dict.pkl'.")
