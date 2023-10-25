import pandas as pd
import argparse
import os
import urllib.request
import urllib.error

# Command-line argument parsing
parser = argparse.ArgumentParser(description='Process CSV files.')
parser.add_argument('-L', '--local-file', help='Specify a local file to use', required=False, default='old_list.csv')
parser.add_argument('-C', '--column', help='Specify the column to use', required=False, default=0, type=int)
parser.add_argument('-S', '--sources-file', help='Specify a local .txt file containing data source URLs', required=False, default='sources.txt')
parser.add_argument('-M', '--main-file', help='Specify the main CSV file', required=False, default='new_list_unedited.csv')
parser.add_argument('-W', '--whitelist-file', help='Specify the whitelist CSV file', required=False, default='allowlist.csv')
args = parser.parse_args()

# Download data from URLs specified in a .txt file or pre-specified URLs
def download_data_from_sources(file_path=None):
    appended_data = pd.DataFrame()
    if file_path:
        with open(file_path, 'r') as f:
            urls = f.readlines()
    else:
        urls = ['http://example.com/pre-specified-file1.csv', 'http://example.com/pre-specified-file2.csv']

    for url in urls:
        url = url.strip()
        try:
            response = urllib.request.urlopen(url)
            if response.status == 200:
                print(f"Source {url} is accessible.")
                temp_df = pd.read_csv(url, header=None)
                appended_data = pd.concat([appended_data, temp_df], ignore_index=True)
            else:
                print(f"Received HTTP status code {response.status} for URL {url}.")
        except urllib.error.URLError as e:
            print(f"Failed to access {url}. Error: {e.reason}")

    return appended_data

# Import the main CSV file
def import_csv(file_path):
    df = pd.read_csv(file_path, header=None)
    return df

# De-duplicate the entries
def deduplicate(df, column):
    return df.drop_duplicates(subset=[column])

# Remove entries that are in the whitelist and print them
def remove_whitelisted(df, whitelist_path, column):
    whitelist_df = pd.read_csv(whitelist_path, header=None)
    removed_entries = df[df[column].isin(whitelist_df[column])]
    if not removed_entries.empty:
        removed_entries.to_csv('allowlist_removed.txt', index=False, header=False, sep='\t')
        print("The following whitelist entries were removed:")
        print(removed_entries)
    else:
        print("No whitelist entries were removed.")
    df = df[~df[column].isin(whitelist_df[column])]
    return df

# Save as a CSV file
def save_csv(df, file_path):
    df.to_csv(file_path, index=False, header=False)

# Compare to a past list and count new entries
def compare_and_count_new_entries(df, past_df, column):
    new_entries = df[~df[column].isin(past_df[column])]
    return new_entries, len(new_entries)

# Generate Output.txt
def generate_output_txt(old_count, new_entries_count, new_list_count):
    addition_total = old_count + new_entries_count
    discrepancy = new_list_count - addition_total
    with open('Output.txt', 'w') as f:
        f.write(f'Old list entries: {old_count}\n')
        f.write(f'New entries: {new_entries_count}\n')
        f.write(f'New list: {new_list_count}\n')
        f.write(f'Addition total: {addition_total}\n')
        f.write(f'Discrepancy: {discrepancy}\n')

if __name__ == "__main__":
    main_file = args.main_file
    whitelist_file = args.whitelist_file
    past_file = args.local_file
    output_file = "new_list.csv"
    new_entries_file = "new_entries.csv"
    column = args.column

    appended_data = None
    if args.sources_file:
        if os.path.exists(args.sources_file):
            print(f"Downloading data from sources specified in {args.sources_file}...")
            appended_data = download_data_from_sources(args.sources_file)
        else:
            print(f"Error: File {args.sources_file} does not exist.")
    else:
        print("Downloading data from pre-specified URLs...")
        appended_data = download_data_from_sources()

    main_df = import_csv(main_file)
    if appended_data is not None and not appended_data.empty:
        main_df = pd.concat([main_df, appended_data], ignore_index=True)

    main_df = deduplicate(main_df, column)
    main_df = remove_whitelisted(main_df, whitelist_file, column)
    save_csv(main_df, output_file)

    past_df = import_csv(past_file)
    new_entries, count_new_entries = compare_and_count_new_entries(main_df, past_df, column)
    print(f"Number of new entries: {count_new_entries}")
    save_csv(new_entries, new_entries_file)

    # Get the counts for each list
    old_count = len(past_df)
    new_entries_count = count_new_entries
    new_list_count = len(main_df)

    # Generate Output.txt with the counts and calculations
    generate_output_txt(old_count, new_entries_count, new_list_count)
