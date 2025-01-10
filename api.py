from flask import Flask, request, jsonify
import csv
from fuzzywuzzy import fuzz

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return 'Search App API'
    
def soundex(name):
    """
    Generate the Soundex code for a given name.
    
    Parameters:
        name (str): The name for which to generate the Soundex code.
        
    Returns:
        str: The Soundex code.
    """
    name = name.upper()
    soundex_code = name[0]  # Start with the first letter
    
    # Define Soundex mappings
    mappings = {
        "BFPV": "1", "CGJKQSXZ": "2", "DT": "3",
        "L": "4", "MN": "5", "R": "6"
    }
    
    # Replace letters with Soundex digits
    for char in name[1:]:
        for key, value in mappings.items():
            if char in key:
                digit = value
                # Avoid duplicate consecutive numbers
                if soundex_code[-1] != digit:
                    soundex_code += digit
                break
        else:
            # Ignore vowels and certain consonants
            if char not in "AEIOUYHW":
                continue
    
    # Trim or pad the code to ensure it's four characters long
    soundex_code = soundex_code[:4].ljust(4, "0")
    
    return soundex_code

def search_csv(file_path, Fname_query, Lname_query, fuzzy_threshold=70):
    """
    Search for names in a CSV file using Soundex and fuzzy matching.
    
    Parameters:
        file_path (str): Path to the CSV file.
        Fname_query (str): First name query to search for.
        Lname_query (str): Last name query to search for.
        fuzzy_threshold (int): The similarity threshold for fuzzy matching (0-100).
        
    Returns:
        list of dict: Matching rows with their similarity scores.
    """
    Fname_soundex = soundex(Fname_query)
    Lname_soundex = soundex(Lname_query)
    matches = []

    with open(file_path, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        print(f"Column names: {reader.fieldnames}")

        for row in reader:
            Fname = row.get("\ufeffFname", "").strip()
            Lname = row.get("Lname", "").strip()
            print(Fname,Lname )
            # Compute Soundex for first and last names
            Fname_match = soundex(Fname) == Fname_soundex
            Lname_match = soundex(Lname) == Lname_soundex
            
            # Compute fuzzy scores
            Fname_fuzzy_score = fuzz.partial_ratio(Fname_query, Fname)
            Lname_fuzzy_score = fuzz.partial_ratio(Lname_query, Lname)
            
            # Combine Soundex and fuzzy results
            if Fname_match or Lname_match or (Fname_fuzzy_score >= fuzzy_threshold and Lname_fuzzy_score >= fuzzy_threshold):
                combined_score = (Fname_fuzzy_score + Lname_fuzzy_score) // 2
                matches.append({
                    "Fname": Fname,
                    "Lname": Lname,
                    "combined_score": combined_score,
                    "row_data": row  # Include entire row data
                })
    
    # Sort matches by similarity score
    matches.sort(key=lambda x: x["combined_score"], reverse=True)
    return matches

@app.route('/search', methods=['POST'])
def search():
    """
    API endpoint to search names in a CSV file using Soundex and fuzzy matching.
    """
    try:
        # Load data from request
        data = request.get_json()
        Fname_query = data.get("Fname", "")
        Lname_query = data.get("Lname", "")
        fuzzy_threshold = int(data.get("threshold", 70))
        csv_file = "College_Identifier.csv"  # Path to your CSV file

        # Validate input
        if not Fname_query or not Lname_query:
            return jsonify({"error": "Both 'Fname' and 'Lname' are required."}), 400

        # Perform the search
        results = search_csv(csv_file, Fname_query, Lname_query, fuzzy_threshold)
        
        # Return results
        if results:
            return jsonify({"matches": results}), 200
        else:
            return jsonify({"message": "No matches found."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
