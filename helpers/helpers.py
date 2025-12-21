import pkg_resources
import csv
from datetime import datetime

def generate_requirements_txt_with_pkg_resources(output_file="requirements.txt"):
    """
    Generates a requirements.txt file using pkg_resources.
    """
    requirements = []
    for dist in pkg_resources.working_set:
        requirements.append(str(dist.as_requirement()))

    try:
        with open(output_file, "w") as f:
            for req in requirements:
                f.write(req + "\n")
        print(f"Successfully generated {output_file}")
    except IOError as e:
        print(f"Error writing to file: {e}")


def parse_injury_data_first_occurrence(input_file="injury_data.csv", output_file="updated_data.csv"):
    """
    Parses through injury data CSV and keeps only the first occurrence of each rider+injury combination.
    This ensures injuries are appropriately linked to their initial location/date and aren't repeat entries.
    
    Args:
        input_file (str): Path to the input CSV file (default: "injury_data.csv")
        output_file (str): Path to the output CSV file (default: "updated_data.csv")
    """
    seen_combinations = {}  # Track rider+injury combinations we've seen
    first_occurrences = []  # Store rows with first occurrences
    
    try:
        # Read the CSV file
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Convert to list and sort by date to process chronologically
            rows = list(reader)
            
            # Sort by date (ascending) to ensure we process earliest dates first
            def parse_date(date_str):
                try:
                    return datetime.strptime(date_str.strip(), '%Y-%m-%d')
                except ValueError:
                    # If date parsing fails, return a far future date to push to end
                    return datetime.max
            
            rows.sort(key=lambda x: parse_date(x['Date']))
            
            # Process each row
            for row in rows:
                rider = row['Rider'].strip()
                injury = row['Injury'].strip()
                
                # Create a unique key for rider+injury combination
                key = (rider, injury)
                
                # If we haven't seen this combination before, add it
                if key not in seen_combinations:
                    seen_combinations[key] = True
                    first_occurrences.append(row)
        
        # Write the filtered data to the output file
        if first_occurrences:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Rider', 'Injury', 'Track', 'Date']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in first_occurrences:
                    writer.writerow(row)
            
            print(f"Successfully processed {len(first_occurrences)} first occurrences from {len(rows)} total entries")
            print(f"Output saved to {output_file}")
        else:
            print("No data to write.")
            
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"Error processing file: {e}")


# Example usage:
if __name__ == "__main__":
    generate_requirements_txt_with_pkg_resources()
    #parse_injury_data_first_occurrence()